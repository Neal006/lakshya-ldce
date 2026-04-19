'use client';

import { useRef, useEffect } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
  Area,
  AreaChart,
} from 'recharts';
import { Card } from '@/components/ui';

// Custom tooltip with dark theme styling
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1A1A1A] border border-white/10 rounded-lg p-3 text-sm shadow-xl">
        <p className="font-semibold mb-1 text-white">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Dark theme chart colors
const CHART_COLORS = {
  primary: '#FF6B35',
  secondary: '#FF8C5A',
  grid: 'rgba(255, 255, 255, 0.05)',
  text: '#B3B3B3',
  high: '#FF3B30',
  medium: '#007AFF',
  low: '#34C759',
};

interface TrendChartProps {
  data: any[];
  title?: string;
}

export function TrendChart({ data, title }: TrendChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const ctx = gsap.context(() => {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 85%',
          toggleActions: 'play none none none',
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef}>
      <Card>
        {title && <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorComplaints" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.4} />
                <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: CHART_COLORS.text }} />
            <YAxis tick={{ fontSize: 12, fill: CHART_COLORS.text }} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="complaints"
              stroke={CHART_COLORS.primary}
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorComplaints)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

interface CategoryChartProps {
  data: any[];
  title?: string;
}

export function CategoryChart({ data, title }: CategoryChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const ctx = gsap.context(() => {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.8,
        delay: 0.1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 85%',
          toggleActions: 'play none none none',
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef}>
      <Card>
        {title && <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              formatter={(value) => <span style={{ color: '#fff' }}>{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

interface PriorityChartProps {
  data: any[];
  title?: string;
}

export function PriorityChart({ data, title }: PriorityChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const ctx = gsap.context(() => {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.8,
        delay: 0.2,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 85%',
          toggleActions: 'play none none none',
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef}>
      <Card>
        {title && <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
            <XAxis type="number" tick={{ fontSize: 12, fill: CHART_COLORS.text }} />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: CHART_COLORS.text }} width={80} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[0, 8, 8, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

interface ProductChartProps {
  data: any[];
  title?: string;
}

export function ProductChart({ data, title }: ProductChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const ctx = gsap.context(() => {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 85%',
          toggleActions: 'play none none none',
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef}>
      <Card>
        {title && <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: CHART_COLORS.text }} angle={-45} textAnchor="end" height={80} />
            <YAxis tick={{ fontSize: 12, fill: CHART_COLORS.text }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="total_complaints" fill={CHART_COLORS.primary} radius={[8, 8, 0, 0]} />
            <Bar dataKey="high_priority" fill={CHART_COLORS.high} radius={[8, 8, 0, 0]} />
            <Legend 
              formatter={(value) => <span style={{ color: '#fff' }}>{value}</span>}
            />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

interface MultiLineChartProps {
  data: any[];
  title?: string;
}

export function MultiLineChart({ data, title }: MultiLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const ctx = gsap.context(() => {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 85%',
          toggleActions: 'play none none none',
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef}>
      <Card>
        {title && <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: CHART_COLORS.text }} />
            <YAxis tick={{ fontSize: 12, fill: CHART_COLORS.text }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend formatter={(value) => <span style={{ color: '#fff' }}>{value}</span>} />
            <Line type="monotone" dataKey="high" stroke={CHART_COLORS.high} strokeWidth={3} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="medium" stroke={CHART_COLORS.medium} strokeWidth={3} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="low" stroke={CHART_COLORS.low} strokeWidth={3} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
