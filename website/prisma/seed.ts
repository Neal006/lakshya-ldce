import { PrismaClient, Role, Priority } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  console.log('Seeding database...')

  const passwordHash = await bcrypt.hash('admin123', 10)

  const admin = await prisma.user.upsert({
    where: { email: 'admin@company.com' },
    update: {},
    create: {
      email: 'admin@company.com',
      name: 'Admin User',
      password_hash: passwordHash,
      role: Role.admin,
      department: 'Management',
    },
  })

  const operational = await prisma.user.upsert({
    where: { email: 'ops@company.com' },
    update: {},
    create: {
      email: 'ops@company.com',
      name: 'Operations User',
      password_hash: passwordHash,
      role: Role.operational,
      department: 'Operations',
    },
  })

  const callCenter = await prisma.user.upsert({
    where: { email: 'support@company.com' },
    update: {},
    create: {
      email: 'support@company.com',
      name: 'Support Agent',
      password_hash: passwordHash,
      role: Role.call_center,
      department: 'Support',
    },
  })

  console.log('Created users:', { admin: admin.email, ops: operational.email, support: callCenter.email })

  const products = [
    { name: 'ProWellness Collagen Peptide', sku: 'PW-COL-001', category: 'supplement' },
    { name: 'ImmunoBoost Vitamin C + Zinc', sku: 'IB-VIT-002', category: 'vitamin' },
    { name: 'OmegaCare Deep Sea Fish Oil', sku: 'OC-OMG-003', category: 'wellness' },
    { name: 'VitaGlow Multivitamin Complex', sku: 'VG-MUL-004', category: 'vitamin' },
    { name: 'PureHerb Ashwagandha Capsules', sku: 'PH-ASH-005', category: 'supplement' },
    { name: 'FlexiJoint Glucosamine Tablets', sku: 'FJ-GLU-006', category: 'wellness' },
  ]

  for (const product of products) {
    await prisma.product.upsert({
      where: { sku: product.sku },
      update: {},
      create: product,
    })
  }

  console.log('Created', products.length, 'products')

  const slaConfigs = [
    { priority: Priority.High, response_hours: 1, resolve_hours: 4 },
    { priority: Priority.Medium, response_hours: 4, resolve_hours: 24 },
    { priority: Priority.Low, response_hours: 24, resolve_hours: 72 },
  ]

  for (const sla of slaConfigs) {
    await prisma.sLAConfig.upsert({
      where: { priority: sla.priority },
      update: sla,
      create: sla,
    })
  }

  console.log('Created SLA configs')

  console.log('Database seeded successfully!')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })