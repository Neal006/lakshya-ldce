import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

/** Normalize `sla_config` (Supabase default) for the app UI. */
function normalizeSlaRows(rows: Record<string, unknown>[] | null) {
  return (rows || []).map((r) => ({
    id: r.id,
    priority: r.priority_level as string,
    priority_level: r.priority_level as string,
    response_hours: r.response_time_hours as number,
    resolve_hours: r.resolution_time_hours as number,
    response_time_hours: r.response_time_hours as number,
    resolution_time_hours: r.resolution_time_hours as number,
    updated_at: r.updated_at,
  }))
}

function normalizeSlaConfigsPlural(
  rows: Record<string, unknown>[] | null
) {
  return (rows || []).map((r) => ({
    id: r.id,
    priority: r.priority as string,
    priority_level: r.priority as string,
    response_hours: r.response_hours as number,
    resolve_hours: r.resolve_hours as number,
    response_time_hours: r.response_hours as number,
    resolution_time_hours: r.resolve_hours as number,
    updated_at: r.updated_at,
  }))
}

export async function GET() {
  try {
    const admin = createAdminClient()

    const a = await admin
      .from('sla_config')
      .select('*')
      .order('priority_level', { ascending: true })

    if (!a.error && a.data?.length) {
      return NextResponse.json({ sla_configs: normalizeSlaRows(a.data) })
    }

    const b = await admin
      .from('sla_configs')
      .select('*')
      .order('priority', { ascending: true })

    if (b.error) throw b.error

    return NextResponse.json({ sla_configs: normalizeSlaConfigsPlural(b.data) })
  } catch (error) {
    console.error('Error fetching SLA config:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const priority =
      (body.priority as string) || (body.priority_level as string)
    const response_hours =
      body.response_hours ?? body.response_time_hours
    const resolve_hours =
      body.resolve_hours ?? body.resolution_time_hours

    if (!priority || response_hours === undefined || resolve_hours === undefined) {
      return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
    }

    const admin = createAdminClient()

    const { data, error } = await admin
      .from('sla_config')
      .update({
        response_time_hours: response_hours,
        resolution_time_hours: resolve_hours,
        updated_at: new Date().toISOString(),
      })
      .eq('priority_level', priority)
      .select()
      .single()

    if (error) throw error

    return NextResponse.json(
      normalizeSlaRows(data ? [data as Record<string, unknown>] : [])[0] ?? data
    )
  } catch (error) {
    console.error('Error updating SLA config:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
