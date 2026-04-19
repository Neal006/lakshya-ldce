'use client';

import { CheckCircle, Clock, ThumbsUp, Target } from 'lucide-react';

const stats = [
  {
    icon: CheckCircle,
    value: '1,250+',
    label: 'Complaints Resolved',
    color: '#22C55E',
  },
  {
    icon: Clock,
    value: '2.4s',
    label: 'Avg. Response Time',
    color: '#3B82F6',
  },
  {
    icon: ThumbsUp,
    value: '99%',
    label: 'Customer Satisfaction',
    color: '#FF6B35',
  },
  {
    icon: Target,
    value: '94%',
    label: 'SLA Compliance',
    color: '#A855F7',
  },
];

export function StatsSection() {
  return (
    <section id="stats" className="py-24 px-4 sm:px-6 lg:px-8 relative scroll-mt-24">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-white mb-4">
            Trusted by teams worldwide
          </h2>
          <p className="text-lg text-gray-400 max-w-xl mx-auto">
            Real-time metrics that show our AI engine at work
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <div key={i} className="card-skeuo p-6 group">
              {/* Icon */}
              <div 
                className="w-14 h-14 rounded-xl flex items-center justify-center mb-6"
                style={{ 
                  background: `linear-gradient(145deg, ${stat.color}20 0%, ${stat.color}10 100%)`,
                  boxShadow: `0 4px 0 ${stat.color}40, inset 0 1px 0 rgba(255,255,255,0.1)`
                }}
              >
                <stat.icon className="w-7 h-7" style={{ color: stat.color }} />
              </div>

              {/* Value */}
              <div className="text-4xl sm:text-5xl font-valorant text-white mb-2">
                {stat.value}
              </div>

              {/* Label */}
              <div className="text-gray-400 text-sm font-medium">
                {stat.label}
              </div>

              {/* Decorative gradient line */}
              <div 
                className="mt-6 h-1 rounded-full opacity-50"
                style={{ 
                  background: `linear-gradient(90deg, ${stat.color} 0%, transparent 100%)` 
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
