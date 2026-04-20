import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'
import { auth } from '@/lib/auth'
import { isSupabaseUnreachableError, supabaseUnavailableResponse } from '@/lib/supabase-http'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const admin = createAdminClient()

    const { data: complaint, error } = await admin
      .from('complaints')
      .select('*, products(*), complaint_timeline(*)')
      .eq('id', id)
      .single()

    if (error || !complaint) {
      return NextResponse.json({ error: 'Complaint not found' }, { status: 404 })
    }

    return NextResponse.json(complaint)
  } catch (error) {
    console.error('Error fetching complaint:', error)
    if (isSupabaseUnreachableError(error)) return supabaseUnavailableResponse()
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await auth()
    const actor = session?.user?.email || session?.user?.name || 'Agent'

    const { id } = await params
    const body = await request.json()
    const { status, complaint_text, category, priority, immediate_action, assigned_team, escalation_required, customer_response } = body

    const admin = createAdminClient()

    const { data: existing } = await admin
      .from('complaints')
      .select('*')
      .eq('id', id)
      .single()

    if (!existing) {
      return NextResponse.json({ error: 'Complaint not found' }, { status: 404 })
    }

    const updateData: any = {}
    if (status) updateData.status = status
    if (complaint_text) updateData.complaint_text = complaint_text
    if (category) updateData.category = category
    if (priority) updateData.priority = priority
    if (immediate_action !== undefined) updateData.immediate_action = immediate_action
    if (assigned_team) updateData.assigned_team = assigned_team
    if (escalation_required !== undefined) updateData.escalation_required = escalation_required
    if (customer_response) updateData.customer_response = customer_response
    updateData.updated_at = new Date().toISOString()
    // Note: set `resolved_at` only after running supabase/migrations/004_add_resolved_at_complaints.sql
    // so PostgREST schema includes the column; otherwise PATCH fails with PGRST204.

const { data: complaint, error } = await admin
      .from('complaints')
      .update(updateData)
      .eq('id', id)
      .select('*, products(*)')
      .single()

    if (error) throw error

    if (status && status !== existing.status) {
      await admin.from('complaint_timeline').insert({
        complaint_id: id,
        action: `Status changed from ${existing.status} to ${status}`,
        performed_by: actor,
        metadata: { from: existing.status, to: status },
      })
    }
    if (complaint_text && complaint_text !== existing.complaint_text) {
      await admin.from('complaint_timeline').insert({
        complaint_id: id,
        action: 'Complaint text updated',
        performed_by: actor,
        metadata: { source: 'text_edit' },
      })
    }
    if (category && category !== existing.category) {
      await admin.from('complaint_timeline').insert({
        complaint_id: id,
        action: `Category updated to ${category}`,
        performed_by: actor,
        metadata: { from: existing.category, to: category },
      })
    }
    if (priority && priority !== existing.priority) {
      await admin.from('complaint_timeline').insert({
        complaint_id: id,
        action: `Priority updated to ${priority}`,
        performed_by: actor,
        metadata: { from: existing.priority, to: priority },
      })
    }

    return NextResponse.json(complaint)
  } catch (error) {
    console.error('Error updating complaint:', error)
    if (isSupabaseUnreachableError(error)) return supabaseUnavailableResponse()
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const admin = createAdminClient()

    await admin.from('complaint_timeline').delete().eq('complaint_id', id)
    const { error } = await admin.from('complaints').delete().eq('id', id)

    if (error) throw error

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting complaint:', error)
    if (isSupabaseUnreachableError(error)) return supabaseUnavailableResponse()
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
