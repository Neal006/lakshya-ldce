import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase-client'
import { z } from 'zod'
import bcrypt from 'bcryptjs'

const createEmployeeSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(6),
  role: z.enum(['admin', 'operational', 'call_center', 'quality_assurance']),
  department: z.string().optional(),
})

export async function GET() {
  try {
    const admin = createAdminClient()

    const { data: employees, error } = await admin
      .from('employees')
      .select('id, name, email, role, department, created_at')
      .order('created_at', { ascending: false })

    if (error) throw error

    return NextResponse.json({ employees: employees || [] })
  } catch (error) {
    console.error('Error fetching employees:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validated = createEmployeeSchema.parse(body)

    const admin = createAdminClient()

    const { data: existing } = await admin
      .from('employees')
      .select('id')
      .eq('email', validated.email)
      .single()

    if (existing) {
      return NextResponse.json({ error: 'Email already exists' }, { status: 409 })
    }

    const password_hash = await bcrypt.hash(validated.password, 10)

    const { data: employee, error } = await admin
      .from('employees')
      .insert({
        name: validated.name,
        email: validated.email,
        password_hash,
        role: validated.role,
        department: validated.department,
      })
      .select('id, name, email, role, department, created_at')
      .single()

    if (error) throw error

    return NextResponse.json(employee, { status: 201 })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation error', details: error.issues },
        { status: 400 }
      )
    }
    console.error('Error creating employee:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
