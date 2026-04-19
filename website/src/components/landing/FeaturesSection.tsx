'use client';

import { Brain, BarChart3, Bell, Shield, Zap, Users, Mail, Clock } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI Classification',
    description: 'Advanced NLP models analyze complaint content and automatically categorize issues with 99.2% accuracy.',
    size: 'large',
    stat: '99.2% Accuracy',
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Track resolution metrics and team performance with live dashboards.',
    size: 'small',
  },
  {
    icon: Bell,
    title: 'Instant Alerts',
    description: 'Get notified instantly when high-priority complaints arrive.',
    size: 'small',
  },
  {
    icon: Shield,
    title: 'Role-based Access',
    description: 'Secure role-based permissions for admins, QA, and call attenders.',
    size: 'small',
  },
  {
    icon: Zap,
    title: 'SSE Real-time Updates',
    description: 'Server-sent events keep your dashboard synchronized in real-time.',
    size: 'small',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Seamless handoffs between team members with full audit trails.',
    size: 'small',
  },
  {
    icon: Mail,
    title: 'Email Integration',
    description: 'Connect with Brevo, SendGrid, or any SMTP provider for automated responses and customer notifications.',
    size: 'large',
  },
  {
    icon: Clock,
    title: 'SLA Management',
    description: 'Automated SLA tracking with escalation alerts and breach prevention.',
    size: 'small',
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 relative scroll-mt-24">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="section-badge mb-4 inline-flex">Powerful Features</span>
          <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-white mb-4">
            Everything you need
          </h2>
          <p className="text-lg text-gray-400 max-w-xl mx-auto">
            A complete AI-powered complaint management solution
          </p>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, i) => (
            <div 
              key={i} 
              className={`card-skeuo p-6 group ${
                feature.size === 'large' ? 'md:col-span-2' : ''
              }`}
            >
              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-[#FF6B35]/10 flex items-center justify-center mb-4 group-hover:bg-[#FF6B35]/20 transition-colors">
                <feature.icon className="w-6 h-6 text-[#FF6B35]" />
              </div>

              {/* Title */}
              <h3 className="font-valorant text-lg text-white mb-2">
                {feature.title}
              </h3>

              {/* Description */}
              <p className="text-gray-400 text-sm leading-relaxed">
                {feature.description}
              </p>

              {/* Stat for large cards */}
              {feature.stat && (
                <div className="mt-4 pt-4 border-t border-white/5">
                  <span className="text-[#FF6B35] font-bold text-lg">{feature.stat}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
