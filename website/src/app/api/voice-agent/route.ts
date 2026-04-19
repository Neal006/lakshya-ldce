import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { transcribeAudio } from '@/lib/stt-client'
import { classifyComplaint } from '@/lib/nlp-client'
import { generateResolution } from '@/lib/genai-client'

export const maxDuration = 30

export async function POST(request: NextRequest) {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let transcript = ''
  let confidence = 0
  let classification: {
    category: string
    priority: string
    sentiment_score: number
  } | null = null
  let resolution: {
    immediate_action: string
    resolution_steps: string[]
    assigned_team: string
    escalation_required: boolean
    follow_up_required: boolean
    follow_up_timeline: string
    customer_communication: string
    estimated_resolution_time: string
  } | null = null
  let sttAvailable = false
  let nlpAvailable = false
  let genaiAvailable = false

  try {
    const formData = await request.formData()
    const file = formData.get('file')
    if (!file || !(file instanceof Blob)) {
      return NextResponse.json({ error: 'Missing audio file' }, { status: 400 })
    }

    const arrayBuffer = await file.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)

    // Step 1: STT - browser already converts to WAV before uploading
    try {
      const sttResult = await transcribeAudio(buffer, 'wav')
      transcript = sttResult.text || ''
      confidence = sttResult.confidence || 0
      sttAvailable = true
    } catch (sttErr) {
      console.error('STT service unavailable:', sttErr)
      const fallbackText = formData.get('transcript') as string | null
      if (fallbackText && fallbackText.trim().length > 0) {
        transcript = fallbackText
        confidence = 0.6
      }
    }

    if (!transcript || transcript.trim().length === 0) {
      return NextResponse.json({
        transcript: '',
        confidence: 0,
        classification: null,
        resolution: null,
        sttAvailable,
        nlpAvailable: false,
        genaiAvailable: false,
        message: sttAvailable ? 'No speech detected. Please try again.' : 'Speech-to-text service is unavailable.',
      })
    }

    // Step 2: NLP Classification
    try {
      const cls = await classifyComplaint(transcript)
      classification = {
        category: cls.category,
        priority: cls.priority,
        sentiment_score: cls.sentiment_score,
      }
      nlpAvailable = true
    } catch (nlpErr) {
      console.error('NLP service unavailable:', nlpErr)
      classification = { category: 'Product', priority: 'Medium', sentiment_score: 0 }
    }

    // Step 3: GenAI Resolution
    try {
      resolution = await generateResolution({
        category: classification.category,
        priority: classification.priority,
        channel: 'call',
        customer_name: session.user?.name || 'Voice Caller',
        product_name: 'General',
        complaint_text: transcript,
        sentiment_score: classification.sentiment_score,
      })
      genaiAvailable = true
    } catch (genaiErr) {
      console.error('GenAI service unavailable:', genaiErr)
      resolution = {
        immediate_action: `Acknowledge the complaint: "${transcript.substring(0, 100)}". Collect details and assure investigation.`,
        resolution_steps: [
          'Document the complaint details',
          'Classify and assign to the appropriate team',
          'Contact the customer with an update within 24 hours',
          'Follow up to confirm resolution',
        ],
        assigned_team: classification.priority === 'High' ? 'Escalation Team' : 'Support Team',
        escalation_required: classification.priority === 'High',
        follow_up_required: true,
        follow_up_timeline: '24-48 hours',
        customer_communication: 'Thank you for bringing this to our attention. We will investigate and follow up within 24 hours.',
        estimated_resolution_time: classification.priority === 'High' ? '4-8 hours' : '1-3 business days',
      }
    }

    return NextResponse.json({ transcript, confidence, classification, resolution, sttAvailable, nlpAvailable, genaiAvailable })
  } catch (error) {
    console.error('Voice agent error:', error)
    return NextResponse.json(
      { error: 'Voice agent processing failed', transcript: '', classification: null, resolution: null, sttAvailable: false, nlpAvailable: false, genaiAvailable: false, details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 502 }
    )
  }
}