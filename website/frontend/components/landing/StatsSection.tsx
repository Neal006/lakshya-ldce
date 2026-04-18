'use client'

import { TrendingUp, Clock, Users, CheckCircle } from 'lucide-react'

const stats = [
  { icon: TrendingUp, value: '1,250+', label: 'Complaints Resolved', color: 'saffron' },
  { icon: Clock, value: '2.4s', label: 'Avg. Response Time', color: 'saffron' },
  { icon: Users, value: '99%', label: 'Customer Satisfaction', color: 'saffron' },
  { icon: CheckCircle, value: '94%', label: 'SLA Compliance', color: 'saffron' },
]

export const StatsSection = () => {
  return (
    <section className="relative py-24 px-4 sm:px-6 lg:px-8 bg-black">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="font-oswald text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 uppercase tracking-wide">
            Trusted by teams worldwide
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto font-inter">
            Real-time metrics that show our AI engine at work
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="card-skeuo group p-8 rounded-2xl transition-all duration-300 hover:border-saffron/50"
            >
              {/* Icon */}
              <div className="w-14 h-14 bg-saffron/20 rounded-xl flex items-center justify-center mb-6 border border-saffron/30">
                <stat.icon className="w-7 h-7 text-saffron" />
              </div>

              {/* Number */}
              <div className="mb-2">
                <span className="font-oswald text-4xl sm:text-5xl font-bold text-saffron">
                  {stat.value}
                </span>
              </div>

              {/* Label */}
              <p className="text-white/50 font-medium font-inter">{stat.label}</p>

              {/* Decorative line */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-saffron to-transparent opacity-50" />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
