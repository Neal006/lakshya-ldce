'use client'

import { 
  Bot, 
  BarChart3, 
  Bell, 
  Shield, 
  Zap, 
  Users,
  Mail,
  Clock
} from 'lucide-react'

const features = [
  {
    icon: Bot,
    title: 'AI Classification',
    description: 'Automatically categorize complaints as Product, Packaging, or Trade with 99.2% accuracy using our ML engine.',
    size: 'large',
    stats: { label: 'Accuracy', value: '99.2%' }
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Track resolution times, SLA compliance, and trends across all complaint categories.',
    size: 'small'
  },
  {
    icon: Bell,
    title: 'Instant Alerts',
    description: 'Get notified when SLA deadlines approach or critical issues arise.',
    size: 'small'
  },
  {
    icon: Shield,
    title: 'Role-based Access',
    description: 'Three distinct dashboards tailored for Admin, QA, and Call Attender roles with appropriate permissions.',
    size: 'medium'
  },
  {
    icon: Zap,
    title: 'SSE Real-time Updates',
    description: 'See complaints update instantly across all connected clients using Server-Sent Events.',
    size: 'small'
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Escalate, assign, and track complaints across your entire support team.',
    size: 'medium'
  },
  {
    icon: Mail,
    title: 'Email Integration',
    description: 'Automatically create complaints from incoming emails via Brevo webhook integration.',
    size: 'large'
  },
  {
    icon: Clock,
    title: 'SLA Management',
    description: 'Auto-calculate deadlines based on priority and get breach warnings before it is too late.',
    size: 'small'
  }
]

export const FeaturesSection = () => {
  const getGridClass = (size: string) => {
    const sizes: Record<string, string> = {
      small: 'col-span-1',
      medium: 'col-span-1',
      large: 'col-span-1 lg:col-span-2'
    }
    return sizes[size] || sizes.small
  }

  return (
    <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-black">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-saffron/10 rounded-full text-sm text-saffron mb-6 border border-saffron/30 font-inter">
            <Zap className="w-4 h-4" />
            Powerful Features
          </span>
          <h2 className="font-oswald text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 uppercase tracking-wide">
            Everything you need
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto font-inter">
            A complete AI-powered complaint management solution
          </p>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          {features.map((feature, index) => {
            const gridClass = getGridClass(feature.size)
            
            return (
              <div
                key={index}
                className={`${gridClass} card-skeuo group p-6 lg:p-8 rounded-2xl cursor-pointer transition-all duration-300 hover:border-saffron/50`}
              >
                {/* Icon */}
                <div className="w-12 h-12 bg-saffron/20 rounded-xl flex items-center justify-center mb-4 border border-saffron/30 group-hover:bg-saffron/30 transition-colors">
                  <feature.icon className="w-6 h-6 text-saffron" />
                </div>

                {/* Content */}
                <div>
                  <h3 className="font-oswald text-xl font-bold text-white mb-2 uppercase tracking-wide">
                    {feature.title}
                  </h3>
                  <p className="text-white/50 text-sm leading-relaxed font-inter">
                    {feature.description}
                  </p>

                  {/* Stats for large cards */}
                  {feature.stats && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                      <div className="flex items-baseline gap-2">
                        <span className="font-oswald text-2xl font-bold text-saffron">{feature.stats.value}</span>
                        <span className="text-xs text-white/40 font-inter">{feature.stats.label}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
