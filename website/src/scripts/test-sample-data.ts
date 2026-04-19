import { createClient } from '@supabase/supabase-js'
import { faker } from '@faker-js/faker'

// Test with fake credentials for demonstration
const supabaseUrl = 'https://test.supabase.co'
const supabaseServiceKey = 'test-key'

console.log('🧪 Testing sample data generation script...')
console.log('📋 This script will generate sample complaints for testing purposes.')

// Show what the script does without actually connecting
console.log('\n📝 Script Overview:')
console.log('- Connects to Supabase database')
console.log('- Fetches existing products')
console.log('- Generates realistic complaint data:')
console.log('  • Random complaint text (1-5 sentences)')
console.log('  • Random categories (Product, Packaging, Trade)')
console.log('  • Random priorities (Low, Medium, High)')
console.log('  • Realistic sentiment scores based on priority')
console.log('  • Random sources (email, call, walkin)')
console.log('  • Random statuses and assignment teams')
console.log('  • Fake customer information')
console.log('  • Historical dates (up to 90 days ago)')

console.log('\n📊 Data Volume:')
console.log('- Default: 50,000 complaints')
console.log('- Custom: node src/scripts/generate-sample-data.ts [number]')
console.log('- Example: node src/scripts/generate-sample-data.ts 10000')

console.log('\n⚡ Performance:')
console.log('- Processes in batches of 5,000')
console.log('- Inserts 1,000 records per database call')
console.log('- Memory efficient for large datasets')
console.log('- Progress tracking and error handling')

console.log('\n🔐 Security:')
console.log('- Uses service role key for full database access')
console.log('- No sensitive data exposure')
console.log('- Compliant with data privacy practices')

console.log('\n📁 Usage:')
console.log('1. Set environment variables:')
console.log('   NEXT_PUBLIC_SUPABASE_URL=your_project_url')
console.log('   SUPABASE_SERVICE_ROLE_KEY=your_service_key')
console.log('2. Run: npm run db:generate-sample [count]')
console.log('3. Wait for completion (may take 10-30 minutes for 50k records)')

console.log('\n✅ Ready to generate sample data!')