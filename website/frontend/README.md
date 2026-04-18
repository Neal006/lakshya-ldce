# TS-14 Frontend

AI-powered complaint resolution landing page built with Next.js 14, GSAP, and Tailwind CSS.

## Features

- ⚡ **Lightning-fast animations** powered by GSAP
- 📜 **Smooth scrolling** with Lenis
- 🎨 **Stunning visual effects** including:
  - Split text reveals
  - Horizontal scroll sections
  - 3D tilt effects on cards
  - Parallax scrolling
  - Infinite marquees
  - Counter animations
  - Mouse-following elements
- 📱 **Fully responsive** design
- 🌙 **Dark mode** optimized
- ♿ **Accessibility** compliant with reduced motion support

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: GSAP + ScrollTrigger + @gsap/react
- **Smooth Scroll**: Lenis (@studio-freight/lenis)
- **Icons**: Lucide React

## Getting Started

### 1. Install Dependencies

```bash
cd website/frontend
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the landing page.

### 3. Build for Production

```bash
npm run build
```

Static files will be generated in the `dist` folder.

## Project Structure

```
frontend/
├── app/
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout with SmoothScroll
│   └── page.tsx             # Landing page
├── components/
│   ├── landing/             # Landing page sections
│   │   ├── HeroSection.tsx
│   │   ├── StatsSection.tsx
│   │   ├── HowItWorksSection.tsx
│   │   ├── FeaturesSection.tsx
│   │   ├── DashboardPreviewSection.tsx
│   │   ├── TestimonialsSection.tsx
│   │   ├── CTASection.tsx
│   │   └── Footer.tsx
│   └── ui/
│       └── SmoothScroll.tsx # Lenis integration
├── hooks/                   # Custom React hooks
├── lib/
│   └── utils.ts             # Utility functions
└── public/                  # Static assets
```

## Animation Highlights

### Hero Section
- Split text reveal with 3D rotation
- Floating UI elements with mouse parallax
- Magnetic cursor-following effect
- Dashboard mockup 3D entrance

### Stats Section
- Animated counters with easing
- 3D flip card reveals
- Pulsing icons
- Hover gradient effects

### How It Works
- Horizontal scroll with pinning
- Progress bar tracking
- Snap-to-section navigation
- Individual step animations

### Features Grid
- Bento grid layout
- 3D tilt on hover
- Gradient overlay animations
- Staggered reveals

### Dashboard Preview
- Parallax depth effect
- Continuous floating animation
- Layered card stacking

### Testimonials
- Infinite marquee
- Scroll velocity affects speed
- Seamless looping

### CTA Section
- Pulsing button glow
- Floating particles
- Animated gradient background

## Performance Optimizations

- Transform-based animations (GPU accelerated)
- `will-change` hints on animated elements
- ScrollTrigger batching for lists
- Automatic cleanup with useGSAP hook
- Reduced motion support via `prefers-reduced-motion`

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT - Built for Tark Shaastra · Lakshya 2.0 Hackathon