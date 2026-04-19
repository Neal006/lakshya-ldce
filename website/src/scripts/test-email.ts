/**
 * Test script for email functionality
 * Run with: ts-node src/scripts/test-email.ts
 */

import { sendEmail, sendComplaintAcknowledgment } from '../lib/email-client'

async function testEmailSending() {
  console.log('🧪 Testing Email Functionality\n')
  console.log('=' .repeat(50))

  // Test 1: Simple email
  console.log('\n📧 Test 1: Sending simple test email...')
  const testResult = await sendEmail({
    to: 'trhatwork@gmail.com',
    toName: 'Test User',
    subject: 'Test Email from SOLV.ai',
    htmlContent: `
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h1 style="color: #667eea;">Test Email</h1>
          <p>This is a test email from SOLV.ai</p>
          <p>If you received this, the email system is working!</p>
        </body>
      </html>
    `,
  })

  if (testResult.success) {
    console.log('✅ Test email sent successfully!')
    console.log(`   Message ID: ${testResult.messageId}`)
  } else {
    console.log('❌ Test email failed:')
    console.log(`   Error: ${testResult.error}`)
  }

  // Test 2: Complaint acknowledgment email
  console.log('\n📧 Test 2: Sending complaint acknowledgment email...')
  const complaintResult = await sendComplaintAcknowledgment({
    customerEmail: 'customer@example.com',
    customerName: 'John Doe',
    complaintId: '12345-abc-67890',
    complaintText: 'The product arrived damaged and the packaging was torn. Very disappointed with the quality.',
    category: 'Product',
    priority: 'High',
    immediateAction: 'We have flagged your complaint as high priority and will arrange a replacement immediately.',
    resolutionSteps: [
      'Quality assurance team will review the damaged product photos',
      'Replacement product will be shipped within 24 hours',
      'Return label will be emailed for the damaged item',
      'Full refund will be processed if replacement is not satisfactory',
    ],
    assignedTeam: 'Quality Assurance & Logistics',
    estimatedResolutionTime: '24-48 hours',
  })

  if (complaintResult.success) {
    console.log('✅ Complaint acknowledgment email sent successfully!')
    console.log(`   Message ID: ${complaintResult.messageId}`)
  } else {
    console.log('❌ Complaint acknowledgment email failed:')
    console.log(`   Error: ${complaintResult.error}`)
  }

  console.log('\n' + '='.repeat(50))
  console.log('\n📊 Test Summary:')
  console.log(`   Test 1 (Simple Email): ${testResult.success ? '✅ PASS' : '❌ FAIL'}`)
  console.log(`   Test 2 (Complaint Ack): ${complaintResult.success ? '✅ PASS' : '❌ FAIL'}`)
  
  if (testResult.success && complaintResult.success) {
    console.log('\n🎉 All tests passed! Email system is ready.')
    process.exit(0)
  } else {
    console.log('\n⚠️  Some tests failed. Check errors above.')
    process.exit(1)
  }
}

// Run tests
testEmailSending().catch(error => {
  console.error('💥 Unexpected error:', error)
  process.exit(1)
})