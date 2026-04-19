import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const q = searchParams.get('q') || ''
    const status = searchParams.get('status')
    const priority = searchParams.get('priority')
    const category = searchParams.get('category')
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '20')

    const admin = createAdminClient()
    let query = admin
      .from('complaints')
      .select('*, products(*)', { count: 'exact' })
      .order('created_at', { ascending: false })

    if (status) query = query.eq('status', status)
    if (priority) query = query.eq('priority', priority)
    if (category) query = query.eq('category', category)

    if (q) {
      query = query.or(
        `complaint_text.ilike.%${q}%,customer_name.ilike.%${q}%,customer_email.ilike.%${q}%`
      )
    }

    const start = (page - 1) * limit
    const end = start + limit - 1
    query = query.range(start, end)

    const { data: complaints, error, count } = await query

    if (error) throw error

    return NextResponse.json({
      complaints: complaints || [],
      pagination: {
        page,
        limit,
        total: count || 0,
        totalPages: Math.ceil((count || 0) / limit),
      },
      query: q,
    })
  } catch (error) {
    console.error('Error searching complaints:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
