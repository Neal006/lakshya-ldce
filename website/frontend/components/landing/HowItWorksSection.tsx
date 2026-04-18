'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { MessageSquare, Brain, Zap, CheckCircle2, ArrowRight } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

const steps = [
  {
    icon: MessageSquare,
    number: '01',
    title: 'Receive Complaint',
    description: 'Customer complaints flow in through email, calls, or dashboard. Our system captures every detail instantly.',
    color: 'blue',
    features: ['Email integration', 'Call logging', 'Dashboard input']
  },
  {
    icon: Brain,
    number: '02',
    title: 'AI Classification',
    description: 'Our ML engine automatically categorizes complaints as Product, Packaging, or Trade issues with 99% accuracy.',
    color: 'purple',
    features: ['Auto-categorization', 'Priority assignment', 'Sentiment analysis']
  },
  {
    icon: Zap,
    number: '03',
    title: 'Smart Resolution',
    description: 'AI generates step-by-step resolution recommendations tailored to each complaint type and priority level.',
    color: 'yellow',
    features: ['Resolution steps', 'SLA tracking', 'Auto-assignment']
  },
  {
    icon: CheckCircle2,
    number: '04',
    title: 'Issue Resolved',
    description: 'Track resolution progress in real-time. Close complaints faster with data-driven insights.',
    color: 'green',
    features: ['Real-time updates', 'Analytics dashboard', 'Performance metrics']
  }
]

export const HowItWorksSection = () => {
  const sectionRef = useRef<HTMLElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      const sections = gsap.utils.toArray<HTMLElement>('.step-panel')
      const progressBar = document.querySelector('.progress-fill')

      // Horizontal scroll
      const scrollTween = gsap.to(sections, {
        xPercent: -100 * (sections.length - 1),
        ease: 'none',
        scrollTrigger: {
          trigger: containerRef.current,
          pin: true,
          scrub: 1,
          end: () => '+=' + window.innerWidth * sections.length,
          onUpdate: (self) => {
            if (progressBar) {
              gsap.to(progressBar, {
                scaleX: self.progress,
                duration: 0.1,
                ease: 'none'
              })
            }
          },
          snap: {
            snapTo: 1 / (sections.length - 1),
            duration: { min: 0.2, max: 0.5 },
            ease: 'power2.inOut'
          }
        }
      })

      // Individual step animations
      sections.forEach((section, i) => {
        const content = section.querySelector('.step-content')
        const image = section.querySelector('.step-visual')

        // Content animation
        gsap.from(content, {
          scrollTrigger: {
            trigger: section,
            containerAnimation: scrollTween,
            start: 'left 80%',
            end: 'left 20%',
            toggleActions: 'play reverse play reverse'
          },
          y: 80,
          opacity: 0,
          duration: 0.8,
          ease: 'power3.out'
        })

        // Image/visual animation
        gsap.from(image, {
          scrollTrigger: {
            trigger: section,
            containerAnimation: scrollTween,
            start: 'left 70%',
            end: 'left 30%',
            toggleActions: 'play reverse play reverse'
          },
          scale: 0.8,
          rotationY: 15,
          opacity: 0,
          duration: 1,
          ease: 'power3.out'
        })
      })

      // Section title animation
      gsap.from('.how-it-works-title', {
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
    const colors: Record<string, string> = {
      blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/30 text-blue-400',
      purple: 'from-purple-500/20 to-purple-600/5 border-purple-500/30 text-purple-400',
      yellow: 'from-yellow-500/20 to-yellow-600/5 border-yellow-500/30 text-yellow-400',
      green: 'from-green-500/20 to-green-600/5 border-green-500/30 text-green-400',
    }
    return colors[color] || colors.blue
  }

  return (
    <section ref={sectionRef} className="relative bg-slate-950">
      {/* Section header */}
      <div className="py-20 px-4 sm:px-6 lg:px-8 text-center">
        <div className="how-it-works-title">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-full text-sm text-slate-400 mb-6 border border-slate-700/50">
            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            How It Works
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Four steps to resolution
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Our AI engine handles the complexity so you can focus on what matters
          </p>
        </div>
      </div>

      {/* Horizontal scroll container */}
      <div ref={containerRef} className="relative h-screen overflow-hidden">
        {/* Progress bar */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-slate-800/50 z-20">
          <div className="progress-fill h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 origin-left" style={{ transform: 'scaleX(0)' }} />
        </div>

        {/* Progress indicators */}
        <div className="absolute top-8 left-1/2 -translate-x-1/2 flex items-center gap-3 z-20">
          {steps.map((_, i) => (
            <div key={i} className="step-indicator w-12 h-1 rounded-full bg-slate-700/50 overflow-hidden">
              <div className={`indicator-fill h-full bg-gradient-to-r from-blue-500 to-purple-500 origin-left`} style={{ transform: 'scaleX(0)' }} />
            </div>
          ))}
        </div>

        {/* Horizontal scrolling panels */}
        <div className="flex h-full">
          {steps.map((step, index) => {
            const colorClass = getColorClasses(step.color)
            return (
              <div
                key={index}
                className="step-panel flex-shrink-0 w-screen h-full flex items-center justify-center px-4 sm:px-8 lg:px-16"
              >
                <div className="max-w-7xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
                  {/* Content */}
                  <div className="step-content order-2 lg:order-1">
                    <div className="flex items-center gap-4 mb-6">
                      <span className={`text-6xl font-bold bg-gradient-to-r ${colorClass} bg-clip-text text-transparent opacity-50`}>
                        {step.number}
                      </span>
                      <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${colorClass} flex items-center justify-center`}>
                        <step.icon className="w-8 h-8" />
                      </div>
                    </div>

                    <h3 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
                      {step.title}
                    </h3>

                    <p className="text-lg text-slate-400 mb-8 leading-relaxed">
                      {step.description}
                    </p>

                    <div className="flex flex-wrap gap-3">
                      {step.features.map((feature, fi) => (
                        <span 
                          key={fi}
                          className="px-4 py-2 bg-slate-800/50 rounded-full text-sm text-slate-300 border border-slate-700/50 flex items-center gap-2"
                        >
                          <div className={`w-1.5 h-1.5 rounded-full bg-${step.color}-400`} />
                          {feature}
                        </span>
                      ))}
                    </div>

                    {index < steps.length - 1 && (
                      <div className="hidden lg:flex items-center gap-3 mt-12 text-slate-500">
                        <span className="text-sm">Next step</span>
                        <ArrowRight className="w-4 h-4 animate-bounce" />
                      </div>
                    )}
                  </div>

                  {/* Visual */}
                  <div className="step-visual order-1 lg:order-2 relative">
                    <div className={`relative aspect-square max-w-md mx-auto bg-gradient-to-br ${colorClass} rounded-3xl p-1`}>
                      <div className="absolute inset-0 bg-slate-900 rounded-3xl m-[2px] flex items-center justify-center">
                        <div className="text-center">
                          <step.icon className={`w-24 h-24 mx-auto mb-6 ${colorClass.split(' ').pop()}`} />
                          <div className="space-y-3">
                            <div className="h-3 w-32 mx-auto bg-slate-800 rounded-full" />
                            <div className="h-3 w-24 mx-auto bg-slate-800 rounded-full" />
                            <div className="h-3 w-40 mx-auto bg-slate-800 rounded-full" />
                          </div>
                        </div>
                      </div>
                      
                      {/* Floating elements */}
                      <div className="absolute -top-4 -right-4 w-20 h-20 bg-slate-800 rounded-2xl border border-slate-700/50 flex items-center justify-center shadow-xl">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500" />
                      </div>
                      
                      <div className="absolute -bottom-4 -left-4 w-24 h-16 bg-slate-800 rounded-xl border border-slate-700/50 flex items-center justify-center shadow-xl">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          <span className="text-xs text-slate-400">Active</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}