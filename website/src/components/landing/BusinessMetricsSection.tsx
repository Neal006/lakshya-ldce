'use client';

import { useRef, useEffect, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { 
  Clock, 
  Target, 
  Bot, 
  TrendingUp, 
  DollarSign, 
  Users, 
  Headphones,
  Heart,
  ArrowRight,
  Zap,
  BarChart3,
  Activity
} from 'lucide-react';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

// Animated counter hook
function useCountUp(end: number, duration: number = 2, start: number = 0) {
  const [count, setCount] = useState(start);
  const countRef = useRef(start);
  const isInView = useRef(false);

  useEffect(() => {
    if (!isInView.current) return;
    
    const startTime = Date.now();
    const animate = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / (duration * 1000), 1);
      const easeProgress = 1 - Math.pow(1 - progress, 3); // easeOut cubic
      countRef.current = start + (end - start) * easeProgress;
      setCount(countRef.current);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [end, duration, start]);

  return { count, setIsInView: (value: boolean) => { isInView.current = value; } };
}

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  color: string;
  delay: number;
  formula?: string;
  description: string;
}

function MetricCard({ title, value, subtitle, icon, color, delay, formula, description }: MetricCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(cardRef, { once: true, margin: "-100px" });

  useEffect(() => {
    if (!cardRef.current || !isInView) return;

    const ctx = gsap.context(() => {
      // Card entrance animation
      gsap.fromTo(cardRef.current,
        { 
          opacity: 0, 
          y: 60,
          rotateX: -15,
          scale: 0.95
        },
        { 
          opacity: 1, 
          y: 0, 
          rotateX: 0,
          scale: 1,
          duration: 0.8,
          delay: delay * 0.15,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: cardRef.current,
            start: 'top 85%',
            toggleActions: 'play none none none',
          }
        }
      );

      // Icon pulse animation
      const iconElement = cardRef.current?.querySelector('.metric-icon');
      if (iconElement) {
        gsap.to(iconElement,
          {
            scale: 1.1,
            duration: 1.5,
            repeat: -1,
            yoyo: true,
            ease: 'power1.inOut',
            delay: delay * 0.1 + 1
          }
        );
      }
    }, cardRef);

    return () => ctx.revert();
  }, [isInView, delay]);

  return (
    <div
      ref={cardRef}
      className="relative group"
      style={{ perspective: '1000px' }}
    >
      <div
        className="relative p-6 rounded-2xl overflow-hidden transition-all duration-300"
        style={{
          background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
          boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.03)',
          transformStyle: 'preserve-3d',
        }}
      >
        {/* Glow effect on hover */}
        <div
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{
            background: `radial-gradient(circle at 50% 0%, ${color}15 0%, transparent 70%)`,
          }}
        />

        {/* Top accent line */}
        <div
          className="absolute top-0 left-0 right-0 h-0.5"
          style={{
            background: `linear-gradient(90deg, transparent 0%, ${color} 50%, transparent 100%)`,
          }}
        />

        {/* Icon */}
        <div
          className="metric-icon w-12 h-12 rounded-xl flex items-center justify-center mb-4"
          style={{
            background: `linear-gradient(145deg, ${color}30 0%, ${color}10 100%)`,
            boxShadow: `0 4px 0 ${color}40, inset 0 1px 0 rgba(255,255,255,0.1)`,
          }}
        >
          {icon}
        </div>

        {/* Title */}
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">
          {title}
        </h3>

        {/* Value with animated gradient */}
        <div
          className="text-3xl font-black mb-1"
          style={{
            background: `linear-gradient(135deg, #fff 0%, ${color} 100%)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          {value}
        </div>

        {/* Subtitle */}
        <p className="text-sm text-gray-500 mb-3">{subtitle}</p>

        {/* Formula tag */}
        {formula && (
          <div
            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-mono"
            style={{
              background: `${color}15`,
              color: color,
              border: `1px solid ${color}30`,
            }}
          >
            <Activity size={10} />
            {formula}
          </div>
        )}

        {/* Description tooltip on hover */}
        <div className="mt-4 pt-4 border-t border-white/5 opacity-60 group-hover:opacity-100 transition-opacity">
          <p className="text-xs text-gray-400 leading-relaxed">{description}</p>
        </div>
      </div>
    </div>
  );
}

// Financial Impact Calculator
function FinancialCalculator() {
  const [ticketsPerMonth, setTicketsPerMonth] = useState(1000);
  const calculatorRef = useRef<HTMLDivElement>(null);
  
  const humanCost = ticketsPerMonth * 45; // $45 per ticket human-handled
  const aiCost = ticketsPerMonth * 12; // $12 per ticket with AI
  const savings = humanCost - aiCost;
  const savingsPercent = Math.round((savings / humanCost) * 100);

  useEffect(() => {
    if (!calculatorRef.current) return;

    const ctx = gsap.context(() => {
      gsap.fromTo('.calculator-item',
        { opacity: 0, x: -30 },
        {
          opacity: 1,
          x: 0,
          duration: 0.6,
          stagger: 0.1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: calculatorRef.current,
            start: 'top 80%',
          }
        }
      );
    }, calculatorRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={calculatorRef} className="space-y-6">
      <div className="calculator-item">
        <label className="text-sm text-gray-400 mb-2 block">Monthly Ticket Volume</label>
        <input
          type="range"
          min="100"
          max="10000"
          step="100"
          value={ticketsPerMonth}
          onChange={(e) => setTicketsPerMonth(Number(e.target.value))}
          className="w-full h-2 rounded-lg appearance-none cursor-pointer"
          style={{
            background: 'linear-gradient(90deg, #FF6B35 0%, #CC3700 100%)',
          }}
        />
        <div className="flex justify-between mt-2">
          <span className="text-xs text-gray-500">100</span>
          <span className="text-sm font-bold text-[#FF6B35]">{ticketsPerMonth.toLocaleString()} tickets</span>
          <span className="text-xs text-gray-500">10,000</span>
        </div>
      </div>

      <div className="calculator-item grid grid-cols-2 gap-4">
        <div
          className="p-4 rounded-xl"
          style={{
            background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
            boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
          }}
        >
          <p className="text-xs text-gray-400 mb-1">Human-Only Cost</p>
          <p className="text-xl font-bold text-gray-300">${humanCost.toLocaleString()}</p>
        </div>
        <div
          className="p-4 rounded-xl"
          style={{
            background: 'linear-gradient(165deg, #22C55E20 0%, #16A34A20 100%)',
            boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(34, 197, 94, 0.2)',
          }}
        >
          <p className="text-xs text-green-400 mb-1">With SOLV.ai</p>
          <p className="text-xl font-bold text-green-400">${aiCost.toLocaleString()}</p>
        </div>
      </div>

      <motion.div
        className="calculator-item p-4 rounded-xl"
        style={{
          background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
          boxShadow: '0 4px 0 #B8441F, 0 8px 16px rgba(255, 107, 53, 0.3)',
        }}
        whileHover={{ y: -2 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-white/80">Monthly Savings</p>
            <p className="text-2xl font-black text-white">${savings.toLocaleString()}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-black text-white">{savingsPercent}%</p>
            <p className="text-xs text-white/70">Cost Reduction</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export function BusinessMetricsSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!titleRef.current) return;

    const ctx = gsap.context(() => {
      // Title animation
      gsap.fromTo('.metrics-title-line',
        { opacity: 0, y: 60, rotateX: -30 },
        {
          opacity: 1,
          y: 0,
          rotateX: 0,
          duration: 0.9,
          stagger: 0.15,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: titleRef.current,
            start: 'top 80%',
          }
        }
      );

      // Badge animation
      gsap.fromTo('.metrics-badge',
        { opacity: 0, scale: 0.8 },
        {
          opacity: 1,
          scale: 1,
          duration: 0.6,
          delay: 0.3,
          ease: 'back.out(1.7)',
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const kpiMetrics = [
    {
      title: 'MTTR',
      value: '2.4h',
      subtitle: 'Mean Time To Resolution',
      icon: <Clock size={24} style={{ color: '#3B82F6' }} />,
      color: '#3B82F6',
      formula: 'Avg(T_resolved - T_created)',
      description: 'Average time from complaint creation to resolution. Industry benchmark: 24-48 hours.',
    },
    {
      title: 'FCR',
      value: '89%',
      subtitle: 'First Contact Resolution',
      icon: <Target size={24} style={{ color: '#22C55E' }} />,
      color: '#22C55E',
      formula: 'Resolved in 1 Touch / Total',
      description: 'Percentage of issues resolved on first contact without escalation or callbacks.',
    },
    {
      title: 'Automation Rate',
      value: '73%',
      subtitle: 'AI-Handled Interactions',
      icon: <Bot size={24} style={{ color: '#8B5CF6' }} />,
      color: '#8B5CF6',
      formula: 'AI Actions / Total Actions',
      description: 'Portion of status changes, classifications, and responses handled by AI agents.',
    },
    {
      title: 'CSAT Score',
      value: '4.7/5',
      subtitle: 'Customer Satisfaction',
      icon: <Heart size={24} style={{ color: '#FF6B35' }} />,
      color: '#FF6B35',
      formula: 'ΣSentiment / N',
      description: 'Aggregated sentiment analysis from customer responses using LLM scoring.',
    },
  ];

  const financialMetrics = [
    {
      title: 'Cost Per Ticket',
      value: '$12.40',
      subtitle: 'Blended AI + Human Cost',
      icon: <DollarSign size={24} style={{ color: '#10B981' }} />,
      color: '#10B981',
      formula: '(Hours × $20) + Tokens',
      description: 'Total cost including AI processing and human oversight time. vs $45 human-only.',
    },
    {
      title: 'TCO Savings',
      value: '$127K',
      subtitle: 'Annual Cost Avoidance',
      icon: <TrendingUp size={24} style={{ color: '#F59E0B' }} />,
      color: '#F59E0B',
      formula: 'Avoided Headcount × $3,375',
      description: 'Equivalent to 3.8 avoided FTE hires based on ticket volume scaling.',
    },
    {
      title: 'Deflection Rate',
      value: '41%',
      subtitle: 'Self-Service Resolution',
      icon: <Headphones size={24} style={{ color: '#EC4899' }} />,
      color: '#EC4899',
      formula: 'AI Sessions / Total Sessions',
      description: 'Issues resolved via AI without ever creating a formal complaint ticket.',
    },
    {
      title: 'Sentiment Recovery',
      value: '+0.68',
      subtitle: 'SRS Score Average',
      icon: <Activity size={24} style={{ color: '#06B6D4' }} />,
      color: '#06B6D4',
      formula: 'Final - Initial Sentiment',
      description: 'Average sentiment improvement from complaint creation to resolution.',
    },
  ];

  return (
    <section
      ref={sectionRef}
      id="business-metrics"
      className="py-24 px-4 sm:px-6 lg:px-8 relative scroll-mt-24 overflow-hidden"
    >
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 rounded-full blur-3xl opacity-20"
          style={{ background: 'radial-gradient(circle, #FF6B35 0%, transparent 70%)' }}
        />
        <div
          className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 rounded-full blur-3xl opacity-20"
          style={{ background: 'radial-gradient(circle, #3B82F6 0%, transparent 70%)' }}
        />
      </div>

      <div className="max-w-7xl mx-auto relative">
        {/* Section Header */}
        <div ref={titleRef} className="text-center mb-16" style={{ perspective: '1000px' }}>
          <motion.span
            className="metrics-badge inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold mb-6"
            style={{
              background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
              color: '#000',
              boxShadow: '0 4px 0 #B8441F, 0 8px 16px rgba(255, 107, 53, 0.3)',
            }}
          >
            <Zap size={16} className="text-black" />
            B2B Intelligence
          </motion.span>

          <h2 className="metrics-title-line font-valorant text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-white mb-4">
            Scale Globally with
          </h2>
          <h2
            className="metrics-title-line font-valorant text-3xl sm:text-4xl md:text-5xl lg:text-6xl mb-6"
            style={{
              background: 'linear-gradient(135deg, #FF6B35 0%, #FF8C5A 50%, #3B82F6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Data-Driven Insights
          </h2>
          <p className="metrics-title-line text-lg sm:text-xl text-gray-400 max-w-3xl mx-auto">
            Our solution doesn't just simplify technology—it transforms your customer service 
            into a competitive advantage with real-time business intelligence.
          </p>
        </div>

        {/* KPI Metrics Grid */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div
              className="p-2 rounded-lg"
              style={{
                background: 'linear-gradient(145deg, #3B82F6 0%, #1D4ED8 100%)',
                boxShadow: '0 2px 0 #1E40AF',
              }}
            >
              <BarChart3 size={20} className="text-white" />
            </div>
            <h3 className="text-xl font-bold text-white">Key Performance Indicators</h3>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {kpiMetrics.map((metric, i) => (
              <MetricCard key={metric.title} {...metric} delay={i} />
            ))}
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-12">
          {/* Financial Metrics */}
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-lg"
                style={{
                  background: 'linear-gradient(145deg, #10B981 0%, #15803D 100%)',
                  boxShadow: '0 2px 0 #166534',
                }}
              >
                <DollarSign size={20} className="text-white" />
              </div>
              <h3 className="text-xl font-bold text-white">Financial Impact</h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {financialMetrics.map((metric, i) => (
                <MetricCard key={metric.title} {...metric} delay={i + 4} />
              ))}
            </div>
          </div>

          {/* ROI Calculator */}
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-lg"
                style={{
                  background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
                  boxShadow: '0 2px 0 #B8441F',
                }}
              >
                <TrendingUp size={20} className="text-white" />
              </div>
              <h3 className="text-xl font-bold text-white">ROI Calculator</h3>
            </div>
            
            <div
              className="p-6 rounded-2xl"
              style={{
                background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.03)',
              }}
            >
              <p className="text-sm text-gray-400 mb-6">
                See how much you can save by switching to SOLV.ai. Adjust your monthly ticket volume to calculate your potential ROI.
              </p>
              <FinancialCalculator />
            </div>
          </div>
        </div>

        {/* CTA */}
        <motion.div
          className="mt-16 text-center"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <motion.a
            href="#demo"
            className="inline-flex items-center gap-3 px-8 py-4 rounded-xl font-bold text-lg"
            style={{
              background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
              color: '#000',
              boxShadow: '0 6px 0 #B8441F, 0 12px 24px rgba(255, 107, 53, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
            }}
            whileHover={{
              y: -2,
              boxShadow: '0 8px 0 #B8441F, 0 16px 32px rgba(255, 107, 53, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
            }}
            whileTap={{
              y: 6,
              boxShadow: '0 0 0 #B8441F, 0 4px 12px rgba(255, 107, 53, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)',
            }}
          >
            Get Detailed Business Report
            <ArrowRight size={20} />
          </motion.a>
          <p className="mt-4 text-sm text-gray-500">
            Includes custom metrics based on your industry and ticket volume
          </p>
        </motion.div>
      </div>
    </section>
  );
}
