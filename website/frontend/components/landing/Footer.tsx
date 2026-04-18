'use client'

import { useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import { Github, Twitter, Linkedin, Mail } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

const footerLinks = {
  Product: ['Features', 'Pricing', 'Integrations', 'Changelog', 'Roadmap'],
  Company: ['About', 'Blog', 'Careers', 'Press', 'Partners'],
  Resources: ['Documentation', 'API Reference', 'Guides', 'Support', 'Community'],
  Legal: ['Privacy', 'Terms', 'Security', 'Cookies', 'Licenses']
}

export const Footer = () => {
  const footerRef = useRef<HTMLElement>(null)

  useGSAP(() => {
    const ctx = gsap.context(() => {
      // Staggered reveal for link columns
      gsap.from('.footer-column', {
        scrollTrigger: {
          trigger: footerRef.current,
          start: 'top 90%',
          toggleActions: 'play none none reverse'
        },
        y: 30,
        opacity: 0,
        stagger: 0.1,
        duration: 0.6,
        ease: 'power2.out'
      })

      // Logo animation
      gsap.from('.footer-logo', {
        scrollTrigger: {
          trigger: footerRef.current,
          start: 'top 90%',
          toggleActions: 'play none none reverse'
        },
        scale: 0.8,
        opacity: 0,
        duration: 0.6,
        ease: 'back.out(1.7)',
        delay: 0.4
      })
    }, footerRef)

    return () => ctx.revert()
  }, [])

  return (
    <footer ref={footerRef} className="relative py-16 px-4 sm:px-6 lg:px-8 bg-slate-950 border-t border-slate-800/50">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 lg:gap-12">
          {/* Brand column */}
          <div className="col-span-2 footer-column">
            <div className="footer-logo flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">TS</span>
              </div>
              <div>
                <span className="text-white font-bold text-xl">TS-14</span>
                <p className="text-xs text-slate-500">AI Complaint Resolution</p>
              </div>
            </div>
            <p className="text-slate-400 text-sm mb-6 max-w-xs">
              Transforming customer complaints into resolved tickets with AI-powered precision.
            </p>
            {/* Social links */}
            <div className="flex gap-4">
              <a href="#" className="w-9 h-9 bg-slate-800/50 hover:bg-slate-800 rounded-lg flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                <Github className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 bg-slate-800/50 hover:bg-slate-800 rounded-lg flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                <Twitter className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 bg-slate-800/50 hover:bg-slate-800 rounded-lg flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                <Linkedin className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 bg-slate-800/50 hover:bg-slate-800 rounded-lg flex items-center justify-center text-slate-400 hover:text-white transition-colors">
                <Mail className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category} className="footer-column">
              <h4 className="text-white font-semibold mb-4">{category}</h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a 
                      href="#" 
                      className="text-slate-400 hover:text-white text-sm transition-colors hover:translate-x-1 inline-block"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-slate-800/50 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-slate-500 text-sm">
            © 2024 TS-14. Built for Tark Shaastra · Lakshya 2.0
          </p>
          <div className="flex items-center gap-6">
            <span className="text-slate-500 text-sm">Made with</span>
            <span className="text-red-400">♥</span>
            <span className="text-slate-500 text-sm">for the hackathon</span>
          </div>
        </div>
      </div>
    </footer>
  )
}