import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'
import { classifyComplaint } from '@/lib/nlp-client'
import { generateResolution } from '@/lib/genai-client'
import { z } from 'zod'
import { broadcastComplaint } from '@/lib/sse-broadcast'
import { sendComplaintAcknowledgment } from '@/lib/email-client'

const brevoWebhookSchema = z.object({
  event: z.string(),
  'item-id': z.string().optional(),
  sender: z.object({
    email: z.string().email(),
    name: z.string().optional(),
  }),
  subject: z.string().optional(),
  content: z.string().optional(),
  'body-html': z.string().optional(),
  'body-text': z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const webhookSecret = process.env.BREVO_WEBHOOK_SECRET
    if (webhookSecret) {
      const signature = request.headers.get('x-brevo-signature')
      if (!signature || signature !== webhookSecret) {
        return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
      }
    }

    const body = await request.json()
    const validated = brevoWebhookSchema.parse(body)

    const complaintText = validated['body-text'] || validated.content || validated.subject || ''
    const senderEmail = validated.sender.email
    const senderName = validated.sender.name || senderEmail.split('@')[0]

    if (!complaintText) {
      return NextResponse.json({ error: 'No complaint text found' }, { status: 400 })
    }

    const admin = createAdminClient()

    const { data: products } = await admin.from('products').select('*')
    const defaultProduct = products?.[0]

    if (!defaultProduct) {
      return NextResponse.json({ error: 'No products in database' }, { status: 500 })
    }

    const nlpResult = await classifyComplaint(complaintText)

    let genAIResult = null
    try {
      genAIResult = await generateResolution({
        category: nlpResult.category,
        priority: nlpResult.priority,
        channel: 'email',
        customer_name: senderName,
        product_name: defaultProduct.name,
        complaint_text: complaintText,
      })
    } catch {
      console.error('GenAI resolution failed for Brevo webhook')
    }

    const complaintData = {
      complaint_text: complaintText,
      category: nlpResult.category,
      priority: nlpResult.priority,
      sentiment_score: nlpResult.sentiment_score,
      source: 'email',
      status: 'new',
      immediate_action: genAIResult?.immediate_action,
      assigned_team: genAIResult?.assigned_team,
      escalation_required: genAIResult?.escalation_required || false,
      customer_response: genAIResult?.customer_communication,
      customer_name: senderName,
      customer_email: senderEmail,
      product_id: defaultProduct.id,
    }

    const { data: complaint, error } = await admin
      .from('complaints')
      .insert(complaintData)
      .select('*, products(*)')
      .single()

    if (error) throw error

    // Send AI-generated acknowledgment email to customer
    let emailSent = false
    try {
      const emailResult = await sendComplaintAcknowledgment({
        customerEmail: senderEmail,
        customerName: senderName,
        complaintId: complaint.id,
        complaintText: complaintText,
        category: nlpResult.category,
        priority: nlpResult.priority,
        immediateAction: genAIResult?.immediate_action || 'We are reviewing your complaint and will take appropriate action.',
        resolutionSteps: genAIResult?.resolution_steps || ['Our team is analyzing your issue', 'We will contact you with updates', 'Your complaint will be resolved within the SLA timeframe'],
        assignedTeam: genAIResult?.assigned_team || 'Customer Support Team',
        estimatedResolutionTime: genAIResult?.estimated_resolution_time || '24-48 hours',
      })
      emailSent = emailResult.success
      
      if (!emailResult.success) {
        console.error('Failed to send acknowledgment email:', emailResult.error)
      }
    } catch (emailError) {
      console.error('Error sending acknowledgment email:', emailError)
    }

    if (complaint?.id) {
      await admin.from('complaint_timeline').insert({
        complaint_id: complaint.id,
        status_from: 'new',
        status_to: 'new',
        changed_by: 'System',
        notes: 'Complaint created via Brevo email webhook from ' + senderEmail + (emailSent ? '. Acknowledgment email sent.' : ''),
      })
    }

    broadcastComplaint({
      type: 'new_complaint',
      data: complaint,
    })

    if (complaint?.priority === 'High') {
      broadcastComplaint({
        type: 'high_priority_alert',
        data: {
          id: complaint.id,
          product: defaultProduct.name,
          category: complaint.category,
          text: complaint.complaint_text?.substring(0, 100),
          created_at: complaint.created_at,
        },
      })
    }

    return NextResponse.json({ 
      success: true, 
      complaint_id: complaint?.id,
      email_sent: emailSent 
    }, { status: 201 })
  } catch (error) {
    console.error('Brevo webhook error:', error)
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: 'Validation error', details: error.issues }, { status: 400 })
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
