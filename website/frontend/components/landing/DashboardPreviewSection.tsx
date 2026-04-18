'use client'

import { LayoutDashboard, BarChart2, Phone, Settings } from 'lucide-react'

const dashboards = [
  {
    icon: LayoutDashboard,
    title: 'Admin Dashboard',
    description: 'Complete oversight with analytics, user management, and demo controls.',
    features: ['Analytics & Charts', 'User Management', 'Demo Mode', 'SLA Monitoring']
  },
  {
    icon: BarChart2,
    title: 'QA Dashboard',
    description: 'Product-level insights with trend analysis and export capabilities.',
    features: ['Product Analytics', 'Trend Analysis', 'Export Reports', 'Category Deep-dive']
  },
  {
    icon: Phone,
    title: 'Call Attender',
    description: 'Streamlined interface focused on resolution steps and quick actions.',
    features: ['Speech-to-Text', 'AI Resolution', 'Quick Actions', 'Real-time Updates']
  }
]

export const DashboardPreviewSection = () => {
  return (
    <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-black">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-20">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-saffron/10 rounded-full text-sm text-saffron mb-6 border border-saffron/30 font-inter">
            <Settings className="w-4 h-4" />
            Role-Based Access
          </span>
          <h2 className="font-oswald text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 uppercase tracking-wide">
            Three dashboards, one platform
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto font-inter">
            Tailored experiences for every team member
          </p>
        </div>

        {/* Dashboard cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {dashboards.map((dashboard, index) => (
            <div
              key={index}
              className="card-skeuo p-6 rounded-2xl group hover:border-saffron/50 transition-all duration-300"
            >
              {/* Header */}
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-saffron/20 rounded-lg flex items-center justify-center border border-saffron/30">
                  <dashboard.icon className="w-5 h-5 text-saffron" />
                </div>
                <div>
                  <h3 className="font-oswald text-lg font-bold text-white uppercase tracking-wide">{dashboard.title}</h3>
                  <p className="text-xs text-white/40 font-inter">{dashboard.description}</p>
                </div>
              </div>

              {/* Mockup content */}
              <div className="space-y-3 mb-6">
                {/* Window controls */}
                <div className="flex items-center gap-1.5 mb-4">
                  <div className="w-2.5 h-2.5 rounded-full bg-saffron/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
                  <div className="w-2.5 h-2.5 rounded-full bg-white/20" />
                </div>

                {/* Mock content based on dashboard type */}
                {index === 0 && (
                  <>
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      <div className="h-16 bg-white/5 rounded-lg border border-white/10" />
                      <div className="h-16 bg-white/5 rounded-lg border border-white/10" />
                    </div>
                    <div className="h-24 bg-white/5 rounded-lg border border-white/10" />
                    <div className="space-y-2 mt-3">
                      <div className="h-8 bg-white/5 rounded-lg border border-white/10" />
                      <div className="h-8 bg-white/5 rounded-lg border border-white/10" />
                    </div>
                  </>
                )}
                {index === 1 && (
                  <>
                    <div className="h-32 bg-white/5 rounded-lg mb-3 border border-white/10" />
                    <div className="space-y-2">
                      <div className="h-6 bg-white/5 rounded-lg w-3/4 border border-white/10" />
                      <div className="h-6 bg-white/5 rounded-lg border border-white/10" />
                      <div className="h-6 bg-white/5 rounded-lg w-5/6 border border-white/10" />
                    </div>
                  </>
                )}
                {index === 2 && (
                  <>
                    <div className="h-20 bg-white/5 rounded-lg mb-3 p-3 border border-white/10">
                      <div className="h-2 bg-white/10 rounded w-3/4 mb-2" />
                      <div className="h-2 bg-white/10 rounded w-1/2" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <div className="flex-1 h-8 bg-saffron/20 rounded-lg border border-saffron/30" />
                        <div className="flex-1 h-8 bg-white/5 rounded-lg border border-white/10" />
                      </div>
                      <div className="h-10 bg-white/5 rounded-lg border border-white/10" />
                    </div>
                  </>
                )}
              </div>

              {/* Feature tags */}
              <div className="flex flex-wrap gap-2 pt-4 border-t border-white/10">
                {dashboard.features.map((feature, fi) => (
                  <span key={fi} className="text-xs text-white/40 bg-white/5 px-2 py-1 rounded border border-white/10 font-inter">
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
