import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

export async function GET() {
  try {
    const admin = createAdminClient()

    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - 6)

    const { data: complaints, error } = await admin
      .from('complaints')
      .select('created_at, priority, category, sentiment_score, status')
      .gte('created_at', startDate.toISOString())
      .order('created_at', { ascending: true })

    if (error) throw error

    const dailyMap = new Map<string, {
      date: string
      total: number
      by_priority: Record<string, number>
      by_category: Record<string, number>
      resolved: number
      avg_sentiment: number
      sentiment_sum: number
      sentiment_count: number
    }>()

    for (let i = 0; i <= 6; i++) {
      const day = new Date(startDate)
      day.setDate(startDate.getDate() + i)
      const key = day.toISOString().split('T')[0]
      dailyMap.set(key, {
        date: day.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        total: 0,
        by_priority: { High: 0, Medium: 0, Low: 0 },
        by_category: { Product: 0, Packaging: 0, Trade: 0 },
        resolved: 0,
        avg_sentiment: 0,
        sentiment_sum: 0,
        sentiment_count: 0,
      })
    }

    complaints?.forEach(c => {
      const key = c.created_at.split('T')[0]
      const day = dailyMap.get(key)
      if (day) {
        day.total++
        day.by_priority[c.priority] = (day.by_priority[c.priority] || 0) + 1
        day.by_category[c.category] = (day.by_category[c.category] || 0) + 1
        day.sentiment_sum += c.sentiment_score || 0
        day.sentiment_count++
        if (c.status === 'resolved' || c.status === 'closed') {
          day.resolved++
        }
      }
    })

    const daily = Array.from(dailyMap.values()).map(day => ({
      ...day,
      avg_sentiment: day.sentiment_count > 0
        ? Math.round((day.sentiment_sum / day.sentiment_count) * 100) / 100
        : 0,
      complaints: day.total,
      high: day.by_priority.High || 0,
      medium: day.by_priority.Medium || 0,
      low: day.by_priority.Low || 0,
    }))

    const totalComplaints = complaints?.length || 0
    const peakDay = daily.reduce((max, day) => day.total > max.total ? day : max, daily[0])
    const trendDirection = daily.length >= 2
      ? (daily[daily.length - 1].total > daily[0].total ? 'increasing' : 'declining')
      : 'stable'

    return NextResponse.json({
      daily,
      trend_direction: trendDirection,
      peak_day: peakDay.date,
      peak_count: peakDay.total,
      total_period: totalComplaints,
    })
  } catch (error) {
    console.error('Error fetching trends:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
