/**
 * Simple Email Test - Direct Brevo API Call
 * Run with: node test-simple-email.js
 */

const fs = require('fs');
const path = require('path');

// Read .env file manually
function loadEnv() {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        let value = match[2].trim();
        // Remove quotes if present
        if ((value.startsWith('"') && value.endsWith('"')) || 
            (value.startsWith("'") && value.endsWith("'"))) {
          value = value.slice(1, -1);
        }
        process.env[key] = value;
      }
    });
  }
}

// Load environment variables
loadEnv();

const BREVO_API_KEY = process.env.BREVO_API_KEY;
const SENDER_EMAIL = 'slbrkr956@gmail.com';
const SENDER_NAME = 'SOLV.ai Support';

async function sendTestEmail() {
  console.log('📧 Testing Brevo Email API...\n');
  
  if (!BREVO_API_KEY) {
    console.error('❌ ERROR: BREVO_API_KEY not found in environment');
    console.log('   Please check your .env file');
    process.exit(1);
  }
  
  console.log('✅ API Key found');
  console.log(`   Key: ${BREVO_API_KEY.substring(0, 30)}...`);
  console.log(`   Sender: ${SENDER_EMAIL}\n`);

  const emailData = {
    sender: {
      email: SENDER_EMAIL,
      name: SENDER_NAME,
    },
    to: [
      {
        email: 'slbrkr956@gmail.com',  // Sending to same email for testing
        name: 'Test User',
      },
    ],
    subject: 'Test Email from SOLV.ai - ' + new Date().toLocaleTimeString(),
    htmlContent: `
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
          <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
            <h1 style="color: #667eea;">✅ Test Email Successful!</h1>
            <p>Hello,</p>
            <p>This is a test email from your SOLV.ai complaint management system.</p>
            <p>If you're seeing this, the email integration is working correctly!</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
              Sent at: ${new Date().toLocaleString()}<br>
              From: ${SENDER_EMAIL}
            </p>
          </div>
        </body>
      </html>
    `,
    textContent: 'Test email from SOLV.ai. If you received this, the email system is working!',
  };

  try {
    console.log('📤 Sending email to Brevo API...');
    console.log('   URL: https://api.brevo.com/v3/smtp/email\n');
    
    const response = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json',
      },
      body: JSON.stringify(emailData),
    });

    const responseData = await response.json();

    console.log(`📥 Response Status: ${response.status}`);
    
    if (response.ok) {
      console.log('\n✅ SUCCESS! Email sent successfully!');
      console.log(`   Message ID: ${responseData.messageId}`);
      console.log(`   To: ${emailData.to[0].email}`);
      console.log(`   Subject: ${emailData.subject}`);
      console.log('\n📧 Check your inbox (and spam folder) at slbrkr956@gmail.com');
      console.log('   The email should arrive within a few minutes.\n');
    } else {
      console.log('\n❌ FAILED to send email');
      console.log(`   Status Code: ${response.status}`);
      console.log(`   Response: ${JSON.stringify(responseData, null, 2)}`);
      
      if (response.status === 401) {
        console.log('\n⚠️  Authentication Error:');
        console.log('   Your BREVO_API_KEY may be invalid or expired.');
        console.log('   Please check your Brevo dashboard and get a new API key.');
      }
      
      if (response.status === 400) {
        console.log('\n⚠️  Bad Request:');
        console.log('   The email data may be malformed.');
      }
    }
  } catch (error) {
    console.error('\n💥 Network Error:', error.message);
    console.log('   Make sure you have an internet connection.');
  }
}

sendTestEmail();