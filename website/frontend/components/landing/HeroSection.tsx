'use client'

import { Sparkles, Zap, Shield, ArrowRight } from 'lucide-react'

export const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8 bg-black">
      {/* Subtle gradient background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-saffron/10 via-black to-black" />
      </div>

      {/* Floating elements - static, no animation */}
      <div className="absolute top-20 left-10 lg:left-20 p-4 card-skeuo rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-saffron/20 rounded-lg flex items-center justify-center border border-saffron/30">
            <Zap className="w-5 h-5 text-saffron" />
          </div>
          <div>
            <p className="text-xs text-white/60">AI Processing</p>
            <p className="text-sm font-semibold text-white">2.4s avg</p>
          </div>
        </div>
      </div>

      <div className="absolute top-32 right-10 lg:right-32 p-4 card-skeuo rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-saffron/20 rounded-lg flex items-center justify-center border border-saffron/30">
            <Shield className="w-5 h-5 text-saffron" />
          </div>
          <div>
            <p className="text-xs text-white/60">SLA Compliance</p>
            <p className="text-sm font-semibold text-white">99.2%</p>
          </div>
        </div>
      </div>

      <div className="absolute bottom-40 left-16 lg:left-40 p-4 card-skeuo rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-saffron/20 rounded-lg flex items-center justify-center border border-saffron/30">
            <Sparkles className="w-5 h-5 text-saffron" />
          </div>
          <div>
            <p className="text-xs text-white/60">Auto-Classified</p>
            <p className="text-sm font-semibold text-white">1,247 today</p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="relative z-10 text-center max-w-5xl mx-auto pt-20">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-saffron/10 border border-saffron/30 rounded-full mb-8">
          <span className="w-2 h-2 bg-saffron rounded-full" />
          <span className="text-sm text-saffron font-medium">Tark Shaastra · Lakshya 2.0</span>
        </div>

        {/* Headline - Valorant style tall font */}
        <h1 className="font-oswald text-6xl sm:text-7xl lg:text-8xl xl:text-9xl font-bold tracking-tight mb-6 uppercase">
          <span className="block text-white">
            AI-Powered
          </span>
          <span className="block text-saffron">
            Complaint
          </span>
          <span className="block text-white">
            Resolution
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-white/60 max-w-2xl mx-auto mb-10 leading-relaxed font-inter">
          Transform customer complaints into resolved tickets in seconds. 
          Our AI engine classifies, prioritizes, and suggests resolutions automatically.
        </p>

        {/* CTA Buttons - Skeuomorphic */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="btn-skeuo px-8 py-4 text-white rounded-xl flex items-center gap-2">
            <span>Get Started Free</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          
          <button className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white font-semibold rounded-xl border border-white/20 transition-colors">
            View Demo
          </button>
        </div>
      </div>

      {/* Dashboard Mockup - Skeuomorphic */}
      <div className="relative z-10 w-full max-w-6xl mx-auto mt-16">
        <div className="card-skeuo rounded-2xl overflow-hidden p-1">
          <div className="bg-neutral-900 rounded-xl overflow-hidden">
            {/* Window controls */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10">
              <div className="w-3 h-3 rounded-full bg-saffron/60" />
              <div className="w-3 h-3 rounded-full bg-white/20" />
              <div className="w-3 h-3 rounded-full bg-white/20" />
              <div className="ml-4 flex items-center gap-2 px-3 py-1 bg-white/5 rounded-md text-xs text-white/40">
                <span>ts14.ai/dashboard</span>
              </div>
            </div>
            
            {/* Mockup content */}
            <div className="p-6 grid grid-cols-12 gap-4">
              {/* Sidebar */}
              <div className="col-span-3 space-y-3">
                <div className="h-8 bg-white/5 rounded-lg border border-white/10" />
                <div className="h-8 bg-saffron/20 rounded-lg border border-saffron/30" />
                <div className="h-8 bg-white/5 rounded-lg border border-white/10" />
                <div className="h-8 bg-white/5 rounded-lg border border-white/10" />
              </div>
              
              {/* Main content */}
              <div className="col-span-9 space-y-4">
                {/* Stats row */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="h-20 bg-white/5 rounded-lg border border-white/10" />
                  <div className="h-20 bg-white/5 rounded-lg border border-white/10" />
                  <div className="h-20 bg-white/5 rounded-lg border border-white/10" />
                  <div className="h-20 bg-white/5 rounded-lg border border-white/10" />
                </div>
                
                {/* Chart area */}
                <div className="h-40 bg-white/5 rounded-lg border border-white/10" />
                
                {/* Table */}
                <div className="space-y-2">
                  <div className="h-10 bg-white/5 rounded-lg border border-white/10" />
                  <div className="h-10 bg-white/5 rounded-lg border border-white/10" />
                  <div className="h-10 bg-white/5 rounded-lg border border-white/10" />
                  <div className="h-10 bg-white/5 rounded-lg border border-white/10" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black to-transparent pointer-events-none" />
    </section>
  )
}
