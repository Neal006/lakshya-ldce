import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

export async function GET() {
  try {
    const admin = createAdminClient()

    const { data: products } = await admin
      .from('products')
      .select('id, name, sku, category')

    const { data: complaints } = await admin
      .from('complaints')
      .select('product_id, sentiment_score, priority, category, status')

    const productAnalytics = (products || []).map(product => {
      const productComplaints = (complaints || []).filter(c => c.product_id === product.id)
      const totalComplaints = productComplaints.length
      const avgSentiment = totalComplaints > 0
        ? Math.round((productComplaints.reduce((sum, c) => sum + (c.sentiment_score || 0), 0) / totalComplaints) * 100) / 100
        : 0
      const positiveCount = productComplaints.filter(c => c.sentiment_score >= 0.05).length
      const negativeCount = productComplaints.filter(c => c.sentiment_score < -0.05).length
      const highPriorityCount = productComplaints.filter(c => c.priority === 'High').length

      const categoryCounts: Record<string, number> = {}
      productComplaints.forEach(c => {
        categoryCounts[c.category] = (categoryCounts[c.category] || 0) + 1
      })

      const topIssues = Object.entries(categoryCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 3)
        .map(([cat]) => cat.toLowerCase())

      const resolved = productComplaints.filter(c => c.status === 'resolved' || c.status === 'closed').length

      return {
        product_id: product.id,
        name: product.name,
        sku: product.sku,
        category: product.category,
        total_complaints: totalComplaints,
        avg_sentiment: avgSentiment,
        positive_count: positiveCount,
        negative_count: negativeCount,
        high_priority_count: highPriorityCount,
        resolution_rate: totalComplaints > 0 ? Math.round((resolved / totalComplaints) * 100) : 0,
        sentiment_trend: avgSentiment > -0.2 ? 'stable' : 'declining',
        top_issues: topIssues,
      }
    })

    productAnalytics.sort((a, b) => b.total_complaints - a.total_complaints)

    return NextResponse.json({ products: productAnalytics })
  } catch (error) {
    console.error('Error fetching product analytics:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
