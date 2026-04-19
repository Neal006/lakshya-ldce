import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

/** QA: recurring product issues, category balance, trend hints */
export async function GET() {
  try {
    const admin = createAdminClient()

    const { data: products } = await admin.from('products').select('id, name, sku, category')
    const { data: complaints } = await admin
      .from('complaints')
      .select('id, product_id, category, priority, status, created_at, sentiment_score')

    const byProduct = (products || []).map((p) => {
      const rows = (complaints || []).filter((c) => c.product_id === p.id)
      const high = rows.filter((c) => c.priority === 'High').length
      const open = rows.filter(
        (c) => !['resolved', 'closed'].includes(c.status)
      ).length
      const catCounts: Record<string, number> = {}
      rows.forEach((c) => {
        catCounts[c.category] = (catCounts[c.category] || 0) + 1
      })
      const dominant = Object.entries(catCounts).sort((a, b) => b[1] - a[1])[0]
      return {
        product_id: p.id,
        name: p.name,
        sku: p.sku,
        total: rows.length,
        high_priority_count: high,
        open_count: open,
        dominant_category: dominant ? dominant[0] : null,
        dominant_share:
          rows.length && dominant
            ? Math.round((dominant[1] / rows.length) * 100)
            : 0,
      }
    })

    const recurring = byProduct
      .filter((x) => x.total >= 4 && (x.high_priority_count >= 2 || x.open_count >= 3))
      .map((x) => ({
        ...x,
        severity: x.high_priority_count >= 3 ? 'critical' : 'warning',
        message:
          x.high_priority_count >= 3
            ? `Elevated high-priority complaints for ${x.name}. Investigate product or batch quality.`
            : `Recurring volume on ${x.name} (${x.total} tickets). Review classification consistency and root cause.`,
      }))
      .sort((a, b) => b.total - a.total)

    const all = complaints || []
    const catTotals: Record<string, number> = {}
    all.forEach((c) => {
      catTotals[c.category] = (catTotals[c.category] || 0) + 1
    })
    const total = all.length || 1
    const category_balance = Object.entries(catTotals).map(([name, value]) => ({
      name,
      value,
      pct: Math.round((value / total) * 1000) / 10,
    }))

    const priTotals: Record<string, number> = {}
    all.forEach((c) => {
      priTotals[c.priority] = (priTotals[c.priority] || 0) + 1
    })
    const priority_mix = Object.entries(priTotals).map(([name, value]) => ({
      name,
      value,
      pct: Math.round((value / total) * 1000) / 10,
    }))

    return NextResponse.json({
      recurring_alerts: recurring,
      category_balance,
      priority_mix,
      classification_note:
        Object.keys(catTotals).length >= 2
          ? 'Category mix looks distributed; spot-check low-volume categories for misclassification.'
          : 'Limited category diversity in dataset; validate classifier on edge cases.',
    })
  } catch (error) {
    console.error('QA insights error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
