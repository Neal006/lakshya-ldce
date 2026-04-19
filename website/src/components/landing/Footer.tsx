'use client';

import { Mail, Globe, MessageCircle, Users } from 'lucide-react';

const footerLinks = {
  Product: ['Features', 'Pricing', 'API Docs', 'Changelog', 'Roadmap'],
  Company: ['About', 'Blog', 'Careers', 'Press', 'Partners'],
  Resources: ['Documentation', 'Guides', 'Support', 'Status', 'Community'],
  Legal: ['Privacy', 'Terms', 'Security', 'Cookies', 'Compliance'],
};

const socialLinks = [
  { icon: Globe, href: '#', label: 'Website' },
  { icon: MessageCircle, href: '#', label: 'Discord' },
  { icon: Users, href: '#', label: 'Team' },
  { icon: Mail, href: '#', label: 'Email' },
];

export function Footer() {
  return (
    <footer className="border-t border-white/5 bg-black">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-6 gap-12">
          {/* Brand column */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF6B35] to-[#E55A2B] flex items-center justify-center">
                <span className="font-valorant text-white text-lg">TS</span>
              </div>
              <div>
                <span className="font-valorant text-xl text-white">TS-14</span>
              </div>
            </div>
            <p className="text-sm text-gray-500 mb-4">AI Complaint Resolution</p>
            <p className="text-gray-400 text-sm mb-6 max-w-xs leading-relaxed">
              Transform customer complaints into resolved tickets with AI-powered precision.
            </p>
            
            {/* Social icons */}
            <div className="flex gap-3">
              {socialLinks.map((social, i) => (
                <a
                  key={i}
                  href={social.href}
                  className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:border-[#FF6B35]/30 transition-colors"
                  aria-label={social.label}
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          <div className="lg:col-span-4 grid grid-cols-2 md:grid-cols-4 gap-8">
            {Object.entries(footerLinks).map(([category, links]) => (
              <div key={category}>
                <h4 className="font-valorant text-white text-sm mb-4">{category}</h4>
                <ul className="space-y-3">
                  {links.map((link) => (
                    <li key={link}>
                      <a 
                        href="#" 
                        className="text-gray-400 text-sm hover:text-[#FF6B35] transition-colors"
                      >
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">
            © 2024 TS-14. Built for Tark Shaastra · Lakshya 2.0
          </p>
          <p className="text-gray-500 text-sm">
            Made with ♥ for the hackathon
          </p>
        </div>
      </div>
    </footer>
  );
}
