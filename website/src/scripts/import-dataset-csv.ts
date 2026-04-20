/**
 * Import complaints from text_classifier/data/data.csv into Supabase.
 *
 * CSV columns: complaint_id, text, category, priority, sentiment, resolution_time
 * Creates placeholder customer + 3 products (Product / Packaging / Trade) for FKs.
 *
 * From `website/`:
 *   set NEXT_PUBLIC_SUPABASE_URL=...
 *   set SUPABASE_SERVICE_ROLE_KEY=...
 *   npx tsx src/scripts/import-dataset-csv.ts
 *   npx tsx src/scripts/import-dataset-csv.ts --limit=10000
 *   npx tsx src/scripts/import-dataset-csv.ts --dry-run
 *
 * Paths: default `../text_classifier/data/data.csv` from cwd, or DATA_CSV_PATH / first CLI arg.
 */

import { createClient } from '@supabase/supabase-js'
import { parse } from 'csv-parse/sync'
import { readFileSync, existsSync } from 'fs'
import { resolve } from 'path'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

const PLACEHOLDER = {
  customerId: 'c0ffee00-0000-4000-8000-000000000001',
  productByCategory: {
    Product: 'c0ffee00-0000-4000-8000-000000000011',
    Packaging: 'c0ffee00-0000-4000-8000-000000000012',
    Trade: 'c0ffee00-0000-4000-8000-000000000013',
  } as Record<string, string>,
}

function parseArgs() {
  const args = process.argv.slice(2)
  let limit: number | null = null
  let dryRun = false
  let filePath: string | null = null
  for (const a of args) {
    if (a.startsWith('--limit=')) limit = parseInt(a.slice('--limit='.length), 10)
    else if (a === '--dry-run') dryRun = true
    else if (!a.startsWith('--')) filePath = a
  }
  return { limit, dryRun, filePath }
}

function resolveCsvPath(explicit: string | null): string {
  if (explicit) return resolve(explicit)
  if (process.env.DATA_CSV_PATH) return resolve(process.env.DATA_CSV_PATH)
  return resolve(process.cwd(), '..', 'text_classifier', 'data', 'data.csv')
}

async function ensurePlaceholders(admin: ReturnType<typeof createClient>) {
  const { error: cErr } = await admin.from('customers').upsert(
    {
      id: PLACEHOLDER.customerId,
      name: 'Dataset import (placeholder)',
      email: 'dataset-import@local.invalid',
      phone: null,
    },
    { onConflict: 'id' }
  )
  if (cErr) throw cErr

  const products = [
    {
      id: PLACEHOLDER.productByCategory.Product,
      name: 'Imported — Product category',
      sku: 'CSV-IMPORT-PRODUCT',
      category: 'supplement',
    },
    {
      id: PLACEHOLDER.productByCategory.Packaging,
      name: 'Imported — Packaging category',
      sku: 'CSV-IMPORT-PACKAGING',
      category: 'supplement',
    },
    {
      id: PLACEHOLDER.productByCategory.Trade,
      name: 'Imported — Trade category',
      sku: 'CSV-IMPORT-TRADE',
      category: 'supplement',
    },
  ]

  for (const p of products) {
    const { error } = await admin.from('products').upsert(p, { onConflict: 'sku' })
    if (error) throw error
  }
}

async function main() {
  const { limit, dryRun, filePath: argPath } = parseArgs()
  const csvPath = resolveCsvPath(argPath)

  if (!supabaseUrl || !serviceKey) {
    console.error('Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY')
    process.exit(1)
  }

  if (!existsSync(csvPath)) {
    console.error('CSV not found:', csvPath)
    process.exit(1)
  }

  console.log('Reading:', csvPath)
  const rawText = readFileSync(csvPath, 'utf-8')

  const table = parse(rawText, {
    skip_empty_lines: true,
    relax_column_count: true,
    trim: true,
  }) as string[][]

  if (table.length < 2) {
    console.error('No data rows')
    process.exit(1)
  }

  const admin = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  })

  if (!dryRun) {
    console.log('Ensuring placeholder customer + products…')
    await ensurePlaceholders(admin)
  }

  const dataRows = table.slice(1)
  const maxRows = limit && limit > 0 ? limit : dataRows.length
  const batchSize = 400
  let inserted = 0
  let skipped = 0
  let rowIndex = 0

  while (rowIndex < dataRows.length && inserted < maxRows) {
    const batch: Record<string, unknown>[] = []

    while (
      batch.length < batchSize &&
      rowIndex < dataRows.length &&
      inserted < maxRows
    ) {
      const cols = dataRows[rowIndex].map((c) => (c ?? '').trim())
      rowIndex++

      if (cols.length < 6) {
        skipped++
        continue
      }

      const [, text, category, priority, sentiment, resolutionTime] = cols
      const cat = category as 'Product' | 'Packaging' | 'Trade'
      const pri = priority as 'High' | 'Medium' | 'Low'

      if (!text || !['Product', 'Packaging', 'Trade'].includes(cat)) {
        skipped++
        continue
      }
      if (!['High', 'Medium', 'Low'].includes(pri)) {
        skipped++
        continue
      }

      const sentimentNum = parseFloat(sentiment)
      if (Number.isNaN(sentimentNum)) {
        skipped++
        continue
      }

      const resMin = parseInt(resolutionTime, 10) || 0
      const sourceId = parseInt(cols[0] || '0', 10)

      batch.push({
        complaint_text: text,
        category: cat,
        priority: pri,
        sentiment_score: sentimentNum,
        source: 'email',
        status: 'new',
        customer_id: PLACEHOLDER.customerId,
        product_id: PLACEHOLDER.productByCategory[cat],
        escalation_required: pri === 'High',
        resolution_steps: {
          source_complaint_id: sourceId || null,
          csv_resolution_minutes: resMin,
        },
      })
      inserted++
    }

    if (batch.length === 0) break

    if (dryRun) {
      console.log(`[dry-run] would insert batch of ${batch.length} (running total ${inserted})`)
      continue
    }

    const { error } = await admin.from('complaints').insert(batch)
    if (error) {
      console.error('Insert error:', error)
      process.exit(1)
    }
    console.log(`Inserted ${inserted} / ${maxRows} …`)
  }

  console.log('Done. Total inserted:', inserted, 'Skipped:', skipped, dryRun ? '(dry-run)' : '')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
