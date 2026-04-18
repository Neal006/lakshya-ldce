'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { Sparkles, Zap, Shield, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

gsap.registerPlugin(ScrollTrigger, useGSAP)

export const HeroSection = () => {
  const containerRef = useRef<HTMLElement>(null)
  const textRef = useRef<HTMLDivElement>(null)
  const mockupRef = useRef<HTMLDivElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Hero text reveal animation - INSANE split text effect
      const words = gsap.utils.toArray<HTMLElement>('.hero-word')
      const chars = gsap.utils.toArray<HTMLElement>('.hero-char')
      
      // Timeline for entrance
      const entranceTl = gsap.timeline({
        defaults: { ease: 'power4.out' }
      })

      entranceTl
        .from('.hero-badge', {
          scale: 0,
          opacity: 0,
          rotation: -180,
          duration: 0.8,
          ease: 'back.out(2)'
        })
        .from(words, {
          y: 120,
          opacity: 0,
          rotationX: -90,
          transformOrigin: 'top center',
          stagger: 0.06,
          duration: 1,
          ease: 'power4.out'
        }, '-=0.4')
        .from('.hero-subtitle', {
          y: 40,
          opacity: 0,
          filter: 'blur(20px)',
          duration: 1,
          ease: 'power3.out'
        }, '-=0.6')
        .from('.hero-cta-group', {
          scale: 0.8,
          opacity: 0,
          duration: 0.8,
          ease: 'back.out(1.7)'
        }, '-=0.5')
        .from('.floating-element', {
          scale: 0,
          opacity: 0,
          y: 50,
          rotation: gsap.utils.random(-30, 30),
          stagger: {
            amount: 0.6,
            from: 'random'
          },
          duration: 1,
          ease: 'elastic.out(1, 0.5)'
        }, '-=0.8')

      // Dashboard mockup 3D entrance
      gsap.from(mockupRef.current, {
        scrollTrigger: {
          trigger: mockupRef.current,
          start: 'top 90%',
          toggleActions: 'play none none reverse'
        },
        y: 200,
        opacity: 0,
        rotationX: 25,
        scale: 0.8,
        transformOrigin: 'center bottom',
        duration: 1.8,
        ease: 'power3.out'
      })

      // Continuous floating animation for elements
      gsap.to('.floating-element-1', {
        y: -20,
        x: 10,
        rotation: 5,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut'
      })

      gsap.to('.floating-element-2', {
        y: 15,
        x: -15,
        rotation: -5,
        duration: 4,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: 0.5
      })

      gsap.to('.floating-element-3', {
        y: -25,
        rotation: 8,
        duration: 3.5,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: 1
      })

      // Mouse parallax effect
      const handleMouseMove = (e: MouseEvent) => {
        const { clientX, clientY } = e
        const centerX = window.innerWidth / 2
        const centerY = window.innerHeight / 2
        
        const moveX = (clientX - centerX) / centerX
        const moveY = (clientY - centerY) / centerY

        gsap.to('.floating-element', {
          x: (i) => moveX * (i + 1) * 20,
          y: (i) => moveY * (i + 1) * 20,
          duration: 0.8,
          ease: 'power2.out'
        })

        gsap.to(mockupRef.current, {
          rotationY: moveX * 5,
          rotationX: -moveY * 5,
          duration: 0.6,
          ease: 'power2.out'
        })
      }

      window.addEventListener('mousemove', handleMouseMove)

      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
      }
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8"
    >
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/30 via-slate-950 to-slate-950" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
        
        {/* Animated mesh gradient */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>
      </div>

      {/* Floating elements */}
      <div className="floating-element floating-element-1 absolute top-20 left-10 lg:left-20 p-4 bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400">AI Processing</p>
            <p className="text-sm font-semibold text-white">2.4s avg</p>
          </div>
        </div>
      </div>

      <div className="floating-element floating-element-2 absolute top-32 right-10 lg:right-32 p-4 bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400">SLA Compliance</p>
            <p className="text-sm font-semibold text-white">99.2%</p>
          </div>
        </div>
      </div>

      <div className="floating-element floating-element-3 absolute bottom-40 left-16 lg:left-40 p-4 bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400">Auto-Classified</p>
            <p className="text-sm font-semibold text-white">1,247 today</p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div ref={textRef} className="relative z-10 text-center max-w-5xl mx-auto pt-20">
        {/* Badge */}
        <div className="hero-badge inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full mb-8">
          <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
          <span className="text-sm text-blue-300 font-medium">Tark Shaastra · Lakshya 2.0</span>
        </div>

        {/* Headline with split words */}
        <h1 className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight mb-6">
          <span className="block overflow-hidden">
            <span className="hero-word inline-block bg-gradient-to-r from-white via-blue-100 to-white bg-clip-text text-transparent">
              AI-Powered
            </span>
          </span>
          <span className="block overflow-hidden">
            <span className="hero-word inline-block bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Complaint
            </span>
          </span>
          <span className="block overflow-hidden">
            <span className="hero-word inline-block bg-gradient-to-r from-white via-blue-100 to-white bg-clip-text text-transparent">
              Resolution
            </span>
          </span>
        </h1>

        {/* Subtitle */}
        <p className="hero-subtitle text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Transform customer complaints into resolved tickets in seconds. 
          Our AI engine classifies, prioritizes, and suggests resolutions automatically.
        </p>

        {/* CTA Buttons */}
        <div className="hero-cta-group flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="group relative px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(37,99,235,0.5)] overflow-hidden">
            <span className="relative z-10 flex items-center gap-2">
              Get Started Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          </button>
          
          <button className="px-8 py-4 bg-slate-800/50 hover:bg-slate-800 text-white font-semibold rounded-xl border border-slate-700 transition-all duration-300 hover:border-slate-600">
            View Demo
          </button>
        </div>
      </div>

      {/* Dashboard Mockup */}
      <div 
        ref={mockupRef}
        className="relative z-10 w-full max-w-6xl mx-auto mt-16 perspective-1000"
        style={{ transformStyle: 'preserve-3d' }}
      >
        <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl overflow-hidden">
          {/* Window controls */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700/50">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
            <div className="ml-4 flex items-center gap-2 px-3 py-1 bg-slate-800/50 rounded-md text-xs text-slate-400">
              <span>ts14.ai/dashboard</span>
            </div>
          </div>
          
          {/* Mockup content */}
          <div className="p-6 grid grid-cols-12 gap-4">
            {/* Sidebar */}
            <div className="col-span-3 space-y-3">
              <div className="h-8 bg-slate-800/50 rounded-lg" />
              <div className="h-8 bg-slate-800/50 rounded-lg" />
              <div className="h-8 bg-blue-600/30 rounded-lg" />
              <div className="h-8 bg-slate-800/50 rounded-lg" />
            </div>
            
            {/* Main content */}
            <div className="col-span-9 space-y-4">
              {/* Stats row */}
              <div className="grid grid-cols-4 gap-3">
                <div className="h-20 bg-slate-800/50 rounded-lg" />
                <div className="h-20 bg-slate-800/50 rounded-lg" />
                <div className="h-20 bg-slate-800/50 rounded-lg" />
                <div className="h-20 bg-slate-800/50 rounded-lg" />
              </div>
              
              {/* Chart area */}
              <div className="h-40 bg-slate-800/30 rounded-lg" />
              
              {/* Table */}
              <div className="space-y-2">
                <div className="h-10 bg-slate-800/50 rounded-lg" />
                <div className="h-10 bg-slate-800/30 rounded-lg" />
                <div className="h-10 bg-slate-800/30 rounded-lg" />
                <div className="h-10 bg-slate-800/30 rounded-lg" />
              </div>
            </div>
          </div>
          
          {/* Glow effect */}
          <div className="absolute -inset-px bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-2xl blur-xl opacity-50 -z-10" />
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none" />
    </section>
  )
}