'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  trend?: string;
  trendUp?: boolean;
  delay?: number;
  className?: string;
}

export function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend, 
  trendUp = true,
  delay = 0,
  className = ''
}: StatCardProps) {
  return (
    <motion.div
      className={`p-6 rounded-2xl ${className}`}
      style={{
        background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
        boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.03)',
      }}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.6, 
        delay,
        ease: [0.22, 1, 0.36, 1] 
      }}
      whileHover={{ 
        y: -4,
        boxShadow: '16px 16px 32px rgba(0, 0, 0, 0.8), -16px -16px 32px rgba(255, 255, 255, 0.03), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 font-medium mb-1 uppercase tracking-wider">{title}</p>
          <h3 
            className="text-3xl font-black text-[#F5F5F5]"
            style={{ 
              fontFamily: "'SF Pro Display', -apple-system, sans-serif",
              fontStretch: '125%',
            }}
          >
            {value}
          </h3>
          
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          
          {trend && (
            <div 
              className={`flex items-center gap-1 mt-3 text-sm font-semibold ${
                trendUp ? 'text-[#22C55E]' : 'text-[#EF4444]'
              }`}
            >
              <div 
                className="flex items-center gap-1 px-2 py-1 rounded-lg"
                style={{
                  background: trendUp ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                }}
              >
                {trendUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                <span>{trend}</span>
              </div>
            </div>
          )}
        </div>
        <div 
          className="p-3 rounded-xl"
          style={{
            background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
            boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
          }}
        >
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

interface MiniChartProps {
  data: number[];
  color?: string;
}

export function MiniChart({ data, color = '#FF6B35' }: MiniChartProps) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  return (
    <div className="flex items-end gap-1 h-12">
      {data.map((value, index) => {
        const height = ((value - min) / range) * 100;
        return (
          <motion.div
            key={index}
            className="w-2 rounded-t-sm"
            style={{ backgroundColor: color }}
            initial={{ height: 0 }}
            animate={{ height: `${Math.max(height, 20)}%` }}
            transition={{ 
              duration: 0.5, 
              delay: index * 0.05,
              ease: [0.22, 1, 0.36, 1]
            }}
          />
        );
      })}
    </div>
  );
}
