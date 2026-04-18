'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { TrendingUp, Clock, Users, CheckCircle } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

const stats = [
  { icon: TrendingUp, value: 1250, suffix: '+', label: 'Complaints Resolved', color: 'blue' },
  { icon: Clock, value: 2.4, suffix: 's', label: 'Avg. Response Time', color: 'purple', decimals: 1 },
  { icon: Users, value: 99, suffix: '%', label: 'Customer Satisfaction', color: 'green' },
  { icon: CheckCircle, value: 94, suffix: '%', label: 'SLA Compliance', color: 'cyan' },
]

export const StatsSection = () => {
  const sectionRef = useRef<HTMLElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Counter animation
      const counters = gsap.utils.toArray<HTMLElement>('.stat-number')
      
      counters.forEach((counter) => {
        const target = parseFloat(counter.dataset.value || '0')
        const decimals = parseInt(counter.dataset.decimals || '0')
        
        ScrollTrigger.create({
          trigger: counter,
          start: 'top 85%',
          onEnter: () => {
            gsap.fromTo(counter, 
              { innerText: 0 },
              {
                innerText: target,
                duration: 2.5,
                ease: 'power2.out',
                snap: { innerText: decimals === 0 ? 1 : 0.1 },
                onUpdate: function() {
                  const current = parseFloat(this.targets()[0].innerText)
                  counter.innerText = decimals === 0 
                    ? Math.round(current).toLocaleString()
                    : current.toFixed(decimals)
                }
              }
            )
          },
          once: true
        })
      })

      // Card reveal with 3D flip
      gsap.from('.stat-card', {
        scrollTrigger: {
          trigger: '.stats-grid',
          start: 'top 85%',
          toggleActions: 'play none none reverse'
        },
        rotationX: 90,
        y: 60,
        opacity: 0,
        transformOrigin: 'top center',
        stagger: {
          amount: 0.8,
          from: 'center'
        },
        duration: 1,
        ease: 'power3.out'
      })

      // Icon pulse animation
      gsap.to('.stat-icon', {
        scale: 1.1,
        duration: 0.8,
        stagger: {
          amount: 2,
          repeat: -1,
          yoyo: true
        },
        ease: 'sine.inOut'
      })

      // Gradient border animation
      gsap.to('.stat-card', {
        backgroundPosition: '200% 200%',
        duration: 5,
        repeat: -1,
        ease: 'none',
        stagger: 0.5
      })
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string; border: string; glow: string }> = {
      blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30', glow: 'shadow-blue-500/20' },
      purple: { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/30', glow: 'shadow-purple-500/20' },
      green: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30', glow: 'shadow-green-500/20' },
      cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/30', glow: 'shadow-cyan-500/20' },
    }
    return colors[color] || colors.blue
  }

  return (
    <section ref={sectionRef} className="relative py-24 px-4 sm:px-6 lg:px-8 bg-slate-950">
      {/* Background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Trusted by teams worldwide
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Real-time metrics that show our AI engine at work
          </p>
        </div>

        {/* Stats grid */}
        <div className="stats-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => {
            const colors = getColorClasses(stat.color)
            return (
              <div
                key={index}
                className={`stat-card group relative p-8 bg-slate-900/50 backdrop-blur-sm rounded-2xl border ${colors.border} hover:border-opacity-50 transition-all duration-500 hover:scale-105 hover:shadow-[0_0_40px_rgba(0,0,0,0.3)] overflow-hidden`}
                style={{
                  background: `linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(30, 41, 59, 0.3) 100%)`,
                }}
              >
                {/* Animated gradient border */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                {/* Glow effect on hover */}
                <div className={`absolute -inset-px bg-gradient-to-r ${colors.glow} rounded-2xl blur-xl opacity-0 group-hover:opacity-30 transition-opacity duration-500`} />

                <div className="relative z-10">
                  {/* Icon */}
                  <div className={`stat-icon w-14 h-14 ${colors.bg} rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <stat.icon className={`w-7 h-7 ${colors.text}`} />
                  </div>

                  {/* Number */}
                  <div className="flex items-baseline gap-1 mb-2">
                    <span 
                      className="stat-number text-4xl sm:text-5xl font-bold text-white"
                      data-value={stat.value}
                      data-decimals={stat.decimals || 0}
                    >
                      0
                    </span>
                    <span className={`text-2xl font-bold ${colors.text}`}>{stat.suffix}</span>
                  </div>

                  {/* Label */}
                  <p className="text-slate-400 font-medium">{stat.label}</p>

                  {/* Decorative line */}
                  <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-${stat.color}-500 to-transparent opacity-50`} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}