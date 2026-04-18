'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
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

gsap.registerPlugin(ScrollTrigger, useGSAP)

const features = [
  {
    icon: Bot,
    title: 'AI Classification',
    description: 'Automatically categorize complaints as Product, Packaging, or Trade with 99.2% accuracy using our ML engine.',
    color: 'blue',
    size: 'large',
    stats: { label: 'Accuracy', value: '99.2%' }
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Track resolution times, SLA compliance, and trends across all complaint categories.',
    color: 'purple',
    size: 'small'
  },
  {
    icon: Bell,
    title: 'Instant Alerts',
    description: 'Get notified when SLA deadlines approach or critical issues arise.',
    color: 'yellow',
    size: 'small'
  },
  {
    icon: Shield,
    title: 'Role-based Access',
    description: 'Three distinct dashboards tailored for Admin, QA, and Call Attender roles with appropriate permissions.',
    color: 'green',
    size: 'medium'
  },
  {
    icon: Zap,
    title: 'SSE Real-time Updates',
    description: 'See complaints update instantly across all connected clients using Server-Sent Events.',
    color: 'cyan',
    size: 'small'
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Escalate, assign, and track complaints across your entire support team.',
    color: 'pink',
    size: 'medium'
  },
  {
    icon: Mail,
    title: 'Email Integration',
    description: 'Automatically create complaints from incoming emails via Brevo webhook integration.',
    color: 'orange',
    size: 'large'
  },
  {
    icon: Clock,
    title: 'SLA Management',
    description: 'Auto-calculate deadlines based on priority and get breach warnings before it is too late.',
    color: 'red',
    size: 'small'
  }
]

export const FeaturesSection = () => {
  const sectionRef = useRef<HTMLElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Batch reveal for cards
      ScrollTrigger.batch('.feature-card', {
        onEnter: (elements) => {
          gsap.from(elements, {
            y: 60,
            opacity: 0,
            scale: 0.95,
            rotationX: 10,
            transformOrigin: 'top center',
            stagger: {
              amount: 0.8,
              grid: [3, 3],
              from: 'start'
            },
            duration: 0.8,
            ease: 'power3.out'
          })
        },
        start: 'top 85%'
      })

      // Hover tilt effect using event listeners
      const cards = gsap.utils.toArray<HTMLElement>('.feature-card')
      
      cards.forEach((card) => {
        card.addEventListener('mousemove', (e: MouseEvent) => {
          const rect = card.getBoundingClientRect()
          const x = e.clientX - rect.left
          const y = e.clientY - rect.top
          const centerX = rect.width / 2
          const centerY = rect.height / 2
          const rotateX = (y - centerY) / 15
          const rotateY = (centerX - x) / 15

          gsap.to(card, {
            rotationX: rotateX,
            rotationY: rotateY,
            scale: 1.02,
            duration: 0.4,
            ease: 'power2.out',
            transformPerspective: 1000
          })

          // Animate gradient on hover
          gsap.to(card.querySelector('.card-gradient'), {
            opacity: 1,
            duration: 0.3
          })
        })

        card.addEventListener('mouseleave', () => {
          gsap.to(card, {
            rotationX: 0,
            rotationY: 0,
            scale: 1,
            duration: 0.6,
            ease: 'elastic.out(1, 0.5)'
          })

          gsap.to(card.querySelector('.card-gradient'), {
            opacity: 0,
            duration: 0.3
          })
        })
      })

      // Title animation
      gsap.from('.features-title', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 80%',
          toggleActions: 'play none none reverse'
        },
        y: 50,
        opacity: 0,
        duration: 0.8,
        ease: 'power3.out'
      })
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string; border: string; gradient: string }> = {
      blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30', gradient: 'from-blue-500/20 to-transparent' },
      purple: { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/30', gradient: 'from-purple-500/20 to-transparent' },
      yellow: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30', gradient: 'from-yellow-500/20 to-transparent' },
      green: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30', gradient: 'from-green-500/20 to-transparent' },
      cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/30', gradient: 'from-cyan-500/20 to-transparent' },
      pink: { bg: 'bg-pink-500/20', text: 'text-pink-400', border: 'border-pink-500/30', gradient: 'from-pink-500/20 to-transparent' },
      orange: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30', gradient: 'from-orange-500/20 to-transparent' },
      red: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30', gradient: 'from-red-500/20 to-transparent' },
    }
    return colors[color] || colors.blue
  }

  const getGridClass = (size: string) => {
    const sizes: Record<string, string> = {
      small: 'col-span-1 row-span-1',
      medium: 'col-span-1 lg:col-span-1 row-span-1',
      large: 'col-span-1 lg:col-span-2 row-span-1 lg:row-span-1'
    }
    return sizes[size] || sizes.small
  }

  return (
    <section ref={sectionRef} className="relative py-24 px-4 sm:px-6 lg:px-8 bg-slate-950">
      {/* Background gradient */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Section header */}
        <div className="features-title text-center mb-16">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-full text-sm text-slate-400 mb-6 border border-slate-700/50">
            <Zap className="w-4 h-4 text-yellow-400" />
            Powerful Features
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Everything you need
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            A complete AI-powered complaint management solution
          </p>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          {features.map((feature, index) => {
            const colors = getColorClasses(feature.color)
            const gridClass = getGridClass(feature.size)
            
            return (
              <div
                key={index}
                className={`feature-card ${gridClass} group relative p-6 lg:p-8 bg-slate-900/50 backdrop-blur-sm rounded-2xl border ${colors.border} overflow-hidden cursor-pointer`}
                style={{ transformStyle: 'preserve-3d' }}
              >
                {/* Hover gradient overlay */}
                <div className={`card-gradient absolute inset-0 bg-gradient-to-br ${colors.gradient} opacity-0 pointer-events-none transition-opacity duration-300`} />
                
                {/* Icon */}
                <div className={`relative z-10 w-12 h-12 ${colors.bg} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className={`w-6 h-6 ${colors.text}`} />
                </div>

                {/* Content */}
                <div className="relative z-10">
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-slate-300 transition-all duration-300">
                    {feature.title}
                  </h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    {feature.description}
                  </p>

                  {/* Stats for large cards */}
                  {feature.stats && (
                    <div className="mt-4 pt-4 border-t border-slate-700/50">
                      <div className="flex items-baseline gap-2">
                        <span className={`text-2xl font-bold ${colors.text}`}>{feature.stats.value}</span>
                        <span className="text-xs text-slate-500">{feature.stats.label}</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Decorative corner */}
                <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl ${colors.gradient} rounded-bl-full opacity-30 group-hover:opacity-50 transition-opacity duration-300`} />
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}