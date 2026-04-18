'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { ArrowRight, Sparkles } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

export const CTASection = () => {
  const sectionRef = useRef<HTMLElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Title animation
      gsap.from('.cta-title', {
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

      // Button pulse animation
      const pulseTl = gsap.timeline({ repeat: -1 })
      pulseTl.to('.cta-button', {
        boxShadow: '0 0 60px rgba(37, 99, 235, 0.6)',
        scale: 1.02,
        duration: 1.5,
        ease: 'sine.inOut'
      }).to('.cta-button', {
        boxShadow: '0 0 20px rgba(37, 99, 235, 0.3)',
        scale: 1,
        duration: 1.5,
        ease: 'sine.inOut'
      })

      // Background gradient animation
      gsap.to('.cta-bg-gradient', {
        backgroundPosition: '200% 200%',
        duration: 8,
        repeat: -1,
        ease: 'none'
      })

      // Floating particles
      gsap.utils.toArray<HTMLElement>('.particle').forEach((particle, i) => {
        gsap.to(particle, {
          y: -100 - (i * 20),
          x: gsap.utils.random(-50, 50),
          opacity: 0,
          duration: 3 + i * 0.5,
          repeat: -1,
          delay: i * 0.8,
          ease: 'power1.out'
        })
      })
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} className="relative py-32 px-4 sm:px-6 lg:px-8 bg-slate-950 overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0">
        <div 
          className="cta-bg-gradient absolute inset-0 bg-[length:400%_400%]"
          style={{
            background: 'linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #1e1b4b)',
            backgroundSize: '400% 400%'
          }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-950/80 to-slate-950" />
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="particle absolute w-2 h-2 bg-blue-500/30 rounded-full"
            style={{
              left: `${15 + i * 15}%`,
              bottom: '20%'
            }}
          />
        ))}
      </div>

      <div className="relative max-w-4xl mx-auto text-center">
        <div className="cta-title">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full mb-8">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-blue-300 font-medium">Get Started Today</span>
          </div>

          {/* Headline */}
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
            Ready to transform your
            <span className="block bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              complaint resolution?
            </span>
          </h2>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-12">
            Join thousands of teams using TS-14 to resolve complaints faster, 
            smarter, and with AI-powered precision.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button 
              ref={buttonRef}
              className="cta-button group relative px-10 py-5 bg-blue-600 hover:bg-blue-500 text-white text-lg font-semibold rounded-2xl transition-all duration-300 overflow-hidden"
            >
              <span className="relative z-10 flex items-center gap-3">
                Start Free Trial
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            </button>

            <button className="px-10 py-5 bg-slate-800/50 hover:bg-slate-800 text-white text-lg font-semibold rounded-2xl border border-slate-700 transition-all duration-300 hover:border-slate-600">
              Schedule Demo
            </button>
          </div>

          {/* Trust badges */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
                <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
                <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <span>14-day free trial</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
                <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}