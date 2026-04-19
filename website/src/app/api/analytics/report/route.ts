import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'
import { generateReport } from '@/lib/genai-client'

export async function GET() {
  try {
    const admin = createAdminClient()
    const today = new Date().toISOString().split('T')[0]
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
    const sevenDaysAgo = new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0]

    const { count: totalComplaints } = await admin.from('complaints').select('*', { count: 'exact', head: true })
    const { count: todayComplaints } = await admin.from('complaints').select('*', { count: 'exact', head: true }).gte('created_at', today)
    const { count: highPriority } = await admin.from('complaints').select('*', { count: 'exact', head: true }).eq('priority', 'High')
    const { count: resolvedToday } = await admin.from('complaints').select('*', { count: 'exact', head: true }).eq('status', 'resolved').gte('updated_at', today)

    const { data: categoryData } = await admin.from('complaints').select('category')
    const { data: priorityData } = await admin.from('complaints').select('priority')
    const { data: sourceData } = await admin.from('complaints').select('source')
    const { data: allComplaints } = await admin.from('complaints').select('sentiment_score, status')

    const categoryCounts: Record<string, number> = {}
    categoryData?.forEach(c => { categoryCounts[c.category] = (categoryCounts[c.category] || 0) + 1 })

    const priorityCounts: Record<string, number> = {}
    priorityData?.forEach(c => { priorityCounts[c.priority] = (priorityCounts[c.priority] || 0) + 1 })

    const sourceCounts: Record<string, number> = {}
    sourceData?.forEach(c => { sourceCounts[c.source] = (sourceCounts[c.source] || 0) + 1 })

    let avgSentiment = 0
    let resolvedCount = 0
    if (allComplaints?.length) {
      const sentiments = allComplaints.filter(c => c.sentiment_score !== null).map(c => c.sentiment_score)
      avgSentiment = sentiments.length > 0 ? Math.round((sentiments.reduce((a, b) => a + b, 0) / sentiments.length) * 100) / 100 : 0
      resolvedCount = allComplaints.filter(c => c.status === 'resolved' || c.status === 'closed').length
    }

    const slaCompliance = (totalComplaints || 0) > 0 ? Math.round((resolvedCount / (totalComplaints || 1)) * 100) : 100

    const { data: recentComplaints } = await admin.from('complaints').select('created_at, priority, category, sentiment_score, status').gte('created_at', sevenDaysAgo).order('created_at', { ascending: true })

    const dailyMap = new Map<string, { date: string; total: number; by_priority: Record<string, number>; resolved: number; sentiment_sum: number; sentiment_count: number }>()
    for (let i = 0; i <= 6; i++) {
      const day = new Date(Date.now() - (6 - i) * 86400000)
      const key = day.toISOString().split('T')[0]
      dailyMap.set(key, { date: day.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), total: 0, by_priority: { High: 0, Medium: 0, Low: 0 }, resolved: 0, sentiment_sum: 0, sentiment_count: 0 })
    }
    recentComplaints?.forEach(c => {
      const key = c.created_at.split('T')[0]
      const day = dailyMap.get(key)
      if (day) {
        day.total++
        day.by_priority[c.priority] = (day.by_priority[c.priority] || 0) + 1
        day.sentiment_sum += c.sentiment_score || 0
        day.sentiment_count++
        if (c.status === 'resolved' || c.status === 'closed') day.resolved++
      }
    })
    const daily = Array.from(dailyMap.values()).map(day => ({ ...day, avg_sentiment: day.sentiment_count > 0 ? Math.round((day.sentiment_sum / day.sentiment_count) * 100) / 100 : 0, complaints: day.total, high: day.by_priority.High || 0, medium: day.by_priority.Medium || 0, low: day.by_priority.Low || 0 }))

    const trendDirection = daily.length >= 2 ? (daily[daily.length - 1].total > daily[0].total ? 'increasing' : 'declining') : 'stable'
    const peakDay = daily.reduce((max, day) => day.total > max.total ? day : max, daily[0])

    const { data: products } = await admin.from('products').select('id, name')
    const { data: allComplaintsForProducts } = await admin.from('complaints').select('product_id, sentiment_score, priority, status')
    const productAnalytics = (products || []).map(product => {
      const c = (allComplaintsForProducts || []).filter(x => x.product_id === product.id)
      const total = c.length
      const avg = total > 0 ? Math.round((c.reduce((sum, x) => sum + (x.sentiment_score || 0), 0) / total) * 100) / 100 : 0
      const pos = c.filter(x => x.sentiment_score >= 0.05).length
      const neg = c.filter(x => x.sentiment_score < -0.05).length
      const hi = c.filter(x => x.priority === 'High').length
      const res = c.filter(x => x.status === 'resolved' || x.status === 'closed').length
      return { name: product.name, total_complaints: total, avg_sentiment: avg, positive: pos, negative: neg, high_priority: hi, resolution_rate: total > 0 ? Math.round((res / total) * 100) : 0 }
    })

    const categoryStr = Object.entries(categoryCounts).map(([k, v]) => `  - ${k}: ${v}`).join('\n') || '  No data'
    const priorityStr = Object.entries(priorityCounts).map(([k, v]) => `  - ${k}: ${v}`).join('\n') || '  No data'
    const sourceStr = Object.entries(sourceCounts).map(([k, v]) => `  - ${k}: ${v}`).join('\n') || '  No data'
    const dailyStr = daily.map(d => `  ${d.date}: ${d.total} complaints (High: ${d.high}, Med: ${d.medium}, Low: ${d.low}), Avg Sentiment: ${d.avg_sentiment}`).join('\n') || '  No data'
    const productStr = productAnalytics.map(p => `  - ${p.name}: ${p.total_complaints} complaints, Avg Sentiment: ${p.avg_sentiment}, Positive: ${p.positive}, Negative: ${p.negative}, Resolution Rate: ${p.resolution_rate}%`).join('\n') || '  No data'

    const reportRequest = {
      total_complaints: totalComplaints || 0,
      today_complaints: todayComplaints || 0,
      high_priority: highPriority || 0,
      resolved_today: resolvedToday || 0,
      avg_sentiment: avgSentiment,
      sla_compliance: slaCompliance,
      category_breakdown: categoryStr,
      priority_breakdown: priorityStr,
      source_breakdown: sourceStr,
      daily_trends: dailyStr,
      product_analytics: productStr,
      trend_direction: trendDirection,
      peak_day: peakDay.date,
      peak_count: peakDay.total,
    }

    let report
    try {
      report = await generateReport(reportRequest)
    } catch (genAIError) {
      console.error('GenAI report generation failed:', genAIError)
      return NextResponse.json({
        error: 'Report generation failed',
        fallback: {
          executive_summary: `Total of ${totalComplaints} complaints recorded. ${todayComplaints} new complaints today with ${highPriority} high priority cases.`,
          key_findings: [`${Object.values(categoryCounts).sort((a, b) => b - a)[0] || 0} complaints in the top category`, `SLA compliance at ${slaCompliance}%`, `Average sentiment score: ${avgSentiment}`],
          trend_analysis: `Complaint trend is ${trendDirection} over the last 7 days. Peak day was ${peakDay.date} with ${peakDay.total} complaints.`,
          product_insights: productAnalytics.map(p => `${p.name} has ${p.total_complaints} complaints`).join('. ') + '.',
          category_breakdown: categoryStr,
          priority_assessment: `${highPriority} high priority complaints require immediate attention.`,
          recommendations: ['Review high priority complaints immediately', 'Monitor trending products for quality issues'],
          risk_flags: (highPriority || 0) > 5 ? ['High volume of critical complaints'] : [],
        },
      }, { status: 206 })
    }

    return NextResponse.json({ report })
  } catch (error) {
    console.error('Error generating report:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
