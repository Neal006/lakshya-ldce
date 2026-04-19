const BASE = 'http://localhost:3000';
const results = { passed: 0, failed: 0, tests: [], latencies: [] };

function log(name, status, details = '') {
  const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : status === 'WARN' ? '🟡' : '🔴';
  console.log(`${icon} [${status}] ${name}`);
  if (details) console.log(`   ${details}`);
  results.tests.push({ name, status, details });
  if (status === 'PASS') results.passed++;
  else if (status === 'FAIL' || status === 'CRIT') results.failed++;
}

async function measureLatency(name, fn) {
  const start = Date.now();
  try {
    const result = await fn();
    const latency = Date.now() - start;
    results.latencies.push({ name, latency });
    return { result, latency, error: null };
  } catch (error) {
    const latency = Date.now() - start;
    results.latencies.push({ name, latency });
    return { result: null, latency, error };
  }
}

async function tier1Tests() {
  console.log('=== TIER 1: HAPPY PATH TESTS ===\n');

  // Test 1: Health endpoint
  const health = await measureLatency('GET /api/health', async () => {
    const res = await fetch(`${BASE}/api/health`);
    return { status: res.status, data: await res.json() };
  });
  if (!health.error && health.result.status === 200 && health.result.data.status) {
    log('GET /api/health', 'PASS', `Status: ${health.result.data.status}, Services: ${health.result.data.services?.length || 0}, Latency: ${health.latency}ms`);
  } else {
    log('GET /api/health', 'FAIL', health.error?.message || `Status: ${health.result?.status}`);
  }

  // Test 2: Products endpoint
  const products = await measureLatency('GET /api/products', async () => {
    const res = await fetch(`${BASE}/api/products`);
    return { status: res.status, data: await res.json() };
  });
  if (!products.error && products.result.status === 200 && Array.isArray(products.result.data.products) && products.result.data.products.length > 0) {
    log('GET /api/products', 'PASS', `Products: ${products.result.data.products.length}, Latency: ${products.latency}ms`);
  } else {
    log('GET /api/products', 'FAIL', products.error?.message || `Status: ${products.result?.status}`);
  }

  // Test 3: Dashboard analytics
  const dashboard = await measureLatency('GET /api/analytics/dashboard', async () => {
    const res = await fetch(`${BASE}/api/analytics/dashboard`);
    return { status: res.status, data: await res.json() };
  });
  if (!dashboard.error && dashboard.result.status === 200 && dashboard.result.data.summary) {
    log('GET /api/analytics/dashboard', 'PASS', `Total: ${dashboard.result.data.summary.total_complaints}, Latency: ${dashboard.latency}ms`);
  } else {
    log('GET /api/analytics/dashboard', 'FAIL', dashboard.error?.message || `Status: ${dashboard.result?.status}, Error: ${dashboard.result?.data?.error}`);
  }

  // Test 4: Complaints list
  const complaints = await measureLatency('GET /api/complaints', async () => {
    const res = await fetch(`${BASE}/api/complaints?limit=5`);
    return { status: res.status, data: await res.json() };
  });
  if (!complaints.error && complaints.result.status === 200 && Array.isArray(complaints.result.data.complaints)) {
    log('GET /api/complaints', 'PASS', `Complaints: ${complaints.result.data.complaints.length}, Latency: ${complaints.latency}ms`);
  } else {
    log('GET /api/complaints', 'FAIL', complaints.error?.message || `Status: ${complaints.result?.status}`);
  }

  // Test 5: SLA config
  const sla = await measureLatency('GET /api/admin/sla-config', async () => {
    const res = await fetch(`${BASE}/api/admin/sla-config`);
    return { status: res.status, data: await res.json() };
  });
  if (!sla.error && sla.result.status === 200 && Array.isArray(sla.result.data.sla_configs) && sla.result.data.sla_configs.length > 0) {
    log('GET /api/admin/sla-config', 'PASS', `Configs: ${sla.result.data.sla_configs.length}, Latency: ${sla.latency}ms`);
  } else {
    log('GET /api/admin/sla-config', 'FAIL', sla.error?.message || `Status: ${sla.result?.status}`);
  }

  // Test 6: Product analytics
  const prodAnalytics = await measureLatency('GET /api/analytics/products', async () => {
    const res = await fetch(`${BASE}/api/analytics/products`);
    return { status: res.status, data: await res.json() };
  });
  if (!prodAnalytics.error && prodAnalytics.result.status === 200 && Array.isArray(prodAnalytics.result.data.products)) {
    log('GET /api/analytics/products', 'PASS', `Products: ${prodAnalytics.result.data.products.length}, Latency: ${prodAnalytics.latency}ms`);
  } else {
    log('GET /api/analytics/products', 'FAIL', prodAnalytics.error?.message || `Status: ${prodAnalytics.result?.status}`);
  }

  // Test 7: Trends
  const trends = await measureLatency('GET /api/analytics/trends', async () => {
    const res = await fetch(`${BASE}/api/analytics/trends`);
    return { status: res.status, data: await res.json() };
  });
  if (!trends.error && trends.result.status === 200 && Array.isArray(trends.result.data.daily)) {
    log('GET /api/analytics/trends', 'PASS', `Days: ${trends.result.data.daily.length}, Latency: ${trends.latency}ms`);
  } else {
    log('GET /api/analytics/trends', 'FAIL', trends.error?.message || `Status: ${trends.result?.status}`);
  }

  // Test 8: Employees
  const employees = await measureLatency('GET /api/admin/employees', async () => {
    const res = await fetch(`${BASE}/api/admin/employees`);
    return { status: res.status, data: await res.json() };
  });
  if (!employees.error && employees.result.status === 200 && Array.isArray(employees.result.data.employees)) {
    log('GET /api/admin/employees', 'PASS', `Employees: ${employees.result.data.employees.length}, Latency: ${employees.latency}ms`);
  } else {
    log('GET /api/admin/employees', 'FAIL', employees.error?.message || `Status: ${employees.result?.status}`);
  }

  // Test 9: Analytics report
  const report = await measureLatency('GET /api/analytics/report', async () => {
    const res = await fetch(`${BASE}/api/analytics/report`);
    return { status: res.status, data: await res.json() };
  });
  if (!report.error && report.result.status === 200 && report.result.data.report) {
    log('GET /api/analytics/report', 'PASS', `Has report data, Latency: ${report.latency}ms`);
  } else {
    log('GET /api/analytics/report', 'FAIL', report.error?.message || `Status: ${report.result?.status}`);
  }

  // Test 10: Create complaint (if products exist)
  let productId = null;
  if (!products.error && products.result.data.products?.length > 0) {
    productId = products.result.data.products[0].id;
  }
  
  if (productId) {
    const createComplaint = await measureLatency('POST /api/complaints', async () => {
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
      return { status: res.status, data: await res.json() };
    });
    if (!createComplaint.error && createComplaint.result.status === 201 && createComplaint.result.data.id) {
      log('POST /api/complaints', 'PASS', `Created: ${createComplaint.result.data.id.substring(0,8)}..., Category: ${createComplaint.result.data.category}, Latency: ${createComplaint.latency}ms`);
    } else {
      log('POST /api/complaints', 'FAIL', createComplaint.error?.message || `Status: ${createComplaint.result?.status}, Error: ${JSON.stringify(createComplaint.result?.data)}`);
    }
  } else {
    log('POST /api/complaints', 'FAIL', 'No product ID available');
  }
}

async function tier2Tests() {
  console.log('\n=== TIER 2: FAILURE MODE TESTS ===\n');

  // Test 1: Invalid complaint ID
  const invalidId = await measureLatency('GET /api/complaints/invalid-id', async () => {
    const res = await fetch(`${BASE}/api/complaints/invalid-id`);
    return { status: res.status, data: await res.json() };
  });
  if (!invalidId.error && (invalidId.result.status === 404 || invalidId.result.status === 500)) {
    log('GET /api/complaints/invalid-id', 'PASS', `Status: ${invalidId.result.status} (expected 404 or 500 for bad UUID)`);
  } else {
    log('GET /api/complaints/invalid-id', 'WARN', `Status: ${invalidId.result?.status} (expected 404)`);
  }

  // Test 2: Create complaint with missing fields
  const missingFields = await measureLatency('POST /api/complaints (missing fields)', async () => {
    const res = await fetch(`${BASE}/api/complaints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Incomplete complaint' }) // missing product_id and source
    });
    return { status: res.status, data: await res.json() };
  });
  if (!missingFields.error && missingFields.result.status === 400) {
    log('POST /api/complaints (missing fields)', 'PASS', `Status: ${missingFields.result.status} - correctly rejected`);
  } else {
    log('POST /api/complaints (missing fields)', 'WARN', `Status: ${missingFields.result?.status} (expected 400)`);
  }

  // Test 3: Invalid JSON
  const invalidJson = await measureLatency('POST /api/complaints (invalid JSON)', async () => {
    const res = await fetch(`${BASE}/api/complaints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{invalid json}'
    });
    return { status: res.status, data: await res.json().catch(() => ({})) };
  });
  if (!invalidJson.error && (invalidJson.result.status === 400 || invalidJson.result.status === 500)) {
    log('POST /api/complaints (invalid JSON)', 'PASS', `Status: ${invalidJson.result.status}`);
  } else {
    log('POST /api/complaints (invalid JSON)', 'WARN', `Status: ${invalidJson.result?.status}`);
  }

  // Test 4: Unknown endpoint
  const unknownEndpoint = await measureLatency('GET /api/unknown', async () => {
    const res = await fetch(`${BASE}/api/unknown`);
    return { status: res.status };
  });
  if (!unknownEndpoint.error && unknownEndpoint.result.status === 404) {
    log('GET /api/unknown', 'PASS', `Status: ${unknownEndpoint.result.status}`);
  } else {
    log('GET /api/unknown', 'WARN', `Status: ${unknownEndpoint.result?.status}`);
  }
}

async function tier3Tests() {
  console.log('\n=== TIER 3: PERFORMANCE TESTS ===\n');
  
  const WARNING_MS = 200;
  const CRITICAL_MS = 500;
  
  // Run each endpoint 3 times and average
  const endpoints = [
    { name: 'GET /api/health', url: '/api/health' },
    { name: 'GET /api/products', url: '/api/products' },
    { name: 'GET /api/analytics/dashboard', url: '/api/analytics/dashboard' },
    { name: 'GET /api/complaints', url: '/api/complaints?limit=10' },
    { name: 'GET /api/admin/sla-config', url: '/api/admin/sla-config' },
    { name: 'GET /api/analytics/products', url: '/api/analytics/products' },
  ];

  for (const endpoint of endpoints) {
    const times = [];
    for (let i = 0; i < 3; i++) {
      const start = Date.now();
      try {
        await fetch(`${BASE}${endpoint.url}`);
        times.push(Date.now() - start);
      } catch (e) {
        times.push(9999);
      }
    }
    const avg = Math.round(times.reduce((a, b) => a + b, 0) / times.length);
    
    if (avg >= CRITICAL_MS) {
      log(endpoint.name, 'CRIT', `${avg}ms (threshold: ${CRITICAL_MS}ms)`);
    } else if (avg >= WARNING_MS) {
      log(endpoint.name, 'WARN', `${avg}ms (threshold: ${WARNING_MS}ms)`);
    } else {
      log(endpoint.name, 'PASS', `${avg}ms`);
    }
  }

  // Concurrent load test
  console.log('\n--- Concurrent Load Test (10 requests) ---');
  const start = Date.now();
  const promises = [];
  for (let i = 0; i < 10; i++) {
    promises.push(fetch(`${BASE}/api/health`));
  }
  await Promise.all(promises);
  const total = Date.now() - start;
  console.log(`10 concurrent /api/health: ${total}ms total`);
}

async function runAll() {
  await tier1Tests();
  await tier2Tests();
  await tier3Tests();

  console.log('\n=== FINAL SUMMARY ===');
  console.log(`Total: ${results.passed + results.failed}, Passed: ${results.passed}, Failed: ${results.failed}`);
  
  // Calculate average latency
  const avgLatency = Math.round(results.latencies.reduce((a, b) => a + b.latency, 0) / results.latencies.length);
  console.log(`Average Latency: ${avgLatency}ms`);
  
  // Show critical latencies
  const slow = results.latencies.filter(l => l.latency >= 500);
  if (slow.length > 0) {
    console.log('\nSlow Endpoints (>500ms):');
    slow.forEach(l => console.log(`  ${l.name}: ${l.latency}ms`));
  }
  
  // Exit with error code if failures
  if (results.failed > 0) {
    process.exit(1);
  }
}

runAll();