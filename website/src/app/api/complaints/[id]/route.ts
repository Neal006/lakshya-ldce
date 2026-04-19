import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'

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
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
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
        status_from: existing.status,
        status_to: status,
        changed_by: 'System',
        notes: `Status changed from ${existing.status} to ${status}`,
      })
    }

    return NextResponse.json(complaint)
  } catch (error) {
    console.error('Error updating complaint:', error)
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
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
