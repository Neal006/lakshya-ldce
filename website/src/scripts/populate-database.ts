/**
 * Idempotent demo seed via Supabase service role.
 * Usage: npm run db:populate
 * Requires: NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 */
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

/** bcrypt hash for password `admin123` (cost 12) */
const HASH =
  '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi'

const EMPLOYEES = [
  {
    id: 'a0000000-0000-0000-0000-000000000001',
    name: 'Admin User',
    email: 'admin@company.com',
    password_hash: HASH,
    role: 'admin',
    department: 'Management',
  },
  {
    id: 'a0000000-0000-0000-0000-000000000002',
    name: 'Operations Manager',
    email: 'ops@company.com',
    password_hash: HASH,
    role: 'operational',
    department: 'Operations',
  },
  {
    id: 'a0000000-0000-0000-0000-000000000003',
    name: 'Support Agent',
    email: 'support@company.com',
    password_hash: HASH,
    role: 'call_center',
    department: 'Customer Support',
  },
  {
    id: 'a0000000-0000-0000-0000-000000000004',
    name: 'QA Lead',
    email: 'qa@company.com',
    password_hash: HASH,
    role: 'quality_assurance',
    department: 'Quality Assurance',
  },
]

async function seedSla(admin: ReturnType<typeof createClient>) {
  const rowsConfig = [
    { priority_level: 'High', response_time_hours: 1, resolution_time_hours: 4 },
    { priority_level: 'Medium', response_time_hours: 4, resolution_time_hours: 24 },
    { priority_level: 'Low', response_time_hours: 24, resolution_time_hours: 72 },
  ]
  const rowsConfigs = [
    { priority: 'High', response_hours: 1, resolve_hours: 4 },
    { priority: 'Medium', response_hours: 4, resolve_hours: 24 },
    { priority: 'Low', response_hours: 24, resolve_hours: 72 },
  ]

  const r = await admin.from('sla_config').upsert(rowsConfig, {
    onConflict: 'priority_level',
  })
  if (!r.error) {
    console.log('✅ SLA: sla_config upserted')
    return
  }
  const r2 = await admin.from('sla_configs').upsert(rowsConfigs, {
    onConflict: 'priority',
  })
  if (r2.error) {
    console.warn('⚠️ SLA:', r.error.message, '|', r2.error.message)
  } else {
    console.log('✅ SLA: sla_configs upserted')
  }
}

async function main() {
  if (!supabaseUrl || !supabaseServiceKey) {
    console.error('Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY')
    process.exit(1)
  }

  const admin = createClient(supabaseUrl, supabaseServiceKey)

  for (const e of EMPLOYEES) {
    const { error } = await admin.from('employees').upsert(e, { onConflict: 'email' })
    if (error) console.error('employees', e.email, error.message)
    else console.log('✅ employee', e.email)
  }

  await seedSla(admin)

  const products = [
    {
      id: 'p0000001-0000-0000-0000-000000000001',
      name: 'Parle-G Glucose Biscuits',
      sku: 'PLG-001',
      category: 'Product',
    },
    {
      id: 'p0000002-0000-0000-0000-000000000002',
      name: 'Frooti Mango Drink',
      sku: 'FRT-002',
      category: 'Product',
    },
    {
      id: 'p0000003-0000-0000-0000-000000000003',
      name: 'Marie Gold Biscuits',
      sku: 'MRG-003',
      category: 'Product',
    },
    {
      id: 'p0000004-0000-0000-0000-000000000004',
      name: 'Hide & Seek Cookies',
      sku: 'HDS-004',
      category: 'Product',
    },
    {
      id: 'p0000005-0000-0000-0000-000000000005',
      name: 'Bakery Fresh Bread',
      sku: 'BFB-005',
      category: 'Product',
    },
    {
      id: 'p0000006-0000-0000-0000-000000000006',
      name: 'Tropical Juice Pack',
      sku: 'TJP-006',
      category: 'Product',
    },
  ]

  for (const p of products) {
    const { error } = await admin.from('products').upsert(p, { onConflict: 'sku' })
    if (error) console.error('product', p.sku, error.message)
  }
  console.log('✅ products upserted')

  const customers = [
    {
      id: 'c0000001-0000-0000-0000-000000000001',
      name: 'Rajesh Kumar',
      email: 'rajesh.kumar@email.com',
      phone: '+91-98765-43201',
    },
    {
      id: 'c0000002-0000-0000-0000-000000000002',
      name: 'Priya Sharma',
      email: 'priya.sharma@email.com',
      phone: '+91-98765-43202',
    },
    {
      id: 'c0000003-0000-0000-0000-000000000003',
      name: 'Amit Patel',
      email: 'amit.patel@email.com',
      phone: '+91-98765-43203',
    },
    {
      id: 'c0000004-0000-0000-0000-000000000004',
      name: 'Sunita Verma',
      email: 'sunita.verma@email.com',
      phone: '+91-98765-43204',
    },
    {
      id: 'c0000005-0000-0000-0000-000000000005',
      name: 'Deepak Singh',
      email: 'deepak.singh@email.com',
      phone: '+91-98765-43205',
    },
  ]

  for (const c of customers) {
    const { error } = await admin.from('customers').upsert(c, { onConflict: 'email' })
    if (error) console.error('customer', c.email, error.message)
  }
  console.log('✅ customers upserted')

  const complaints = [
    {
      id: 'd0000d01-0000-4000-8000-000000000001',
      complaint_text:
        'Plastic fragment found inside biscuit pack — safety concern.',
      category: 'Product' as const,
      priority: 'High' as const,
      sentiment_score: -0.85,
      source: 'call' as const,
      status: 'in_progress' as const,
      immediate_action: 'Hold batch review',
      assigned_team: 'Quality Assurance',
      escalation_required: true,
      customer_id: 'c0000001-0000-0000-0000-000000000001',
      product_id: 'p0000001-0000-0000-0000-000000000001',
    },
    {
      id: 'd0000d02-0000-4000-8000-000000000002',
      complaint_text: 'Frooti tasted off; suspected storage issue.',
      category: 'Product' as const,
      priority: 'High' as const,
      sentiment_score: -0.7,
      source: 'email' as const,
      status: 'assigned' as const,
      immediate_action: 'Cold chain check',
      assigned_team: 'Supply Chain',
      escalation_required: false,
      customer_id: 'c0000002-0000-0000-0000-000000000002',
      product_id: 'p0000002-0000-0000-0000-000000000002',
    },
    {
      id: 'd0000d03-0000-4000-8000-000000000003',
      complaint_text: 'Packaging hard to open — spills every time.',
      category: 'Packaging' as const,
      priority: 'Medium' as const,
      sentiment_score: -0.35,
      source: 'email' as const,
      status: 'new' as const,
      assigned_team: 'Packaging Team',
      escalation_required: false,
      customer_id: 'c0000003-0000-0000-0000-000000000003',
      product_id: 'p0000001-0000-0000-0000-000000000001',
    },
  ]

  for (const row of complaints) {
    const { error } = await admin.from('complaints').upsert(row, { onConflict: 'id' })
    if (error) console.error('complaint', row.id, error.message)
  }
  console.log('✅ sample complaints upserted (3 rows; run SQL file for full set)')

  console.log('\nDone. Logins (password admin123): admin@company.com, ops@company.com, support@company.com, qa@company.com')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
