'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { apiClient } from '@/lib/api-client';
import { StatCard } from '@/components/dashboard/StatCard';
import {
  CategoryChart,
  PriorityChart,
  MultiLineChart,
  TrendChart,
} from '@/components/charts';
import {
  Activity,
  Clock,
  Target,
  BarChart3,
  Radio,
  Loader2,
  FileDown,
} from 'lucide-react';
import { generateOperationalReportPDF, captureChart } from '@/lib/generate-report-pdf';
import type { ChartImages } from '@/lib/generate-report-pdf';

const catColors: Record<string, string> = {
  Product: '#FF6B35',
  Packaging: '#8B5CF6',
  Trade: '#3B82F6',
};

const priorityColors: Record<string, string> = {
  High: '#FF3B30',
  Medium: '#007AFF',
  Low: '#34C759',
};

export default function OperationalDashboardPage() {
  const [dash, setDash] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [sla, setSla] = useState<{ priority: string; response_hours: number; resolve_hours: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [liveHint, setLiveHint] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const multiLineChartRef = useRef<HTMLDivElement>(null);
  const categoryChartRef = useRef<HTMLDivElement>(null);
  const priorityChartRef = useRef<HTMLDivElement>(null);
  const trendChartRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [dRes, tRes, sRes] = await Promise.allSettled([
        apiClient.getDashboardAnalytics(),
        apiClient.getTrends(),
        apiClient.getSLAConfig(),
      ]);
      if (dRes.status === 'fulfilled') setDash(dRes.value);
      else console.error('Dashboard analytics failed:', dRes.reason);
      if (tRes.status === 'fulfilled') setTrends(tRes.value);
      else console.error('Trends failed:', tRes.reason);
      if (sRes.status === 'fulfilled') setSla(sRes.value.sla_configs || []);
      else {
        console.error('SLA config failed:', sRes.reason);
        setSla([]);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const captureCharts = async (): Promise<ChartImages> => {
    const [multiLineChart, categoryChart, priorityChart, trendChart] = await Promise.all([
      captureChart(multiLineChartRef.current),
      captureChart(categoryChartRef.current),
      captureChart(priorityChartRef.current),
      captureChart(trendChartRef.current),
    ])
    return { multiLineChart, categoryChart, priorityChart, trendChart }
  }

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const url = `${window.location.origin}/api/sse/complaints`;
    const es = new EventSource(url);
    esRef.current = es;
    es.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'new_complaint') {
          setLiveHint('New complaint received — refreshing metrics.');
          load();
        }
        if (msg.type === 'high_priority_alert') {
          setLiveHint('High priority alert — check queue.');
          load();
        }
      } catch {
        /* ignore */
      }
    };
    es.onerror = () => {
      /* browser will retry */
    };
    return () => {
      es.close();
      esRef.current = null;
    };
  }, [load]);

  useEffect(() => {
    if (!liveHint) return;
    const t = setTimeout(() => setLiveHint(null), 5000);
    return () => clearTimeout(t);
  }, [liveHint]);

  const summary = dash?.summary;
  const categoryData =
    dash?.by_category?.map((c: { name: string; value: number }) => ({
      name: c.name,
      value: c.value,
      color: catColors[c.name] || '#888',
    })) || [];

  const priorityData =
    dash?.by_priority?.map((c: { name: string; value: number }) => ({
      name: c.name,
      value: c.value,
      color: priorityColors[c.name] || '#888',
    })) || [];

  if (loading && !dash) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-gray-500">
        <Loader2 className="animate-spin w-8 h-8" />
      </div>
    );
  }

  const handleGetPDF = async () => {
    const reportData = {
      summary,
      trends: trends?.daily,
      category_data: categoryData,
      priority_data: priorityData,
    }
    const charts = await captureCharts()
    generateOperationalReportPDF(reportData, charts)
  }

  return (
    <div className="pb-12 max-w-[1920px] mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[#F5F5F5] flex items-center gap-3">
            <BarChart3 className="text-[#FF6B35]" />
            Operations command center
          </h1>
          <p className="text-gray-400 mt-1">
            Live complaint distribution, SLA compliance, and resolution time for operational oversight.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <motion.button
            type="button"
            onClick={handleGetPDF}
            className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg font-medium"
            style={{
              background: 'linear-gradient(145deg, #22C55E 0%, #16A34A 100%)',
              color: '#fff',
              boxShadow: '0 3px 0 #15803D, 0 6px 12px rgba(34, 197, 94, 0.25)',
            }}
            whileHover={{ y: -1 }}
            whileTap={{ y: 2 }}
          >
            <FileDown className="w-4 h-4" />
            Get PDF
          </motion.button>
          <button
            type="button"
            onClick={() => load()}
            className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5"
          >
            Refresh metrics
          </button>
          <div className="flex items-center gap-2 text-xs text-emerald-400/90">
            <Radio className="w-4 h-4 animate-pulse" />
            Live updates (SSE)
          </div>
        </div>
      </div>

      {liveHint && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-orange-500/30 bg-orange-500/10 text-orange-200 px-4 py-2 text-sm"
        >
          {liveHint}
        </motion.div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          title="Total complaints"
          value={summary?.total_complaints ?? '—'}
          icon={<Activity className="text-[#FF6B35]" size={22} />}
          delay={0}
        />
        <StatCard
          title="Today"
          value={summary?.today_complaints ?? '—'}
          subtitle="New today"
          icon={<BarChart3 className="text-blue-400" size={22} />}
          delay={0.05}
        />
        <StatCard
          title="SLA compliance"
          value={`${summary?.sla_compliance_percent ?? 0}%`}
          subtitle="Resolved within priority window"
          icon={<Target className="text-emerald-400" size={22} />}
          delay={0.1}
        />
        <StatCard
          title="Avg resolution (h)"
          value={
            summary?.avg_resolution_time_hours != null &&
            summary.avg_resolution_time_hours > 0
              ? summary.avg_resolution_time_hours
              : '—'
          }
          subtitle="From create → resolved"
          icon={<Clock className="text-amber-400" size={22} />}
          delay={0.15}
        />
      </div>

      <div
        ref={multiLineChartRef}
        className="rounded-2xl p-6"
        style={{
          background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
          border: '1px solid rgba(255, 255, 255, 0.03)',
        }}
      >
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Priority trend (7 days)
        </h2>
        {trends?.daily && <MultiLineChart data={trends.daily} />}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div
          ref={categoryChartRef}
          className="rounded-2xl p-6"
          style={{
            background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
          }}
        >
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
            By category
          </h2>
          {categoryData.length > 0 && <CategoryChart data={categoryData} />}
        </div>
        <div
          ref={priorityChartRef}
          className="rounded-2xl p-6"
          style={{
            background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
          }}
        >
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
            By priority
          </h2>
          {priorityData.length > 0 && <PriorityChart data={priorityData} />}
        </div>
      </div>

      <div
        ref={trendChartRef}
        className="rounded-2xl p-6"
        style={{
          background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
          border: '1px solid rgba(255, 255, 255, 0.03)',
        }}
      >
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Daily volume
        </h2>
        {trends?.daily && <TrendChart data={trends.daily} />}
      </div>

      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
          border: '1px solid rgba(255, 255, 255, 0.03)',
        }}
      >
        <div className="px-6 py-4 border-b border-white/5 text-sm font-semibold text-gray-400 uppercase tracking-wider">
          SLA targets (hours)
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-white/5">
                <th className="py-3 px-6">Priority</th>
                <th className="py-3 px-6">Response</th>
                <th className="py-3 px-6">Resolve</th>
              </tr>
            </thead>
            <tbody>
              {sla.map((row) => (
                <tr key={row.priority} className="border-b border-white/5 text-[#F5F5F5]">
                  <td className="py-3 px-6 font-medium">{row.priority}</td>
                  <td className="py-3 px-6">{row.response_hours}h</td>
                  <td className="py-3 px-6">{row.resolve_hours}h</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}