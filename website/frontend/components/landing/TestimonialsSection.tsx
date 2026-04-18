'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { Quote, Star } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

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
  const sectionRef = useRef<HTMLElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Marquee animations - row 1 moves left
      gsap.to('.marquee-row-1', {
        xPercent: -50,
        duration: 40,
        ease: 'none',
        repeat: -1
      })

      // Marquee animations - row 2 moves right
      gsap.to('.marquee-row-2', {
        xPercent: 50,
        duration: 45,
        ease: 'none',
        repeat: -1
      })

      // Speed up on scroll
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top bottom',
        end: 'bottom top',
        onUpdate: (self) => {
          const velocity = Math.abs(self.getVelocity()) / 5000
          const timeScale = 1 + Math.min(velocity, 3)
          gsap.to('.marquee-row-1, .marquee-row-2', {
            timeScale: timeScale,
            duration: 0.3
          })
        }
      })

      // Title animation
      gsap.from('.testimonials-title', {
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

  const TestimonialCard = ({ testimonial }: { testimonial: typeof testimonials[0] }) => (
    <div className="flex-shrink-0 w-[400px] p-6 mx-3 bg-slate-900/60 backdrop-blur-sm rounded-2xl border border-slate-700/50 hover:border-slate-600/50 transition-all duration-300 hover:scale-[1.02] group">
      {/* Quote icon */}
      <div className="mb-4">
        <Quote className="w-8 h-8 text-blue-500/40 group-hover:text-blue-500/60 transition-colors" />
      </div>

      {/* Rating */}
      <div className="flex gap-1 mb-4">
        {[...Array(testimonial.rating)].map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-yellow-500 text-yellow-500" />
        ))}
      </div>

      {/* Quote text */}
      <p className="text-slate-300 mb-6 leading-relaxed">
        &ldquo;{testimonial.quote}&rdquo;
      </p>

      {/* Author */}
      <div className="flex items-center gap-3 pt-4 border-t border-slate-700/50">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
          {testimonial.author.charAt(0)}
        </div>
        <div>
          <p className="text-white font-medium">{testimonial.author}</p>
          <p className="text-sm text-slate-500">{testimonial.role} · {testimonial.company}</p>
        </div>
      </div>
    </div>
  )

  return (
    <section ref={sectionRef} className="relative py-24 bg-slate-950 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800/20 via-slate-950 to-slate-950" />
      </div>

      <div className="relative">
        {/* Section header */}
        <div className="testimonials-title text-center mb-16 px-4">
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-full text-sm text-slate-400 mb-6 border border-slate-700/50">
            <Star className="w-4 h-4 text-yellow-400" />
            Customer Love
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Trusted by teams worldwide
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            See what our customers have to say
          </p>
        </div>

        {/* Marquee row 1 - left */}
        <div className="mb-6 overflow-hidden">
          <div className="marquee-row-1 flex" style={{ width: 'fit-content' }}>
            {/* Double the testimonials for seamless loop */}
            {[...testimonials, ...testimonials].map((testimonial, index) => (
              <TestimonialCard key={`row1-${index}`} testimonial={testimonial} />
            ))}
          </div>
        </div>

        {/* Marquee row 2 - right */}
        <div className="overflow-hidden">
          <div 
            className="marquee-row-2 flex" 
            style={{ 
              width: 'fit-content',
              transform: 'translateX(-50%)'
            }}
          >
            {/* Reverse order for variety */}
            {[...testimonials.reverse(), ...testimonials].map((testimonial, index) => (
              <TestimonialCard key={`row2-${index}`} testimonial={testimonial} />
            ))}
          </div>
        </div>

        {/* Gradient overlays for smooth edges */}
        <div className="absolute top-0 left-0 bottom-0 w-32 bg-gradient-to-r from-slate-950 to-transparent pointer-events-none z-10" />
        <div className="absolute top-0 right-0 bottom-0 w-32 bg-gradient-to-l from-slate-950 to-transparent pointer-events-none z-10" />
      </div>
    </section>
  )
}