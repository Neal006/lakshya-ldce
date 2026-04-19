'use client';

import { ArrowRight, Zap, Shield, Clock } from 'lucide-react';

export function HeroSection() {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 pt-24 pb-16 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-radial from-[#FF6B35]/10 via-transparent to-transparent blur-3xl" />
      </div>

      {/* Floating stat chips */}
      <div className="absolute top-24 left-8 md:left-16 lg:left-24 hidden md:flex items-center gap-2 bg-black/50 backdrop-blur-sm border border-white/10 rounded-full px-4 py-2">
        <Zap className="w-4 h-4 text-[#FF6B35]" />
        <span className="text-sm font-medium">AI Processing:</span>
        <span className="text-sm font-bold text-[#FF6B35]">2.4s avg</span>
      </div>

      <div className="absolute top-32 right-8 md:right-16 lg:right-24 hidden md:flex items-center gap-2 bg-black/50 backdrop-blur-sm border border-white/10 rounded-full px-4 py-2">
        <Shield className="w-4 h-4 text-[#22C55E]" />
        <span className="text-sm font-medium">SLA Compliance:</span>
        <span className="text-sm font-bold text-[#22C55E]">99.2%</span>
      </div>

      <div className="absolute bottom-48 left-4 md:left-12 lg:left-20 hidden lg:flex items-center gap-2 bg-black/50 backdrop-blur-sm border border-white/10 rounded-full px-4 py-2">
        <Clock className="w-4 h-4 text-[#3B82F6]" />
        <span className="text-sm font-medium">Auto-Classified:</span>
        <span className="text-sm font-bold text-[#3B82F6]">1,247 today</span>
      </div>

      {/* Main content */}
      <div className="max-w-5xl mx-auto text-center relative z-10">
        {/* Badge */}
        <div className="mb-8">
          <span className="section-badge">
            Tark Shaastra · Lakshya 2.0
          </span>
        </div>

        {/* Headline */}
        <h1 className="mb-8">
          <span className="font-valorant text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl text-white block mb-2">
            AI-Powered
          </span>
          <span className="font-valorant text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl text-[#FF6B35] block mb-2">
            Complaint
          </span>
          <span className="font-valorant text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl text-white block">
            Resolution
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Transform customer complaints into resolved tickets in seconds. Our AI engine classifies, prioritizes, and suggests resolutions automatically.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <button className="btn-skeuo">
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </button>
          <button className="btn-secondary">
            View Demo
          </button>
        </div>

        {/* Dashboard Mockup */}
        <div className="card-skeuo w-full max-w-4xl mx-auto p-4 sm:p-6">
          {/* Browser chrome */}
          <div className="bg-[#0a0a0a] rounded-lg overflow-hidden border border-white/5">
            {/* Window controls */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-[#0f0f0f]">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
              </div>
              <div className="flex-1 flex justify-center">
                <div className="bg-[#1a1a1a] rounded-md px-4 py-1 text-xs text-gray-500">
                  ts-14.app/dashboard
                </div>
              </div>
            </div>

            {/* Dashboard content */}
            <div className="p-4 sm:p-6">
              {/* Sidebar + Main content layout */}
              <div className="flex gap-4">
                {/* Sidebar */}
                <div className="hidden sm:flex flex-col gap-2 w-16">
                  <div className="w-10 h-10 rounded-lg bg-[#FF6B35]/20 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-[#FF6B35]" />
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-white/5" />
                  <div className="w-10 h-10 rounded-lg bg-white/5" />
                  <div className="w-10 h-10 rounded-lg bg-white/5" />
                </div>

                {/* Main content */}
                <div className="flex-1 space-y-4">
                  {/* Stats row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: 'Total', value: '2,847' },
                      { label: 'Pending', value: '124' },
                      { label: 'Resolved', value: '2,598' },
                      { label: 'SLA', value: '99.2%' },
                    ].map((stat, i) => (
                      <div key={i} className="bg-white/5 rounded-lg p-3">
                        <div className="text-xs text-gray-500 mb-1">{stat.label}</div>
                        <div className="text-lg font-bold text-white">{stat.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Chart area */}
                  <div className="bg-white/5 rounded-lg p-4 h-24 flex items-end gap-2">
                    {[40, 65, 45, 80, 55, 70, 90].map((height, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-[#FF6B35]/60 rounded-t-sm"
                        style={{ height: `${height}%` }}
                      />
                    ))}
                  </div>

                  {/* Table rows */}
                  <div className="space-y-2">
                    {[
                      { id: '#2841', status: 'High' },
                      { id: '#2840', status: 'Medium' },
                      { id: '#2839', status: 'Low' },
                    ].map((row, i) => (
                      <div key={i} className="flex items-center gap-3 bg-white/5 rounded-lg p-3">
                        <div className="w-8 h-8 rounded bg-white/10" />
                        <div className="flex-1">
                          <div className="h-2 w-24 bg-white/20 rounded mb-1" />
                          <div className="h-2 w-16 bg-white/10 rounded" />
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${
                          row.status === 'High' ? 'bg-red-500/20 text-red-400' :
                          row.status === 'Medium' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {row.status}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black to-transparent pointer-events-none" />
    </section>
  );
}
