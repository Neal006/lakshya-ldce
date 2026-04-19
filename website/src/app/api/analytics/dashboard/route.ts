import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

/** Start of current UTC day — reliable vs comparing to date-only strings. */
function startOfUtcDayIso(): string {
  const d = new Date()
  d.setUTCHours(0, 0, 0, 0)
  return d.toISOString()
}

async function loadSlaResolveMap(admin: ReturnType<typeof createAdminClient>) {
  const a = await admin
    .from('sla_config')
    .select('priority_level, resolution_time_hours')
  if (!a.error && a.data?.length) {
    const m: Record<string, number> = {}
    a.data.forEach(
      (r: { priority_level: string; resolution_time_hours: number }) => {
        m[r.priority_level] = r.resolution_time_hours
      }
    )
    return m
  }
  const b = await admin.from('sla_configs').select('priority, resolve_hours')
  if (!b.error && b.data?.length) {
    const m: Record<string, number> = {}
    b.data.forEach((r: { priority: string; resolve_hours: number }) => {
      m[r.priority] = r.resolve_hours
    })
    return m
  }
  return {}
}

export async function GET() {
  try {
    const admin = createAdminClient()
    const todayStart = startOfUtcDayIso()

    const { count: totalComplaints } = await admin
      .from('complaints')
      .select('*', { count: 'exact', head: true })

    const { count: todayComplaints } = await admin
      .from('complaints')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', todayStart)

    const { count: highPriority } = await admin
      .from('complaints')
      .select('*', { count: 'exact', head: true })
      .eq('priority', 'High')

    const { count: resolvedToday } = await admin
      .from('complaints')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'resolved')
      .gte('updated_at', todayStart)

    const { data: categoryData } = await admin
      .from('complaints')
      .select('category')

    const { data: priorityData } = await admin
      .from('complaints')
      .select('priority')

    const { data: sourceData } = await admin
      .from('complaints')
      .select('source')

    const { data: allComplaints } = await admin
      .from('complaints')
      .select('sentiment_score, status, created_at, updated_at, priority')

    const categoryCounts: Record<string, number> = {}
    categoryData?.forEach(c => {
      categoryCounts[c.category] = (categoryCounts[c.category] || 0) + 1
    })

    const priorityCounts: Record<string, number> = {}
    priorityData?.forEach(c => {
      priorityCounts[c.priority] = (priorityCounts[c.priority] || 0) + 1
    })

    const sourceCounts: Record<string, number> = {}
    sourceData?.forEach(c => {
      sourceCounts[c.source] = (sourceCounts[c.source] || 0) + 1
    })

    const totalWithCategory = Object.values(categoryCounts).reduce((a, b) => a + b, 0)
    const totalWithSource = Object.values(sourceCounts).reduce((a, b) => a + b, 0)

    let avgSentiment = 0
    let resolvedCount = 0
    let avgResolutionHours: number | null = null
    if (allComplaints?.length) {
      const sentiments = allComplaints.filter(c => c.sentiment_score !== null).map(c => c.sentiment_score)
      avgSentiment = sentiments.length > 0
        ? Math.round((sentiments.reduce((a, b) => a + b, 0) / sentiments.length) * 100) / 100
        : 0
      resolvedCount = allComplaints.filter(c => c.status === 'resolved' || c.status === 'closed').length

      const withResolution = allComplaints.filter(
        c =>
          (c.status === 'resolved' || c.status === 'closed') &&
          c.updated_at &&
          c.created_at
      )
      if (withResolution.length > 0) {
        const totalHours = withResolution.reduce((sum, c) => {
          const start = new Date(c.created_at).getTime()
          // Use updated_at when `resolved_at` column is not present in DB (approx. resolution time).
          const end = new Date(c.updated_at).getTime()
          return sum + Math.max(0, (end - start) / (1000 * 60 * 60))
        }, 0)
        avgResolutionHours = Math.round((totalHours / withResolution.length) * 10) / 10
      }
    }

    const slaMap = await loadSlaResolveMap(admin)

    const withinSla = (() => {
      if (!allComplaints?.length || !Object.keys(slaMap).length)
        return { met: 0, judged: 0 }
      let met = 0
      let judged = 0
      for (const c of allComplaints) {
        if (c.status !== 'resolved' && c.status !== 'closed') continue
        if (!c.updated_at || !c.created_at || !c.priority) continue
        judged++
        const hours =
          (new Date(c.updated_at).getTime() - new Date(c.created_at).getTime()) / (1000 * 60 * 60)
        const limit = slaMap[c.priority] ?? 72
        if (hours <= limit) met++
      }
      return { met, judged }
    })()

    const slaCompliance =
      withinSla.judged > 0 ? Math.round((withinSla.met / withinSla.judged) * 100) : (resolvedCount > 0 ? 100 : 100)

    return NextResponse.json({
      summary: {
        total_complaints: totalComplaints || 0,
        today_complaints: todayComplaints || 0,
        high_priority: highPriority || 0,
        resolved_today: resolvedToday || 0,
        avg_resolution_time_hours: avgResolutionHours ?? 0,
        sla_compliance_percent: slaCompliance,
        avg_sentiment: avgSentiment,
      },
      by_category: Object.entries(categoryCounts).map(([name, value]) => ({
        name,
        value,
        percentage: totalWithCategory > 0 ? Math.round((value / totalWithCategory) * 100 * 10) / 10 : 0,
      })),
      by_priority: Object.entries(priorityCounts).map(([name, value]) => ({
        name,
        value,
        percentage: totalWithCategory > 0 ? Math.round((value / totalWithCategory) * 100 * 10) / 10 : 0,
      })),
      by_source: Object.entries(sourceCounts).map(([name, value]) => ({
        name,
        value,
        percentage: totalWithSource > 0 ? Math.round((value / totalWithSource) * 100 * 10) / 10 : 0,
      })),
    })
  } catch (error) {
    console.error('Error fetching dashboard analytics:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
