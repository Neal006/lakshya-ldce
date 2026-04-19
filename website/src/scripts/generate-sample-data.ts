import { createClient } from '@supabase/supabase-js'
import { faker } from '@faker-js/faker'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('❌ Missing Supabase environment variables')
  console.error('Please set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseServiceKey)

// Complaint categories and their mappings
const complaintCategories = ['Product', 'Packaging', 'Trade']
const priorities = ['Low', 'Medium', 'High']
const sources = ['email', 'call', 'walkin']
const statuses = ['new', 'assigned', 'in_progress', 'resolved', 'escalated']
const teams = [
  'Customer Support', 'Technical Support', 'Logistics', 'Sales', 'Quality Assurance'
]

// Sentiment scores based on priority
function getSentimentScore(priority: string): number {
  switch (priority) {
    case 'High': return faker.number.float({ min: -0.8, max: -0.3 })
    case 'Medium': return faker.number.float({ min: -0.3, max: 0.3 })
    case 'Low': return faker.number.float({ min: 0.3, max: 0.8 })
    default: return 0
  }
}

// Generate a single complaint
function generateComplaint(productId: string) {
  const priority = faker.helpers.arrayElement(priorities)
  const category = faker.helpers.arrayElement(complaintCategories)
  
  return {
    complaint_text: faker.lorem.sentences(faker.number.int({ min: 1, max: 5 })),
    category,
    priority,
    sentiment_score: getSentimentScore(priority),
    source: faker.helpers.arrayElement(sources),
    product_id: productId,
    status: faker.helpers.arrayElement(statuses),
    customer_response: faker.lorem.sentence(),
    immediate_action: faker.lorem.sentence(),
    escalation_required: faker.datatype.boolean(),
    assigned_team: faker.helpers.arrayElement(teams),
    customer_name: faker.person.fullName(),
    customer_email: faker.internet.email(),
    customer_phone: faker.phone.number(),
    created_at: faker.date.between({
      from: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), // 90 days ago
      to: new Date()
    }).toISOString()
  }
}

// Batch insert complaints
async function insertComplaintsBatch(complaints: any[], batchSize: number = 1000) {
  for (let i = 0; i < complaints.length; i += batchSize) {
    const batch = complaints.slice(i, i + batchSize)
    
    const { error } = await supabase
      .from('complaints')
      .insert(batch)
      
    if (error) {
      console.error(`❌ Error inserting batch ${Math.floor(i/batchSize) + 1}:`, error.message)
      return false
    }
    
    console.log(`✅ Inserted batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(complaints.length/batchSize)}`)
  }
  
  return true
}

// Main function to generate and insert complaints
async function generateSampleData(count: number = 50000) {
  console.log(`🚀 Starting generation of ${count.toLocaleString()} sample complaints...`)
  
  try {
    // Get existing products from database
    console.log('📥 Fetching product IDs...')
    const { data: productData, error: productError } = await supabase
      .from('products')
      .select('id')
      
    if (productError) {
      console.error('❌ Error fetching products:', productError.message)
      return
    }
    
    if (!productData || productData.length === 0) {
      console.error('❌ No products found in database. Please run the schema script first.')
      return
    }
    
    const productIds = productData.map(p => p.id)
    console.log(`✅ Found ${productIds.length} products`)
    
    // Generate complaints in batches to avoid memory issues
    const batchSize = 5000
    let totalInserted = 0
    
    for (let batchNum = 0; batchNum < Math.ceil(count / batchSize); batchNum++) {
      const currentBatchSize = Math.min(batchSize, count - totalInserted)
      const complaints = []
      
      console.log(`🔄 Generating batch ${batchNum + 1} with ${currentBatchSize} complaints...`)
      
      for (let i = 0; i < currentBatchSize; i++) {
        const productId = faker.helpers.arrayElement(productIds)
        complaints.push(generateComplaint(productId))
      }
      
      console.log(`💾 Inserting batch ${batchNum + 1}...`)
      const success = await insertComplaintsBatch(complaints)
      
      if (!success) {
        console.error(`❌ Failed to insert batch ${batchNum + 1}`)
        return
      }
      
      totalInserted += currentBatchSize
      console.log(`📊 Progress: ${totalInserted}/${count} complaints inserted`)
    }
    
    console.log(`🎉 Successfully inserted ${totalInserted.toLocaleString()} sample complaints!`)
    
  } catch (error) {
    console.error('❌ Error generating sample data:', error)
  }
}

// Parse command line arguments
const args = process.argv.slice(2)
const count = args.length > 0 ? parseInt(args[0]) : 50000

if (isNaN(count) || count <= 0) {
  console.error('❌ Please provide a valid number of complaints to generate')
  process.exit(1)
}

// Run the script
if (require.main === module) {
  generateSampleData(count)
}

export default generateSampleData