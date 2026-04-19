import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'
import { classifyComplaint } from '@/lib/nlp-client'
import { transcribeAudio } from '@/lib/stt-client'
import { generateResolution } from '@/lib/genai-client'
import { z } from 'zod'
import { broadcastComplaint } from '@/lib/sse-broadcast'

const createComplaintSchema = z.object({
  text: z.string().min(1).max(5000).optional(),
  source: z.enum(['email', 'call', 'walkin']),
  product_id: z.string().min(1),
  customer_name: z.string().min(1),
  customer_email: z.string().email().optional().nullable(),
  customer_phone: z.string().optional().nullable(),
  audio_base64: z.string().optional().nullable(),
})

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const priority = searchParams.get('priority')
    const category = searchParams.get('category')
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '20')

    const admin = createAdminClient()
    let query = admin
      .from('complaints')
      .select('*, products(*)', { count: 'exact' })
      .order('created_at', { ascending: false })

    if (status) query = query.eq('status', status)
    if (priority) query = query.eq('priority', priority)
    if (category) query = query.eq('category', category)

    const start = (page - 1) * limit
    const end = start + limit - 1
    query = query.range(start, end)

    const { data: complaints, error, count } = await query

    if (error) throw error

    return NextResponse.json({
      complaints: complaints || [],
      pagination: {
        page,
        limit,
        total: count || 0,
        totalPages: Math.ceil((count || 0) / limit),
      },
    })
  } catch (error) {
    console.error('Error fetching complaints:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validated = createComplaintSchema.parse(body)

    let complaintText = validated.text || ''

    if (validated.source === 'call' && validated.audio_base64) {
      try {
        const audioBuffer = Buffer.from(validated.audio_base64, 'base64')
        const sttResult = await transcribeAudio(audioBuffer, 'wav')
        complaintText = sttResult.text
      } catch (sttError) {
        console.error('STT error:', sttError)
      }
    }

    if (!complaintText) {
      return NextResponse.json(
        { error: 'Complaint text is required' },
        { status: 400 }
      )
    }

    const admin = createAdminClient()

    const { data: product } = await admin
      .from('products')
      .select('*')
      .eq('id', validated.product_id)
      .single()

    if (!product) {
      return NextResponse.json({ error: 'Product not found' }, { status: 404 })
    }

    const nlpResult = await classifyComplaint(complaintText)

    let genAIResult = null
    try {
      genAIResult = await generateResolution({
        category: nlpResult.category,
        priority: nlpResult.priority,
        channel: validated.source,
        customer_name: validated.customer_name,
        product_name: product.name,
        complaint_text: complaintText,
      })
    } catch (genAIError) {
      console.error('GenAI error:', genAIError)
    }

    const complaintData = {
      complaint_text: complaintText,
      category: nlpResult.category,
      priority: nlpResult.priority,
      sentiment_score: nlpResult.sentiment_score,
      source: validated.source,
      status: 'new',
      immediate_action: genAIResult?.immediate_action,
      assigned_team: genAIResult?.assigned_team,
      escalation_required: genAIResult?.escalation_required || false,
      customer_response: genAIResult?.customer_communication,
      customer_name: validated.customer_name,
      customer_email: validated.customer_email || null,
      customer_phone: validated.customer_phone || null,
      product_id: validated.product_id,
    }

    const { data: complaint, error } = await admin
      .from('complaints')
      .insert(complaintData)
      .select('*, products(*)')
      .single()

    if (error) throw error

    if (complaint?.id) {
      await admin.from('complaint_timeline').insert({
        complaint_id: complaint.id,
        status_from: 'new',
        status_to: 'new',
        changed_by: 'System',
        notes: 'Complaint created and classified as ' + complaint.category + ' with priority ' + complaint.priority,
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
          product: product.name,
          category: complaint.category,
          text: complaint.complaint_text?.substring(0, 100),
          created_at: complaint.created_at,
        },
      })
    }

    return NextResponse.json(complaint, { status: 201 })
  } catch (error) {
    console.error('Error creating complaint:', error)
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation error', details: error.issues },
        { status: 400 }
      )
    }
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
