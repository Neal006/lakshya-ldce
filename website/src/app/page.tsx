'use client';

import {
  LandingNavbar,
  HeroSection,
  StatsSection,
  BusinessMetricsSection,
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
      <LandingNavbar />
      <HeroSection />
      <StatsSection />
      <BusinessMetricsSection />
      <HowItWorksSection />
      <FeaturesSection />
      <DashboardPreviewSection />
      <TestimonialsSection />
      <CTASection />
      <Footer />
    </main>
  );
}
