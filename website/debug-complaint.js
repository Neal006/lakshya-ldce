async function debug() {
  const BASE = 'http://localhost:3000';
  
  // Get a product ID first
  const products = await fetch(`${BASE}/api/products`).then(r => r.json());
  const productId = products.products[0]?.id;
  console.log('Product ID:', productId);
  
  // Try to create a complaint
  const res = await fetch(`${BASE}/api/complaints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: 'Test complaint from verification suite',
      source: 'email',
      product_id: productId,
      customer_name: 'Test User',
      customer_email: 'test@example.com'
    })
  });
  
  console.log('Status:', res.status);
  const data = await res.json();
  console.log('Response:', JSON.stringify(data, null, 2));
}

debug();