'use client';

import { ArrowRight, CheckCircle } from 'lucide-react';

export function CTASection() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-4xl mx-auto">
        <div className="card-skeuo p-8 sm:p-12 lg:p-16 text-center relative overflow-hidden">
          {/* Background glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[200%] h-[200%] bg-gradient-radial from-[#FF6B35]/10 via-transparent to-transparent pointer-events-none" />
          
          <div className="relative z-10">
            {/* Badge */}
            <span className="section-badge mb-6 inline-flex">Get Started Today</span>

            {/* Headline */}
            <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-white mb-4">
              Ready to transform your
            </h2>
            <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-[#FF6B35] mb-6">
              complaint resolution?
            </h2>

            {/* Subtitle */}
            <p className="text-lg text-gray-400 max-w-xl mx-auto mb-8">
              Join thousands of teams using SOLV.ai to resolve complaints faster, smarter, and with AI-powered precision.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8">
              <button className="btn-skeuo">
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </button>
              <button className="btn-secondary">
                Schedule Demo
              </button>
            </div>

            {/* Trust bullets */}
            <div className="flex flex-wrap items-center justify-center gap-6">
              {[
                'No credit card required',
                '14-day free trial',
                'Cancel anytime',
              ].map((bullet, i) => (
                <div key={i} className="flex items-center gap-2 text-gray-400 text-sm">
                  <CheckCircle className="w-4 h-4 text-[#22C55E]" />
                  <span>{bullet}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
