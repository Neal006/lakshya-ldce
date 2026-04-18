'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { LayoutDashboard, BarChart2, Phone, Settings } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

const dashboards = [
  {
    icon: LayoutDashboard,
    title: 'Admin Dashboard',
    description: 'Complete oversight with analytics, user management, and demo controls.',
    color: 'blue',
    features: ['Analytics & Charts', 'User Management', 'Demo Mode', 'SLA Monitoring']
  },
  {
    icon: BarChart2,
    title: 'QA Dashboard',
    description: 'Product-level insights with trend analysis and export capabilities.',
    color: 'purple',
    features: ['Product Analytics', 'Trend Analysis', 'Export Reports', 'Category Deep-dive']
  },
  {
    icon: Phone,
    title: 'Call Attender',
    description: 'Streamlined interface focused on resolution steps and quick actions.',
    color: 'green',
    features: ['Speech-to-Text', 'AI Resolution', 'Quick Actions', 'Real-time Updates']
  }
]

export const DashboardPreviewSection = () => {
  const sectionRef = useRef<HTMLElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Parallax effect for dashboard cards
      gsap.to('.dashboard-card-1', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1.5
        },
        y: -80,
        rotation: -3,
        ease: 'none'
      })

      gsap.to('.dashboard-card-2', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1
        },
        y: -120,
        ease: 'none'
      })

      gsap.to('.dashboard-card-3', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 2
        },
        y: -160,
        rotation: 3,
        ease: 'none'
      })

      // Reveal animation
      gsap.from('.dashboard-title', {
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

      gsap.from('.dashboard-card', {
        scrollTrigger: {
          trigger: '.dashboard-cards',
          start: 'top 85%',
          toggleActions: 'play none none reverse'
        },
        y: 100,
        opacity: 0,
        scale: 0.9,
        stagger: 0.2,
        duration: 1,
        ease: 'power3.out'
      })

      // Continuous floating animation
      gsap.to('.dashboard-card-1', {
        y: '-=15',
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut'
      })

      gsap.to('.dashboard-card-2', {
        y: '-=20',
        duration: 3.5,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: 0.5
      })

      gsap.to('.dashboard-card-3', {
        y: '-=15',
        duration: 4,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: 1
      })
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  const getColorClasses = (color: string) => {
    const colors: Record<string, { border: string; gradient: string; text: string }> = {
      blue: { 
        border: 'border-blue-500/30', 
        gradient: 'from-blue-500/20 via-blue-600/10 to-transparent',
        text: 'text-blue-400'
      },
      purple: { 
        border: 'border-purple-500/30', 
        gradient: 'from-purple-500/20 via-purple-600/10 to-transparent',
        text: 'text-purple-400'
      },
      green: { 
        border: 'border-green-500/30', 
        gradient: 'from-green-500/20 via-green-600/10 to-transparent',
        text: 'text-green-400'
      }
    }
    return colors[color] || colors.blue
  }

  return (
    <section ref={sectionRef} className="relative py-32 px-4 sm:px-6 lg:px-8 bg-slate-950 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-800/30 via-slate-950 to-slate-950" />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Section header */}
        <div className="dashboard-title text-center mb-20">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-full text-sm text-slate-400 mb-6 border border-slate-700/50">
            <Settings className="w-4 h-4" />
            Role-Based Access
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Three dashboards, one platform
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Tailored experiences for every team member
          </p>
        </div>

        {/* Dashboard cards with parallax */}
        <div className="dashboard-cards relative flex flex-col lg:flex-row items-center justify-center gap-6 lg:gap-8 perspective-1000">
          {dashboards.map((dashboard, index) => {
            const colors = getColorClasses(dashboard.color)
            const cardClass = `dashboard-card dashboard-card-${index + 1}`
            
            return (
              <div
                key={index}
                className={`${cardClass} relative w-full lg:w-96 bg-slate-900/80 backdrop-blur-sm rounded-2xl border ${colors.border} p-6 shadow-2xl`}
                style={{ 
                  transformStyle: 'preserve-3d',
                  zIndex: index === 1 ? 20 : 10
                }}
              >
                {/* Gradient overlay */}
                <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} rounded-2xl opacity-50`} />
                
                {/* Glow effect */}
                <div className={`absolute -inset-px bg-gradient-to-r ${colors.gradient} rounded-2xl blur-xl opacity-20`} />

                <div className="relative z-10">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-6">
                    <div className={`w-10 h-10 bg-${dashboard.color}-500/20 rounded-lg flex items-center justify-center`}>
                      <dashboard.icon className={`w-5 h-5 ${colors.text}`} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">{dashboard.title}</h3>
                      <p className="text-xs text-slate-400">{dashboard.description}</p>
                    </div>
                  </div>

                  {/* Mockup content */}
                  <div className="space-y-3">
                    {/* Window controls */}
                    <div className="flex items-center gap-1.5 mb-4">
                      <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                      <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                      <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
                    </div>

                    {/* Mock content based on dashboard type */}
                    {index === 0 && (
                      <>
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          <div className="h-16 bg-slate-800/50 rounded-lg" />
                          <div className="h-16 bg-slate-800/50 rounded-lg" />
                        </div>
                        <div className="h-24 bg-slate-800/30 rounded-lg" />
                        <div className="space-y-2 mt-3">
                          <div className="h-8 bg-slate-800/50 rounded-lg" />
                          <div className="h-8 bg-slate-800/30 rounded-lg" />
                        </div>
                      </>
                    )}
                    {index === 1 && (
                      <>
                        <div className="h-32 bg-slate-800/30 rounded-lg mb-3" />
                        <div className="space-y-2">
                          <div className="h-6 bg-slate-800/50 rounded-lg w-3/4" />
                          <div className="h-6 bg-slate-800/30 rounded-lg" />
                          <div className="h-6 bg-slate-800/50 rounded-lg w-5/6" />
                        </div>
                      </>
                    )}
                    {index === 2 && (
                      <>
                        <div className="h-20 bg-slate-800/30 rounded-lg mb-3 p-3">
                          <div className="h-2 bg-slate-700/50 rounded w-3/4 mb-2" />
                          <div className="h-2 bg-slate-700/50 rounded w-1/2" />
                        </div>
                        <div className="space-y-2">
                          <div className="flex gap-2">
                            <div className="flex-1 h-8 bg-blue-600/30 rounded-lg" />
                            <div className="flex-1 h-8 bg-slate-800/50 rounded-lg" />
                          </div>
                          <div className="h-10 bg-slate-800/30 rounded-lg" />
                        </div>
                      </>
                    )}
                  </div>

                  {/* Feature tags */}
                  <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-700/50">
                    {dashboard.features.map((feature, fi) => (
                      <span key={fi} className="text-xs text-slate-400 bg-slate-800/50 px-2 py-1 rounded">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Bottom decorative elements */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />
      </div>
    </section>
  )
}