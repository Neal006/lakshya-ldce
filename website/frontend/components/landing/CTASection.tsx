'use client'

import { ArrowRight, Sparkles } from 'lucide-react'

export const CTASection = () => {
  return (
    <section className="relative py-32 px-4 sm:px-6 lg:px-8 bg-black overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-saffron/10 via-black to-black" />
      </div>

      <div className="relative max-w-4xl mx-auto text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-saffron/10 border border-saffron/30 rounded-full mb-8">
          <Sparkles className="w-4 h-4 text-saffron" />
          <span className="text-sm text-saffron font-medium font-inter">Get Started Today</span>
        </div>

        {/* Headline */}
        <h2 className="font-oswald text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 uppercase tracking-wide">
          Ready to transform your
          <span className="block text-saffron">
            complaint resolution?
          </span>
        </h2>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-white/50 max-w-2xl mx-auto mb-12 font-inter">
          Join thousands of teams using TS-14 to resolve complaints faster, 
          smarter, and with AI-powered precision.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="btn-skeuo px-10 py-5 text-white text-lg rounded-2xl flex items-center gap-3">
            <span>Start Free Trial</span>
            <ArrowRight className="w-5 h-5" />
          </button>

          <button className="px-10 py-5 bg-white/5 hover:bg-white/10 text-white text-lg font-semibold rounded-2xl border border-white/20 transition-colors font-inter">
            Schedule Demo
          </button>
        </div>

        {/* Trust badges */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-white/40 font-inter">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-saffron/20 flex items-center justify-center border border-saffron/30">
              <svg className="w-3 h-3 text-saffron" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <span>No credit card required</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-saffron/20 flex items-center justify-center border border-saffron/30">
              <svg className="w-3 h-3 text-saffron" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <span>14-day free trial</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-saffron/20 flex items-center justify-center border border-saffron/30">
              <svg className="w-3 h-3 text-saffron" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <span>Cancel anytime</span>
          </div>
        </div>
      </div>
    </section>
  )
}
