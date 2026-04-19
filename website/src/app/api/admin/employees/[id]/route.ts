import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'
import { z } from 'zod'

const updateEmployeeSchema = z.object({
  name: z.string().min(1).optional(),
  email: z.string().email().optional(),
  role: z.enum(['admin', 'operational', 'call_center']).optional(),
  department: z.string().optional(),
  password: z.string().min(6).optional(),
})

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const validated = updateEmployeeSchema.parse(body)

    const admin = createAdminClient()

    const { data: existing } = await admin
      .from('employees')
      .select('*')
      .eq('id', id)
      .single()

    if (!existing) {
      return NextResponse.json({ error: 'Employee not found' }, { status: 404 })
    }

    const updateData: any = {}
    if (validated.name) updateData.name = validated.name
    if (validated.email) updateData.email = validated.email
    if (validated.role) updateData.role = validated.role
    if (validated.department !== undefined) updateData.department = validated.department
    if (validated.password) updateData.password_hash = validated.password

    const { data: employee, error } = await admin
      .from('employees')
      .update(updateData)
      .eq('id', id)
      .select('id, name, email, role, department, created_at')
      .single()

    if (error) throw error

    return NextResponse.json(employee)
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation error', details: error.issues },
        { status: 400 }
      )
    }
    console.error('Error updating employee:', error)
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

    const { data: existing } = await admin
      .from('employees')
      .select('*')
      .eq('id', id)
      .single()

    if (!existing) {
      return NextResponse.json({ error: 'Employee not found' }, { status: 404 })
    }

    const { error } = await admin.from('employees').delete().eq('id', id)

    if (error) throw error

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting employee:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
