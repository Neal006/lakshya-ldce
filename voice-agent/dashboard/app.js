const API_BASE = window.location.origin.replace(/:\d+$/, ':8000');
let authToken = localStorage.getItem('lakshya_token');
let currentUser = JSON.parse(localStorage.getItem('lakshya_user') || 'null');
let currentPage = 'overview';
let currentFilters = { status: '', category: '', priority: '', page: 1 };

document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        showDashboard();
    } else {
        showLogin();
    }
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('refresh-btn').addEventListener('click', () => loadComplaints());
    document.getElementById('modal-close').addEventListener('click', () => {
        document.getElementById('complaint-modal').style.display = 'none';
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchPage(item.dataset.page);
        });
    });
    document.getElementById('filter-status').addEventListener('change', applyFilters);
    document.getElementById('filter-category').addEventListener('change', applyFilters);
    document.getElementById('filter-priority').addEventListener('change', applyFilters);
});

function showLogin() {
    document.getElementById('login-screen').style.display = '';
    document.getElementById('dashboard-screen').style.display = 'none';
}

function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard-screen').style.display = '';
    document.getElementById('user-name').textContent = currentUser ? currentUser.name : 'User';
    loadDashboard();
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errEl = document.getElementById('login-error');
    errEl.style.display = 'none';
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.error?.message || data.detail || 'Login failed';
            errEl.style.display = '';
            return;
        }
        authToken = data.data.access_token;
        currentUser = data.data.user;
        localStorage.setItem('lakshya_token', authToken);
        localStorage.setItem('lakshya_user', JSON.stringify(currentUser));
        showDashboard();
    } catch (err) {
        errEl.textContent = 'Network error. Is the backend running?';
        errEl.style.display = '';
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('lakshya_token');
    localStorage.removeItem('lakshya_user');
    showLogin();
}

async function apiCall(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json', ...options.headers }
    });
    if (res.status === 401) { handleLogout(); return null; }
    return res.json();
}

function switchPage(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    if (page === 'overview') loadDashboard();
    if (page === 'complaints') loadComplaints();
    if (page === 'analytics') loadAnalytics();
}

async function loadDashboard() {
    const data = await apiCall('/analytics/dashboard');
    if (!data || !data.data) return;
    const s = data.data.summary || data.data;
    document.getElementById('kpi-total').textContent = s.total_complaints ?? '--';
    document.getElementById('kpi-open').textContent = s.open_complaints ?? '--';
    document.getElementById('kpi-resolved').textContent = s.resolved_complaints ?? '--';
    document.getElementById('kpi-escalated').textContent = s.escalated_complaints ?? '--';
    document.getElementById('kpi-sla').textContent = s.sla_compliance_rate != null ? s.sla_compliance_rate + '%' : '--';
    document.getElementById('kpi-avg-time').textContent = s.avg_resolution_time_hours != null ? s.avg_resolution_time_hours : '--';
    const recentData = await apiCall('/complaints?limit=5');
    if (recentData && recentData.data) {
        const complaints = recentData.data.complaints || [];
        const container = document.getElementById('recent-complaints');
        container.innerHTML = complaints.length === 0 ? '<p style="color: var(--text-muted)">No complaints yet</p>' :
            complaints.map(c => `<div class="complaint-item" onclick="showComplaint('${c.id}')">
                <div><span class="complaint-id">${c.id?.substring(0,8) || ''}</span>
                <span class="badge badge-${c.priority || ''}">${c.priority || ''}</span>
                <span class="badge badge-${c.status || ''}">${c.status || ''}</span>
                <span class="badge badge-${c.category || ''}">${c.category || ''}</span></div>
                <div class="complaint-text">${(c.raw_text || '').substring(0, 80)}${(c.raw_text || '').length > 80 ? '...' : ''}</div>
            </div>`).join('');
    }
}

async function loadComplaints() {
    const params = new URLSearchParams();
    if (currentFilters.status) params.set('status', currentFilters.status);
    if (currentFilters.category) params.set('category', currentFilters.category);
    if (currentFilters.priority) params.set('priority', currentFilters.priority);
    params.set('page', currentFilters.page);
    params.set('limit', '20');
    const data = await apiCall(`/complaints?${params.toString()}`);
    if (!data || !data.data) return;
    const complaints = data.data.complaints || [];
    const pagination = data.data.pagination || {};
    const container = document.getElementById('complaints-table');
    container.innerHTML = `<table><thead><tr>
        <th>ID</th><th>Customer</th><th>Text</th><th>Category</th><th>Priority</th><th>Status</th><th>SLA</th><th>Created</th>
    </tr></thead><tbody>${complaints.map(c => `<tr onclick="showComplaint('${c.id}')" style="cursor:pointer">
        <td>${(c.id || '').substring(0,8)}</td>
        <td>${c.customer?.name || c.customer || '--'}</td>
        <td>${(c.raw_text || '').substring(0, 50)}${(c.raw_text || '').length > 50 ? '...' : ''}</td>
        <td><span class="badge badge-${c.category || ''}">${c.category || '--'}</span></td>
        <td><span class="badge badge-${c.priority || ''}">${c.priority || '--'}</span></td>
        <td><span class="badge badge-${c.status || ''}">${c.status || '--'}</span></td>
        <td class="${c.sla_breached ? 'sla-breach' : 'sla-ok'}">${c.sla_breached ? 'BREACHED' : 'OK'}</td>
        <td>${c.created_at ? new Date(c.created_at).toLocaleDateString() : '--'}</td>
    </tr>`).join('')}</tbody></table>`;
    const pContainer = document.getElementById('pagination');
    const tp = pagination.total_pages || 1;
    let pHtml = '';
    for (let i = 1; i <= tp; i++) {
        pHtml += `<button class="${i === currentFilters.page ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    pContainer.innerHTML = pHtml;
}

function applyFilters() {
    currentFilters.status = document.getElementById('filter-status').value;
    currentFilters.category = document.getElementById('filter-category').value;
    currentFilters.priority = document.getElementById('filter-priority').value;
    currentFilters.page = 1;
    loadComplaints();
}

function goToPage(p) {
    currentFilters.page = p;
    loadComplaints();
}

async function showComplaint(id) {
    const data = await apiCall(`/complaints/${id}`);
    if (!data || !data.data || !data.data.complaint) return;
    const c = data.data.complaint;
    const steps = Array.isArray(c.resolution_steps) ? c.resolution_steps : [];
    const timeline = Array.isArray(c.timeline) ? c.timeline : [];
    document.getElementById('modal-title').textContent = `Complaint ${(c.id || '').substring(0, 8)}`;
    document.getElementById('modal-body').innerHTML = `
        <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value"><span class="badge badge-${c.status}">${c.status}</span></span></div>
        <div class="detail-row"><span class="detail-label">Category</span><span class="detail-value"><span class="badge badge-${c.category}">${c.category}</span></span></div>
        <div class="detail-row"><span class="detail-label">Priority</span><span class="detail-value"><span class="badge badge-${c.priority}">${c.priority}</span></span></div>
        <div class="detail-row"><span class="detail-label">Sentiment</span><span class="detail-value">${c.sentiment_score != null ? c.sentiment_score.toFixed(2) : '--'}</span></div>
        <div class="detail-row"><span class="detail-label">Submitted Via</span><span class="detail-value">${c.submitted_via}</span></div>
        <div class="detail-row"><span class="detail-label">SLA</span><span class="detail-value ${c.sla_breached ? 'sla-breach' : 'sla-ok'}">${c.sla_breached ? 'BREACHED' : 'On Track'}</span></div>
        <div class="detail-row"><span class="detail-label">Created</span><span class="detail-value">${c.created_at ? new Date(c.created_at).toLocaleString() : '--'}</span></div>
        ${c.resolved_at ? `<div class="detail-row"><span class="detail-label">Resolved</span><span class="detail-value">${new Date(c.resolved_at).toLocaleString()}</span></div>` : ''}
        <div style="margin-top:16px"><strong>Complaint Text:</strong></div>
        <p style="margin-top:8px;color:var(--text-muted)">${c.raw_text || '--'}</p>
        <div style="margin-top:16px"><strong>Resolution Steps:</strong></div>
        <ul class="steps-list">${steps.length > 0 ? steps.map(s => `<li>${typeof s === 'string' ? s : JSON.stringify(s)}</li>`).join('') : '<li>No steps yet</li>'}</ul>
        ${timeline.length > 0 ? `<div style="margin-top:16px"><strong>Timeline:</strong></div>
        <ul class="steps-list">${timeline.map(t => `<li>${new Date(t.created_at).toLocaleString()} - ${t.action} ${t.notes ? '(' + t.notes + ')' : ''}</li>`).join('')}</ul>` : ''}
    `;
    document.getElementById('complaint-modal').style.display = '';
}

async function loadAnalytics() {
    const data = await apiCall('/analytics/dashboard');
    if (!data || !data.data) return;
    renderBarChart('chart-category', data.data.by_category || [], 'category', 'count');
    renderBarChart('chart-priority', data.data.by_priority || [], 'priority', 'count');
    renderDonutChart('chart-status', data.data.by_status || [], 'status', 'count');
}

function renderBarChart(containerId, items, labelKey, valueKey) {
    const container = document.getElementById(containerId);
    if (typeof Chart === 'undefined' || !items.length) {
        container.innerHTML = `<div style="color:var(--text-muted)">${items.length ? 'Chart.js not loaded' : 'No data'}</div>`;
        if (typeof Chart !== 'undefined' && items.length) {
            new Chart(container, {
                type: 'bar',
                data: {
                    labels: items.map(i => i[labelKey]),
                    datasets: [{ label: 'Count', data: items.map(i => i[valueKey]), backgroundColor: '#FF6B35', borderRadius: 4 }]
                },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
            });
        } else {
            const maxVal = Math.max(...items.map(i => i[valueKey]));
            container.innerHTML = items.map(i => `<div style="display:flex;align-items:center;gap:8px;margin:4px 0">
                <span style="min-width:80px;font-size:12px;color:var(--text-muted)">${i[labelKey]}</span>
                <div style="height:16px;background:var(--primary);border-radius:3px;width:${(i[valueKey]/maxVal)*100}%"></div>
                <span style="font-size:13px">${i[valueKey]}</span>
            </div>`).join('');
        }
    } else {
        new Chart(container, {
            type: 'bar',
            data: {
                labels: items.map(i => i[labelKey]),
                datasets: [{ label: 'Count', data: items.map(i => i[valueKey]), backgroundColor: '#FF6B35', borderRadius: 4 }]
            },
            options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });
    }
}

function renderDonutChart(containerId, items, labelKey, valueKey) {
    const colors = ['#3B82F6', '#22C55E', '#F59E0B', '#EF4444'];
    const container = document.getElementById(containerId);
    if (typeof Chart === 'undefined') {
        const total = items.reduce((s, i) => s + i[valueKey], 0);
        container.innerHTML = items.map(i => `<div style="margin:4px 0;font-size:13px"><span style="color:var(--primary)">${i[labelKey]}</span>: ${i[valueKey]} (${total > 0 ? Math.round(i[valueKey]/total*100) : 0}%)</div>`).join('');
        return;
    }
    new Chart(container, {
        type: 'doughnut',
        data: {
            labels: items.map(i => i[labelKey]),
            datasets: [{ data: items.map(i => i[valueKey]), backgroundColor: colors.slice(0, items.length) }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
}