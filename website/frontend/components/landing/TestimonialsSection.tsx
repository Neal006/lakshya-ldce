'use client'

import { Quote, Star } from 'lucide-react'

const testimonials = [
  {
    quote: "TS-14 reduced our average resolution time by 60%. The AI classification is incredibly accurate.",
    author: "Sarah Chen",
    role: "Head of Customer Success",
    company: "TechCorp Inc.",
    rating: 5
  },
  {
    quote: "The real-time SSE updates keep our entire team synchronized. It is like magic.",
    author: "Michael Rodriguez",
    role: "Support Manager",
    company: "GlobalRetail",
    rating: 5
  },
  {
    quote: "Finally, a complaint system that actually understands context. The ML engine is impressive.",
    author: "Emily Watson",
    role: "QA Lead",
    company: "ProductFirst",
    rating: 5
  },
  {
    quote: "We went from 2-day response times to under 2 hours. Our customers love it.",
    author: "David Kim",
    role: "CTO",
    company: "FastServe",
    rating: 5
  },
  {
    quote: "The role-based dashboards give everyone exactly what they need. No clutter, pure efficiency.",
    author: "Lisa Park",
    role: "Operations Director",
    company: "ScaleUp Co",
    rating: 5
  },
  {
    quote: "Brevo integration works flawlessly. Emails automatically become trackable complaints.",
    author: "James Wilson",
    role: "IT Manager",
    company: "MailStream",
    rating: 5
  }
]

export const TestimonialsSection = () => {
  return (
    <section className="relative py-24 bg-black overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-saffron/10 rounded-full text-sm text-saffron mb-6 border border-saffron/30 font-inter">
            <Star className="w-4 h-4" />
            Customer Love
          </span>
          <h2 className="font-oswald text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 uppercase tracking-wide">
            Trusted by teams worldwide
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto font-inter">
            See what our customers have to say
          </p>
        </div>

        {/* Testimonials grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="card-skeuo p-6 rounded-2xl group hover:border-saffron/50 transition-all duration-300"
            >
              {/* Quote icon */}
              <div className="mb-4">
                <Quote className="w-8 h-8 text-saffron/40" />
              </div>

              {/* Rating */}
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-saffron text-saffron" />
                ))}
              </div>

              {/* Quote text */}
              <p className="text-white/70 mb-6 leading-relaxed font-inter">
                &ldquo;{testimonial.quote}&rdquo;
              </p>

              {/* Author */}
              <div className="flex items-center gap-3 pt-4 border-t border-white/10">
                <div className="w-10 h-10 rounded-full bg-saffron/20 flex items-center justify-center text-saffron font-bold border border-saffron/30">
                  {testimonial.author.charAt(0)}
                </div>
                <div>
                  <p className="text-white font-medium font-inter">{testimonial.author}</p>
                  <p className="text-sm text-white/40 font-inter">{testimonial.role} · {testimonial.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
