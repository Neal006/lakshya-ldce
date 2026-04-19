import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

export async function GET() {
  try {
    const admin = createAdminClient()

    const { data: slaConfigs, error } = await admin
      .from('sla_config')
      .select('*')
      .order('priority_level', { ascending: true })

    if (error) throw error

    return NextResponse.json({ sla_configs: slaConfigs || [] })
  } catch (error) {
    console.error('Error fetching SLA config:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { priority_level, response_time_hours, resolution_time_hours } = body

    if (!priority_level || response_time_hours === undefined || resolution_time_hours === undefined) {
      return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
    }

    const admin = createAdminClient()

    const { data: existing } = await admin
      .from('sla_config')
      .select('*')
      .eq('priority_level', priority_level)
      .single()

    let result
    if (existing) {
      const { data, error } = await admin
        .from('sla_config')
        .update({ response_time_hours, resolution_time_hours })
        .eq('priority_level', priority_level)
        .select()
        .single()
      if (error) throw error
      result = data
    } else {
      const { data, error } = await admin
        .from('sla_config')
        .insert({ priority_level, response_time_hours, resolution_time_hours })
        .select()
        .single()
      if (error) throw error
      result = data
    }

    return NextResponse.json(result)
  } catch (error) {
    console.error('Error updating SLA config:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
