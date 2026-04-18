import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { SmoothScroll } from '@/components/ui/SmoothScroll'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TS-14 | AI Complaint Resolution Engine',
  description: 'AI-powered complaint classification and resolution for Tark Shaastra · Lakshya 2.0',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <SmoothScroll>
          {children}
        </SmoothScroll>
      </body>
    </html>
  )
}