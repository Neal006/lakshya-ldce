'use client';

import { Quote, Star } from 'lucide-react';

const testimonials = [
  {
    quote: "TS-14 has completely transformed how we handle customer complaints. The AI classification is incredibly accurate and saves us hours every day.",
    author: "Sarah Mitchell",
    role: "Head of Customer Success",
    company: "TechCorp Inc.",
    initial: "S",
  },
  {
    quote: "The real-time analytics and SLA tracking have helped us improve our response times by 300%. Our customers have never been happier.",
    author: "James Chen",
    role: "VP of Operations",
    company: "GlobalSupport LLC",
    initial: "J",
  },
  {
    quote: "We integrated TS-14 in under a week. The API is clean, documentation is excellent, and the team was incredibly responsive.",
    author: "Priya Patel",
    role: "CTO",
    company: "StartupXYZ",
    initial: "P",
  },
  {
    quote: "The role-based dashboards are perfect. Our QA team, call attenders, and admins each have exactly what they need.",
    author: "Michael Torres",
    role: "Call Center Manager",
    company: "ServiceFirst Co.",
    initial: "M",
  },
  {
    quote: "Finally, a complaint management system that actually works with AI, not just buzzwords. The auto-resolution suggestions are game-changing.",
    author: "Emily Watson",
    role: "Director of Support",
    company: "CloudNine Systems",
    initial: "E",
  },
  {
    quote: "We've reduced our average resolution time from days to hours. The ROI on TS-14 was visible within the first month.",
    author: "David Kim",
    role: "CEO",
    company: "RapidResponse",
    initial: "D",
  },
];

export function TestimonialsSection() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="section-badge mb-4 inline-flex">Customer Love</span>
          <h2 className="font-valorant text-3xl sm:text-4xl md:text-5xl text-white mb-4">
            Trusted by teams worldwide
          </h2>
          <p className="text-lg text-gray-400 max-w-xl mx-auto">
            See what our customers have to say
          </p>
        </div>

        {/* Testimonials grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, i) => (
            <div key={i} className="card-skeuo p-6 group">
              {/* Quote icon */}
              <div className="mb-4">
                <Quote className="w-8 h-8 text-[#FF6B35]/50" />
              </div>

              {/* Stars */}
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, j) => (
                  <Star 
                    key={j} 
                    className="w-4 h-4 fill-[#FF6B35] text-[#FF6B35]" 
                  />
                ))}
              </div>

              {/* Quote */}
              <blockquote className="text-gray-300 text-sm leading-relaxed mb-6">
                "{testimonial.quote}"
              </blockquote>

              {/* Author */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#FF6B35]/20 flex items-center justify-center text-[#FF6B35] font-bold">
                  {testimonial.initial}
                </div>
                <div>
                  <div className="text-white font-medium text-sm">{testimonial.author}</div>
                  <div className="text-gray-500 text-xs">{testimonial.role}, {testimonial.company}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
