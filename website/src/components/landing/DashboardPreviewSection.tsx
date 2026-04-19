'use client';

import { LayoutDashboard, ClipboardCheck, Headphones, BarChart3, Users, Shield } from 'lucide-react';

const dashboards = [
  {
    icon: LayoutDashboard,
    title: 'Admin Dashboard',
    description: 'Complete oversight with employee management, SLA configuration, and system analytics.',
    features: ['Employee Management', 'SLA Config', 'System Analytics', 'Role Control'],
    colors: ['#FF6B35', '#E55A2B'],
  },
  {
    icon: ClipboardCheck,
    title: 'QA Dashboard',
    description: 'Quality assurance tools with complaint review, classification override, and trend analysis.',
    features: ['Review Queue', 'Classification', 'Trend Analysis', 'Reports'],
    colors: ['#3B82F6', '#1E40AF'],
  },
  {
    icon: Headphones,
    title: 'Call Attender',
    description: 'Streamlined interface for handling complaints with AI suggestions and quick actions.',
    features: ['Complaint View', 'AI Suggestions', 'Quick Actions', 'Status Update'],
    colors: ['#22C55E', '#166534'],
  },
];

export function DashboardPreviewSection() {
  return (
    <section id="dashboard" className="py-24 px-4 sm:px-6 lg:px-8 relative scroll-mt-24">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="section-badge mb-4 inline-flex">Role-Based Access</span>
          <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-white mb-4">
            Three dashboards, one platform
          </h2>
          <p className="text-lg text-gray-400 max-w-xl mx-auto">
            Tailored experiences for every team member
          </p>
        </div>

        {/* Dashboard cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {dashboards.map((dashboard, i) => (
            <div key={i} className="card-skeuo overflow-hidden group">
              {/* Header */}
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                    style={{ 
                      background: `linear-gradient(145deg, ${dashboard.colors[0]}20 0%, ${dashboard.colors[1]}10 100%)` 
                    }}
                  >
                    <dashboard.icon className="w-6 h-6" style={{ color: dashboard.colors[0] }} />
                  </div>
                  <div>
                    <h3 className="font-valorant text-lg text-white">{dashboard.title}</h3>
                  </div>
                </div>

                {/* Description */}
                <p className="text-gray-400 text-sm mb-6 leading-relaxed">
                  {dashboard.description}
                </p>

                {/* Mini mockup */}
                <div className="bg-black/50 rounded-lg p-4 border border-white/5 mb-4">
                  <div className="flex gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full" style={{ background: dashboard.colors[0] }} />
                    <div className="w-2 h-2 rounded-full bg-white/20" />
                    <div className="w-2 h-2 rounded-full bg-white/20" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <div className="flex-1 h-8 rounded bg-white/5" />
                      <div className="flex-1 h-8 rounded bg-white/5" />
                    </div>
                    <div className="h-16 rounded bg-white/5" />
                  </div>
                </div>

                {/* Feature tags */}
                <div className="flex flex-wrap gap-2">
                  {dashboard.features.map((feature, j) => (
                    <span 
                      key={j}
                      className="text-xs px-2 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
