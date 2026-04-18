'use client'

import { Github, Twitter, Linkedin, Mail } from 'lucide-react'

const footerLinks = {
  Product: ['Features', 'Pricing', 'Integrations', 'Changelog', 'Roadmap'],
  Company: ['About', 'Blog', 'Careers', 'Press', 'Partners'],
  Resources: ['Documentation', 'API Reference', 'Guides', 'Support', 'Community'],
  Legal: ['Privacy', 'Terms', 'Security', 'Cookies', 'Licenses']
}

export const Footer = () => {
  return (
    <footer className="relative py-16 px-4 sm:px-6 lg:px-8 bg-black border-t border-white/10">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 lg:gap-12">
          {/* Brand column */}
          <div className="col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-saffron rounded-xl flex items-center justify-center border-2 border-saffron-dark shadow-lg">
                <span className="text-black font-bold text-lg font-oswald">TS</span>
              </div>
              <div>
                <span className="text-white font-bold text-xl font-oswald uppercase tracking-wide">TS-14</span>
                <p className="text-xs text-white/40 font-inter">AI Complaint Resolution</p>
              </div>
            </div>
            <p className="text-white/50 text-sm mb-6 max-w-xs font-inter">
              Transforming customer complaints into resolved tickets with AI-powered precision.
            </p>
            {/* Social links */}
            <div className="flex gap-4">
              <a href="#" className="w-9 h-9 bg-white/5 hover:bg-saffron/20 rounded-lg flex items-center justify-center text-white/50 hover:text-saffron transition-colors border border-white/10 hover:border-saffron/30">
                <Github className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 bg-white/5 hover:bg-saffron/20 rounded-lg flex items-center justify-center text-white/50 hover:text-saffron transition-colors border border-white/10 hover:border-saffron/30">
                <Twitter className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 bg-white/5 hover:bg-saffron/20 rounded-lg flex items-center justify-center text-white/50 hover:text-saffron transition-colors border border-white/10 hover:border-saffron/30">
                <Linkedin className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 bg-white/5 hover:bg-saffron/20 rounded-lg flex items-center justify-center text-white/50 hover:text-saffron transition-colors border border-white/10 hover:border-saffron/30">
                <Mail className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-white font-semibold mb-4 font-oswald uppercase tracking-wide">{category}</h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a 
                      href="#" 
                      className="text-white/50 hover:text-saffron text-sm transition-colors inline-block font-inter"
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
        <div className="mt-16 pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-white/40 text-sm font-inter">
            © 2024 TS-14. Built for Tark Shaastra · Lakshya 2.0
          </p>
          <div className="flex items-center gap-2 text-white/40 text-sm font-inter">
            <span>Made with</span>
            <span className="text-saffron">♥</span>
            <span>for the hackathon</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
