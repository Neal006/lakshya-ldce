import { NextResponse } from 'next/server'

interface ServiceHealth {
  name: string
  url: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  latency_ms?: number
  error?: string
}

async function checkService(name: string, url: string): Promise<ServiceHealth> {
  const start = Date.now()
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)

    const response = await fetch(`${url}/health`, {
      method: 'GET',
      signal: controller.signal,
    })

    clearTimeout(timeout)
    const latency = Date.now() - start

    if (response.ok) {
      return {
        name,
        url,
        status: 'healthy',
        latency_ms: latency,
      }
    }

    return {
      name,
      url,
      status: 'unhealthy',
      latency_ms: latency,
      error: `HTTP ${response.status}`,
    }
  } catch (error) {
    const latency = Date.now() - start
    return {
      name,
      url,
      status: 'unhealthy',
      latency_ms: latency,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

export async function GET() {
  const services = [
    { name: 'NLP Classifier', url: process.env.ML_CLASSIFIER_URL || 'http://localhost:8001' },
    { name: 'STT Service', url: process.env.STT_SERVICE_URL || 'http://localhost:8002' },
    { name: 'GenAI Service', url: process.env.GENAI_SERVICE_URL || 'http://localhost:8003' },
  ]

  const results = await Promise.all(services.map(s => checkService(s.name, s.url)))

  const allHealthy = results.every(r => r.status === 'healthy')
  const overallStatus = allHealthy ? 'healthy' : 'degraded'

  return NextResponse.json({
    status: overallStatus,
    timestamp: new Date().toISOString(),
    services: results,
  })
}
