'use client'

import { MessageSquare, Brain, Zap, CheckCircle2, ArrowRight } from 'lucide-react'

const steps = [
  {
    icon: MessageSquare,
    number: '01',
    title: 'Receive Complaint',
    description: 'Customer complaints flow in through email, calls, or dashboard. Our system captures every detail instantly.',
    features: ['Email integration', 'Call logging', 'Dashboard input']
  },
  {
    icon: Brain,
    number: '02',
    title: 'AI Classification',
    description: 'Our ML engine automatically categorizes complaints as Product, Packaging, or Trade issues with 99% accuracy.',
    features: ['Auto-categorization', 'Priority assignment', 'Sentiment analysis']
  },
  {
    icon: Zap,
    number: '03',
    title: 'Smart Resolution',
    description: 'AI generates step-by-step resolution recommendations tailored to each complaint type and priority level.',
    features: ['Resolution steps', 'SLA tracking', 'Auto-assignment']
  },
  {
    icon: CheckCircle2,
    number: '04',
    title: 'Issue Resolved',
    description: 'Track resolution progress in real-time. Close complaints faster with data-driven insights.',
    features: ['Real-time updates', 'Analytics dashboard', 'Performance metrics']
  }
]

export const HowItWorksSection = () => {
  return (
    <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-black">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-saffron/10 rounded-full text-sm text-saffron mb-6 border border-saffron/30 font-inter">
            <span className="w-2 h-2 bg-saffron rounded-full" />
            How It Works
          </span>
          <h2 className="font-oswald text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 uppercase tracking-wide">
            Four steps to resolution
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto font-inter">
            Our AI engine handles the complexity so you can focus on what matters
          </p>
        </div>

        {/* Steps grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {steps.map((step, index) => (
            <div
              key={index}
              className="card-skeuo p-8 rounded-2xl group hover:border-saffron/50 transition-all duration-300"
            >
              <div className="flex items-start gap-6">
                {/* Number and Icon */}
                <div className="flex-shrink-0">
                  <span className="font-oswald text-6xl font-bold text-saffron/30">
                    {step.number}
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-saffron/20 rounded-xl flex items-center justify-center border border-saffron/30">
                      <step.icon className="w-6 h-6 text-saffron" />
                    </div>
                    <h3 className="font-oswald text-2xl font-bold text-white uppercase tracking-wide">
                      {step.title}
                    </h3>
                  </div>

                  <p className="text-white/50 mb-6 leading-relaxed font-inter">
                    {step.description}
                  </p>

                  {/* Features */}
                  <div className="flex flex-wrap gap-2">
                    {step.features.map((feature, fi) => (
                      <span 
                        key={fi}
                        className="px-3 py-1 bg-saffron/10 rounded-full text-sm text-saffron border border-saffron/20 font-inter"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Arrow to next step */}
              {index < steps.length - 1 && (
                <div className="hidden lg:flex items-center justify-end mt-6 text-saffron/50">
                  <ArrowRight className="w-6 h-6" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
