'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  trend?: 'up' | 'down';
  trendValue?: string;
  delay?: number;
}

export function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend, 
  trendValue,
  delay = 0 
}: StatCardProps) {
  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.6, 
        delay,
        ease: [0.22, 1, 0.36, 1] 
      }}
      whileHover={{ y: -4 }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 font-medium mb-1 uppercase tracking-wider">{title}</p>
          <h3 className="text-3xl font-black text-white heading-fortnite" style={{ fontSize: '2rem' }}>{value}</h3>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend && trendValue && (
            <div className={`flex items-center gap-1 mt-2 text-sm font-semibold ${
              trend === 'up' ? 'text-[#34C759]' : 'text-[#FF3B30]'
            }`}>
              {trend === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>{trendValue}</span>
            </div>
          )}
        </div>
        <div className="p-3 rounded-xl bg-[#1A1A1A] border border-white/10 shadow-lg">
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
