'use client';

import {
  HeroSection,
  StatsSection,
  HowItWorksSection,
  FeaturesSection,
  DashboardPreviewSection,
  TestimonialsSection,
  CTASection,
  Footer,
} from '@/components/landing';

export default function LandingPage() {
  return (
    <main className="relative overflow-hidden bg-black">
      <HeroSection />
      <StatsSection />
      <HowItWorksSection />
      <FeaturesSection />
      <DashboardPreviewSection />
      <TestimonialsSection />
      <CTASection />
      <Footer />
    </main>
  );
}
