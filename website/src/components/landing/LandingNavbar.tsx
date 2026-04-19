'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Menu, X } from 'lucide-react';

const navLinks = [
  { href: '/#stats', label: 'Impact' },
  { href: '/#features', label: 'Features' },
  { href: '/#how-it-works', label: 'How it works' },
  { href: '/#dashboard', label: 'Dashboards' },
  { href: '/#testimonials', label: 'Stories' },
];

export function LandingNavbar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/"
            className="flex items-center gap-3 transition-opacity hover:opacity-90"
            onClick={() => setOpen(false)}
          >
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{
                background: 'linear-gradient(145deg, #FF6B35 0%, #FF4500 50%, #CC3700 100%)',
                boxShadow:
                  '0 2px 0 #CC3700, 0 4px 8px rgba(255, 69, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
              }}
            >
              <AlertCircle className="text-white" size={20} aria-hidden />
            </div>
            <div className="leading-tight">
              <span className="font-valorant text-lg tracking-wide text-white">TS-14</span>
              <p className="text-[11px] text-gray-400">Complaint resolution</p>
            </div>
          </Link>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
            {navLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-white/5 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="hidden items-center gap-2 sm:flex">
            <Link
              href="/login"
              className="rounded-xl px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:text-white"
            >
              Log in
            </Link>
            <Link
              href="/login"
              className="btn-skeuo !py-2 !px-4 text-sm !shadow-none"
            >
              Get started
            </Link>
          </div>

          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 sm:hidden"
            aria-expanded={open}
            aria-controls="landing-mobile-nav"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      <AnimatePresence>
        {open && (
          <motion.div
            id="landing-mobile-nav"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed left-0 right-0 top-16 z-40 overflow-hidden border-b border-white/10 bg-black/95 backdrop-blur-md sm:hidden"
          >
            <nav className="flex flex-col gap-1 px-4 py-4" aria-label="Mobile primary">
              {navLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-3 py-3 text-sm font-medium text-gray-200 hover:bg-white/5"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
              <div className="mt-2 flex flex-col gap-2 border-t border-white/10 pt-4">
                <Link
                  href="/login"
                  className="rounded-xl px-3 py-3 text-center text-sm font-medium text-gray-300 hover:bg-white/5"
                  onClick={() => setOpen(false)}
                >
                  Log in
                </Link>
                <Link
                  href="/login"
                  className="btn-skeuo text-center text-sm !shadow-none"
                  onClick={() => setOpen(false)}
                >
                  Get started
                </Link>
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
