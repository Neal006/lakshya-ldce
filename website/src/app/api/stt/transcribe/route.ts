import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { transcribeAudio } from '@/lib/stt-client'

export async function POST(request: NextRequest) {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const formData = await request.formData()
    const file = formData.get('file')
    if (!file || !(file instanceof Blob)) {
      return NextResponse.json({ error: 'Missing audio file' }, { status: 400 })
    }

    const name = (file as File).name || 'audio.wav'
    const ext = name.split('.').pop()?.toLowerCase() || 'wav'
    const allowed = ['wav', 'mp3', 'webm', 'ogg', 'm4a']
    const fmt = allowed.includes(ext) ? ext : 'wav'

    const arrayBuffer = await file.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)

    const result = await transcribeAudio(buffer, fmt)
    return NextResponse.json(result)
  } catch (e) {
    console.error('STT route error:', e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Transcription failed' },
      { status: 502 }
    )
  }
}
