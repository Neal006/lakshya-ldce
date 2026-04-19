'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { apiClient } from '@/lib/api-client';
import {
  TrendChart,
  CategoryChart,
  MultiLineChart,
} from '@/components/charts';
import {
  AlertTriangle,
  ShieldCheck,
  Loader2,
  BarChart3,
} from 'lucide-react';

export default function QualityAssurancePage() {
  const [trends, setTrends] = useState<any>(null);
  const [qa, setQa] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, q] = await Promise.all([
        apiClient.getTrends(),
        apiClient.getQAInsights(),
      ]);
      setTrends(t);
      setQa(q);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const catColors: Record<string, string> = {
    Product: '#FF6B35',
    Packaging: '#8B5CF6',
    Trade: '#3B82F6',
  };

  const categoryChartData =
    qa?.category_balance?.map((c: { name: string; value: number }) => ({
      name: c.name,
      value: c.value,
      color: catColors[c.name] || '#888',
    })) || [];

  return (
    <div className="pb-12 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-[#F5F5F5] flex items-center gap-3">
          <ShieldCheck className="text-[#FF6B35]" />
          Quality assurance
        </h1>
        <p className="text-gray-400 mt-1">
          Category mix, complaint trends, and recurring product signals for classification and resolution quality.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-24 text-gray-500">
          <Loader2 className="animate-spin w-8 h-8" />
        </div>
      ) : (
        <>
          {qa?.recurring_alerts?.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-[#F5F5F5] flex items-center gap-2">
                <AlertTriangle className="text-amber-400" />
                Recurring issue warnings
              </h2>
              <div className="grid gap-3">
                {qa.recurring_alerts.map(
                  (a: {
                    product_id: string;
                    name: string;
                    severity: string;
                    message: string;
                    total: number;
                  }) => (
                    <motion.div
                      key={a.product_id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`rounded-xl px-4 py-3 border ${
                        a.severity === 'critical'
                          ? 'border-red-500/40 bg-red-500/10 text-red-200'
                          : 'border-amber-500/30 bg-amber-500/10 text-amber-100'
                      }`}
                    >
                      <p className="font-semibold">{a.name}</p>
                      <p className="text-sm opacity-90 mt-1">{a.message}</p>
                      <p className="text-xs mt-2 text-white/60">{a.total} complaints tracked</p>
                    </motion.div>
                  )
                )}
              </div>
            </div>
          )}

          <div
            className="rounded-2xl p-6"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              border: '1px solid rgba(255, 255, 255, 0.03)',
            }}
          >
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BarChart3 size={16} />
              7-day volume & priority mix
            </h3>
            {trends?.daily && (
              <MultiLineChart data={trends.daily} title="Priority trends" />
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div
              className="rounded-2xl p-6"
              style={{
                background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                border: '1px solid rgba(255, 255, 255, 0.03)',
              }}
            >
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                Category distribution
              </h3>
              {categoryChartData.length > 0 && (
                <CategoryChart data={categoryChartData} />
              )}
            </div>
            <div
              className="rounded-2xl p-6"
              style={{
                background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
                border: '1px solid rgba(255, 255, 255, 0.03)',
              }}
            >
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                Daily volume
              </h3>
              {trends?.daily && <TrendChart data={trends.daily} />}
            </div>
          </div>

          <div
            className="rounded-2xl p-6 text-sm text-gray-300"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              border: '1px solid rgba(255, 255, 255, 0.03)',
            }}
          >
            <p className="font-semibold text-[#F5F5F5] mb-2">Classification consistency</p>
            <p>{qa?.classification_note}</p>
            {qa?.priority_mix?.length > 0 && (
              <ul className="mt-3 space-y-1 text-gray-400">
                {qa.priority_mix.map((p: { name: string; value: number; pct: number }) => (
                  <li key={p.name}>
                    {p.name}: {p.value} ({p.pct}%)
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
