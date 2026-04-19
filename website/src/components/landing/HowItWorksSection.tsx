'use client';

import { Inbox, Brain, Sparkles, CheckCircle } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: Inbox,
    title: 'Receive Complaint',
    description: 'Ingest complaints from email, forms, chat, or API. Our system captures every detail instantly.',
    features: ['Multi-channel', 'Auto-capture', 'Instant sync'],
  },
  {
    number: '02',
    icon: Brain,
    title: 'AI Classification',
    description: 'Our ML model analyzes sentiment, categorizes issues, and assigns priority automatically.',
    features: ['Sentiment analysis', 'Smart categorization', 'Priority scoring'],
  },
  {
    number: '03',
    icon: Sparkles,
    title: 'Smart Resolution',
    description: 'Get AI-suggested resolutions based on historical data and similar resolved cases.',
    features: ['Auto-suggestions', 'Knowledge base', 'Smart routing'],
  },
  {
    number: '04',
    icon: CheckCircle,
    title: 'Issue Resolved',
    description: 'Track resolution progress with real-time updates and automated status changes.',
    features: ['Auto-updates', 'SLA tracking', 'Analytics'],
  },
];

export function HowItWorksSection() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="section-badge mb-4 inline-flex">How It Works</span>
          <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-white mb-4">
            Four steps to resolution
          </h2>
          <p className="text-lg text-gray-400 max-w-xl mx-auto">
            Our AI engine handles the complexity so you can focus on what matters
          </p>
        </div>

        {/* Steps grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <div key={i} className="card-skeuo p-6 group relative">
              {/* Number badge */}
              <div className="absolute -top-3 -right-3 w-10 h-10 rounded-full bg-[#FF6B35] flex items-center justify-center text-black font-bold text-sm">
                {step.number}
              </div>

              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-[#FF6B35]/10 flex items-center justify-center mb-4 group-hover:bg-[#FF6B35]/20 transition-colors">
                <step.icon className="w-6 h-6 text-[#FF6B35]" />
              </div>

              {/* Title */}
              <h3 className="font-valorant text-xl text-white mb-3">
                {step.title}
              </h3>

              {/* Description */}
              <p className="text-gray-400 text-sm mb-4 leading-relaxed">
                {step.description}
              </p>

              {/* Feature chips */}
              <div className="flex flex-wrap gap-2">
                {step.features.map((feature, j) => (
                  <span 
                    key={j}
                    className="text-xs px-2 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10"
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
