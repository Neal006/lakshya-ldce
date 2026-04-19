'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  MicOff,
  Volume2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  ArrowRight,
  Loader2,
  RotateCcw,
} from 'lucide-react'

interface Classification {
  category: string
  priority: string
  sentiment_score: number
}

interface Resolution {
  immediate_action: string
  resolution_steps: string[]
  assigned_team: string
  escalation_required: boolean
  follow_up_required: boolean
  follow_up_timeline: string
  customer_communication: string
  estimated_resolution_time: string
}

interface VoiceAgentResponse {
  transcript: string
  confidence: number
  classification: Classification | null
  resolution: Resolution | null
  message?: string
  sttAvailable?: boolean
  nlpAvailable?: boolean
  genaiAvailable?: boolean
  details?: string
}

type AgentState = 'idle' | 'recording' | 'processing' | 'result' | 'error'

export default function VoiceAgentPage() {
  const [agentState, setAgentState] = useState<AgentState>('idle')
  const [response, setResponse] = useState<VoiceAgentResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [transcriptParts, setTranscriptParts] = useState<string[]>([])
  const [isThinking, setIsThinking] = useState(false)

  // Use refs for everything event handlers read to avoid stale closures
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isHoldingRef = useRef(false)
  const recognitionRef = useRef<any>(null)
  const browserTranscriptRef = useRef('')
  const agentStateRef = useRef<AgentState>('idle')

  // Keep ref in sync with state
  useEffect(() => { agentStateRef.current = agentState }, [agentState])

  const stopBrowserRecognition = useCallback(() => {
    try { recognitionRef.current?.stop() } catch {}
    recognitionRef.current = null
  }, [])

  // Convert recorded webm/opus blob to 16kHz mono WAV using Web Audio API
  const convertToWav = useCallback(async (blob: Blob): Promise<Blob> => {
    const arrayBuffer = await blob.arrayBuffer()
    const audioContext = new AudioContext({ sampleRate: 16000 })
    try {
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
      const numChannels = 1
      const sampleRate = 16000
      const length = audioBuffer.length
      const offlineCtx = new OfflineAudioContext(numChannels, Math.ceil(length * (sampleRate / audioBuffer.sampleRate)), sampleRate)
      const source = offlineCtx.createBufferSource()
      source.buffer = audioBuffer
      source.connect(offlineCtx.destination)
      source.start()
      const renderedBuffer = await offlineCtx.startRendering()

      // Convert AudioBuffer to WAV
      const channelData = renderedBuffer.getChannelData(0)
      const wavBuffer = new ArrayBuffer(44 + channelData.length * 2)
      const view = new DataView(wavBuffer)

      // RIFF header
      const writeString = (offset: number, str: string) => { for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i)) }
      writeString(0, 'RIFF')
      view.setUint32(4, 36 + channelData.length * 2, true)
      writeString(8, 'WAVE')
      writeString(12, 'fmt ')
      view.setUint32(16, 16, true)
      view.setUint16(20, 1, true)
      view.setUint16(22, numChannels, true)
      view.setUint32(24, sampleRate, true)
      view.setUint32(28, sampleRate * numChannels * 2, true)
      view.setUint16(32, numChannels * 2, true)
      view.setUint16(34, 16, true)
      writeString(36, 'data')
      view.setUint32(40, channelData.length * 2, true)

      // Write PCM samples
      let offset = 44
      for (let i = 0; i < channelData.length; i++) {
        const s = Math.max(-1, Math.min(1, channelData[i]))
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
        offset += 2
      }

      return new Blob([wavBuffer], { type: 'audio/wav' })
    } finally {
      await audioContext.close()
    }
  }, [])

  const startBrowserRecognition = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return
    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'
    browserTranscriptRef.current = ''
    recognition.onresult = (event: any) => {
      let finalTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript
        }
      }
      if (finalTranscript) {
        browserTranscriptRef.current = finalTranscript
      }
    }
    recognition.onerror = () => {}
    recognition.onend = () => {}
    try { recognition.start() } catch {}
    recognitionRef.current = recognition
  }, [])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      })

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : ''

      const options = mimeType ? { mimeType } : {}
      const mediaRecorder = new MediaRecorder(stream, options)

      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.start(250)
      mediaRecorderRef.current = mediaRecorder
      setAgentState('recording')
      agentStateRef.current = 'recording'
      setRecordingDuration(0)

      startBrowserRecognition()

      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1)
      }, 1000)
    } catch (err) {
      console.error('Microphone access failed:', err)
      setError('Microphone access denied. Please allow microphone permissions.')
      setAgentState('error')
      agentStateRef.current = 'error'
    }
  }, [startBrowserRecognition])

const stopRecording = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    stopBrowserRecognition()

    const mediaRecorder = mediaRecorderRef.current
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      setAgentState('idle')
      agentStateRef.current = 'idle'
      setIsThinking(false)
      return
    }

    const capturedBrowserTranscript = browserTranscriptRef.current

    setAgentState('processing')
    agentStateRef.current = 'processing'
    setIsThinking(true)

    return new Promise<void>((resolve) => {
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' })
        mediaRecorder.stream.getTracks().forEach((track) => track.stop())
        mediaRecorderRef.current = null

        if (audioBlob.size < 500) {
          setAgentState('idle')
          agentStateRef.current = 'idle'
          setIsThinking(false)
          resolve()
          return
        }

        try {
          const wavBlob = await convertToWav(audioBlob)

          const formData = new FormData()
          formData.append('file', wavBlob, 'recording.wav')
          if (capturedBrowserTranscript) {
            formData.append('transcript', capturedBrowserTranscript)
          }

          const res = await fetch('/api/voice-agent', {
            method: 'POST',
            body: formData,
          })

          if (!res.ok) {
            const errData = await res.json().catch(() => ({ error: 'Unknown error' }))
            throw new Error(errData.error || errData.details || `Server error (${res.status})`)
          }

          const data: VoiceAgentResponse = await res.json()
          setResponse(data)

          const finalTranscript = data.transcript || capturedBrowserTranscript
          if (finalTranscript) {
            setTranscriptParts((prev) => [...prev, finalTranscript])
            if (!data.transcript && capturedBrowserTranscript) {
              setResponse({ ...data, transcript: finalTranscript })
            }
          }

          if (data.message && !data.transcript && !capturedBrowserTranscript) {
            setError(data.message)
            setAgentState('error')
            agentStateRef.current = 'error'
          } else {
            setAgentState(finalTranscript ? 'result' : 'idle')
            agentStateRef.current = finalTranscript ? 'result' : 'idle'
            setError(null)
          }
        } catch (err) {
          console.error('Voice agent error:', err)
          if (capturedBrowserTranscript) {
            setResponse({
              transcript: capturedBrowserTranscript,
              confidence: 0.6,
              classification: { category: 'Product', priority: 'Medium', sentiment_score: 0 },
              resolution: {
                immediate_action: `Acknowledge the complaint: "${capturedBrowserTranscript.substring(0, 100)}". Collect details and assure investigation.`,
                resolution_steps: ['Document the complaint details', 'Classify and assign to the appropriate team', 'Contact the customer with an update within 24 hours', 'Follow up to confirm resolution'],
                assigned_team: 'Support Team',
                escalation_required: false,
                follow_up_required: true,
                follow_up_timeline: '24-48 hours',
                customer_communication: 'Thank you for bringing this to our attention. We will investigate and follow up within 24 hours.',
                estimated_resolution_time: '1-3 business days',
              },
              sttAvailable: false,
              nlpAvailable: false,
              genaiAvailable: false,
            })
            setTranscriptParts((prev) => [...prev, capturedBrowserTranscript])
            setAgentState('result')
            agentStateRef.current = 'result'
            setError('AI services are partially offline. Using browser transcription with fallback analysis.')
          } else {
            setError(err instanceof Error ? err.message : 'Processing failed')
            setAgentState('error')
            agentStateRef.current = 'error'
          }
        } finally {
          setIsThinking(false)
        }

        resolve()
      }

      mediaRecorder.stop()
    })
  }, [convertToWav, stopBrowserRecognition])

  // Stable keyboard handlers using refs — never recreated
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !e.repeat) {
        e.preventDefault()
        if (isHoldingRef.current) return
        isHoldingRef.current = true
        const state = agentStateRef.current
        if (state === 'idle' || state === 'result' || state === 'error') {
          setResponse(null)
          setError(null)
          startRecording()
        }
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault()
        isHoldingRef.current = false
        if (agentStateRef.current === 'recording') {
          stopRecording()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [startRecording, stopRecording])

  const handleButtonPress = () => {
    const state = agentStateRef.current
    if (state === 'idle' || state === 'result' || state === 'error') {
      setResponse(null)
      setError(null)
      startRecording()
    }
  }

  const handleButtonRelease = () => {
    if (agentStateRef.current === 'recording') {
      stopRecording()
    }
  }

  const handleReset = () => {
    setResponse(null)
    setError(null)
    setTranscriptParts([])
    setRecordingDuration(0)
    setAgentState('idle')
    agentStateRef.current = 'idle'
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const priorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return '#EF4444'
      case 'medium': return '#3B82F6'
      case 'low': return '#22C55E'
      default: return '#9CA3AF'
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <motion.div
        className="w-full max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{
              background: 'linear-gradient(145deg, #8B5CF6 0%, #6D28D9 100%)',
              boxShadow: '0 4px 0 #5B21B6, 0 8px 16px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
            }}
            animate={
              agentState === 'recording'
                ? { scale: [1, 1.1, 1], transition: { repeat: Infinity, duration: 1.5 } }
                : { scale: 1 }
            }
          >
            <Volume2 size={32} className="text-white" />
          </motion.div>
          <h1 className="text-3xl font-bold text-[#F5F5F5] mb-2">Voice Agent</h1>
          <p className="text-gray-400">
            {agentState === 'idle' && 'Press and hold SPACEBAR or the button below to speak'}
            {agentState === 'recording' && 'Listening... Release to process'}
            {agentState === 'processing' && 'Processing your complaint...'}
            {agentState === 'result' && 'Response received. Hold SPACEBAR to speak again.'}
            {agentState === 'error' && 'Something went wrong. Press SPACEBAR to try again.'}
          </p>
        </div>

        {/* Push-to-Talk Button */}
        <div className="flex justify-center mb-8">
          <motion.button
            onMouseDown={handleButtonPress}
            onMouseUp={handleButtonRelease}
            onMouseLeave={() => { if (agentStateRef.current === 'recording') handleButtonRelease() }}
            onTouchStart={handleButtonPress}
            onTouchEnd={handleButtonRelease}
            className="relative w-40 h-40 rounded-full flex items-center justify-center cursor-pointer select-none"
            style={{
              background:
                agentState === 'recording'
                  ? 'linear-gradient(145deg, #EF4444 0%, #DC2626 100%)'
                  : agentState === 'processing'
                    ? 'linear-gradient(145deg, #F59E0B 0%, #D97706 100%)'
                    : 'linear-gradient(145deg, #8B5CF6 0%, #6D28D9 100%)',
              boxShadow:
                agentState === 'recording'
                  ? '0 0 0 4px rgba(239, 68, 68, 0.3), 0 0 40px rgba(239, 68, 68, 0.2), inset 0 2px 0 rgba(255, 255, 255, 0.2)'
                  : agentState === 'processing'
                    ? '0 0 0 4px rgba(245, 158, 11, 0.3), 0 0 40px rgba(245, 158, 11, 0.2), inset 0 2px 0 rgba(255, 255, 255, 0.2)'
                    : '0 4px 0 #5B21B6, 0 8px 16px rgba(139, 92, 246, 0.3), inset 0 2px 0 rgba(255, 255, 255, 0.2)',
            }}
            whileTap={{ scale: 0.95 }}
            disabled={agentState === 'processing'}
          >
            {/* Pulse rings when recording */}
            {agentState === 'recording' && (
              <>
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-red-400"
                  animate={{ scale: [1, 1.5], opacity: [0.6, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                />
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-red-400"
                  animate={{ scale: [1, 1.8], opacity: [0.4, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5, delay: 0.3 }}
                />
              </>
            )}

            {agentState === 'processing' ? (
              <Loader2 className="animate-spin text-white" size={48} />
            ) : agentState === 'recording' ? (
              <MicOff size={48} className="text-white" />
            ) : (
              <Mic size={48} className="text-white" />
            )}
          </motion.button>
        </div>

        {/* Recording Duration */}
        {agentState === 'recording' && (
          <motion.div
            className="text-center mb-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full"
              style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-red-400 font-mono text-lg">{formatDuration(recordingDuration)}</span>
            </div>
          </motion.div>
        )}

        {/* Processing indicator */}
        {isThinking && (
          <motion.div
            className="text-center mb-6"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-xl"
              style={{
                background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                border: '1px solid rgba(139, 92, 246, 0.2)',
              }}
            >
              <Loader2 className="animate-spin text-[#8B5CF6]" size={20} />
              <span className="text-gray-300">
                {agentState === 'processing' ? 'Transcribing & analyzing...' : 'Thinking...'}
              </span>
            </div>
          </motion.div>
        )}

        {/* Error */}
        <AnimatePresence>
          {error && (agentState === 'error' || agentState === 'result') && (
            <motion.div
              className="mb-6"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="p-4 rounded-xl border border-amber-500/20"
                style={{ background: 'rgba(245, 158, 11, 0.05)' }}
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle size={20} className="text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-amber-400 font-medium text-sm">Notice</p>
                    <p className="text-gray-300 text-sm mt-1">{error}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Response Display */}
        <AnimatePresence>
          {response && agentState === 'result' && (
            <motion.div
              className="space-y-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
            >
              {/* Transcript */}
              <div className="p-5 rounded-2xl"
                style={{
                  background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                  boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.03)',
                }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg" style={{ background: 'linear-gradient(145deg, #8B5CF6 0%, #6D28D9 100%)' }}>
                    <Mic size={16} className="text-white" />
                  </div>
                  <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider">Your Complaint</h3>
                  {response.sttAvailable === false && (
                    <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">Browser STT</span>
                  )}
                </div>
                <p className="text-[#F5F5F5] text-base leading-relaxed">{response.transcript}</p>
                {response.confidence > 0 && (
                  <p className="text-xs text-gray-500 mt-2">Confidence: {Math.round(response.confidence * 100)}%</p>
                )}
              </div>

              {/* Classification */}
              {response.classification && (
                <div className="p-5 rounded-2xl"
                  style={{
                    background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                    boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.03)',
                  }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg" style={{ background: 'linear-gradient(145deg, #3B82F6 0%, #1D4ED8 100%)' }}>
                      <Zap size={16} className="text-white" />
                    </div>
                    <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider">AI Classification</h3>
                    {response.nlpAvailable === false && (
                      <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">Default</span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 rounded-xl" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                      <p className="text-xs text-gray-400 mb-1">Category</p>
                      <p className="text-sm font-semibold text-[#F5F5F5]">{response.classification.category}</p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                      <p className="text-xs text-gray-400 mb-1">Priority</p>
                      <p className="text-sm font-semibold" style={{ color: priorityColor(response.classification.priority) }}>
                        {response.classification.priority}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                      <p className="text-xs text-gray-400 mb-1">Sentiment</p>
                      <p className="text-sm font-semibold text-[#F5F5F5]">
                        {response.classification.sentiment_score > 0.05 ? 'Positive' : response.classification.sentiment_score < -0.05 ? 'Negative' : 'Neutral'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* GenAI Resolution */}
              {response.resolution && (
                <div className="p-5 rounded-2xl"
                  style={{
                    background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                    boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.03)',
                  }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg" style={{ background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)' }}>
                      <CheckCircle size={16} className="text-white" />
                    </div>
                    <h3 className="text-sm font-semibold text-[#FF6B35] uppercase tracking-wider">AI Resolution</h3>
                    {response.genaiAvailable === false && (
                      <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">Fallback</span>
                    )}
                  </div>

                  {/* Immediate Action */}
                  <div className="p-4 rounded-xl mb-3 border border-purple-500/20"
                    style={{ background: 'linear-gradient(165deg, rgba(139, 92, 246, 0.1) 0%, rgba(109, 40, 217, 0.05) 100%)' }}
                  >
                    <p className="text-xs text-purple-400 font-semibold mb-1">Immediate Action</p>
                    <p className="text-sm text-gray-200">{response.resolution.immediate_action}</p>
                  </div>

                  {/* Resolution Steps */}
                  {response.resolution.resolution_steps && response.resolution.resolution_steps.length > 0 && (
                    <div className="p-4 rounded-xl mb-3 border border-blue-500/20"
                      style={{ background: 'linear-gradient(165deg, rgba(59, 130, 246, 0.1) 0%, rgba(29, 78, 216, 0.05) 100%)' }}
                    >
                      <p className="text-xs text-blue-400 font-semibold mb-2">Resolution Steps</p>
                      <ul className="space-y-1">
                        {response.resolution.resolution_steps.map((step, i) => (
                          <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-blue-400 mt-0.5"><ArrowRight size={14} /></span>
                            {step}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Key Info Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="p-3 rounded-xl" style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                      <p className="text-xs text-emerald-400 mb-1">Assigned Team</p>
                      <p className="text-sm font-semibold text-[#F5F5F5]">{response.resolution.assigned_team}</p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                      <p className="text-xs text-emerald-400 mb-1">Est. Resolution</p>
                      <p className="text-sm font-semibold text-[#F5F5F5]">
                        <Clock size={12} className="inline mr-1" />
                        {response.resolution.estimated_resolution_time}
                      </p>
                    </div>
                  </div>

                  {/* Escalation & Follow-up */}
                  <div className="flex gap-2 mb-3">
                    {response.resolution.escalation_required && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                        Escalation Required
                      </span>
                    )}
                    {response.resolution.follow_up_required && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        Follow-up: {response.resolution.follow_up_timeline}
                      </span>
                    )}
                  </div>

                  {/* Customer Communication */}
                  {response.resolution.customer_communication && (
                    <div className="p-4 rounded-xl border border-emerald-500/20"
                      style={{ background: 'linear-gradient(165deg, rgba(34, 197, 94, 0.1) 0%, rgba(22, 163, 74, 0.05) 100%)' }}
                    >
                      <p className="text-xs text-emerald-400 font-semibold mb-1">Suggested Customer Response</p>
                      <p className="text-sm text-gray-300 leading-relaxed">{response.resolution.customer_communication}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Reset Button */}
              <div className="flex justify-center mt-6">
                <motion.button
                  onClick={handleReset}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-gray-300"
                  style={{
                    background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                    boxShadow: '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <RotateCcw size={16} />
                  New Conversation
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Conversation History */}
        {transcriptParts.length > 1 && agentState !== 'error' && (
          <motion.div
            className="mt-6 p-4 rounded-xl"
            style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <p className="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wider">Conversation History</p>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {transcriptParts.map((part, i) => (
                <p key={i} className="text-sm text-gray-400">
                  <span className="text-gray-600">{i + 1}.</span> {part}
                </p>
              ))}
            </div>
          </motion.div>
        )}

        {/* Keyboard hint */}
        {agentState === 'idle' && (
          <motion.div
            className="text-center mt-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs text-gray-500"
              style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}
            >
              <kbd className="px-2 py-0.5 rounded text-gray-400 font-mono text-xs"
                style={{ background: '#2A2A2E', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              >
                SPACE
              </kbd>
              <span>Hold to talk, release to process</span>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}