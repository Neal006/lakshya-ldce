import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const priority = searchParams.get('priority')
    const category = searchParams.get('category')

    const admin = createAdminClient()
    let query = admin
      .from('complaints')
      .select('*, products(*)')
      .order('created_at', { ascending: false })

    if (status) query = query.eq('status', status)
    if (priority) query = query.eq('priority', priority)
    if (category) query = query.eq('category', category)

    const { data: complaints, error } = await query

    if (error) throw error

    const headers = [
      'ID', 'Date', 'Customer', 'Email', 'Phone', 'Product',
      'Category', 'Priority', 'Sentiment', 'Source', 'Status',
      'Assigned Team', 'Escalation', 'Complaint Text',
    ]

    const rows = (complaints || []).map(c => [
      c.id,
      new Date(c.created_at).toISOString().split('T')[0],
      c.customer_name || '',
      c.customer_email || '',
      c.customer_phone || '',
      c.products?.name || '',
      c.category,
      c.priority,
      (c.sentiment_score || 0).toFixed(2),
      c.source,
      c.status,
      c.assigned_team || '',
      c.escalation_required ? 'Yes' : 'No',
      `"${(c.complaint_text || '').replace(/"/g, '""')}"`,
    ])

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')

    return new NextResponse(csvContent, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="complaints_${new Date().toISOString().split('T')[0]}.csv"`,
      },
    })
  } catch (error) {
    console.error('Error exporting complaints:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
