import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

export async function GET() {
  try {
    const admin = createAdminClient()

    const { data: products, error } = await admin
      .from('products')
      .select('*')
      .order('name', { ascending: true })

    if (error) throw error

    return NextResponse.json({ products: products || [] })
  } catch (error) {
    console.error('Error fetching products:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
