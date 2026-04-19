'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { StatCard } from '@/components/dashboard/StatCard';
import { ComplaintTable } from '@/components/dashboard/ComplaintTable';
import { TrendChart, CategoryChart, PriorityChart } from '@/components/charts';
import { apiClient } from '@/lib/api-client';
import { 
  MessageSquare, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Target,
  FileText,
  Bell,
  Loader2,
  X
} from 'lucide-react';
import { Card, ProgressBar } from '@/components/ui';

interface DashboardStats {
  total_complaints: number;
  today_complaints: number;
  high_priority: number;
  resolved_today: number;
  avg_resolution_time_hours: number;
  sla_compliance_percent: number;
  avg_sentiment: number;
}

interface ComplaintData {
  id: string;
  text: string;
  category: string;
  priority: string;
  status: string;
  sentiment_score: number;
  source: string;
  assigned_team?: string;
  created_at: string;
  customer?: { name: string; email?: string };
  product?: { name: string };
}

interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [complaints, setComplaints] = useState<ComplaintData[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [priorityData, setPriorityData] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const [dashboardRes, complaintsRes, trendsRes] = await Promise.all([
        apiClient.getDashboardAnalytics(),
        apiClient.getComplaints({limit: '10'}),
        apiClient.getTrends(),
      ]);

      setStats(dashboardRes.summary);
      setComplaints(complaintsRes.complaints);
      setCategoryData(dashboardRes.by_category.map((c: any) => ({
        name: c.name,
        value: c.value,
        color: c.name === 'Product' ? '#FF6B35' : c.name === 'Packaging' ? '#AF52DE' : '#5AC8FA',
      })));
      setPriorityData(dashboardRes.by_priority.map((p: any) => ({
        name: p.name,
        value: p.value,
        color: p.name === 'High' ? '#FF3B30' : p.name === 'Medium' ? '#007AFF' : '#34C759',
      })));
      setTrendData(trendsRes.daily);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      const result = await apiClient.getAnalyticsReport();
      setReport(result.report || result);
    } catch (error) {
      console.error('Failed to generate report:', error);
      setReport({
        executive_summary: 'Unable to generate AI report at this time. The GenAI service may be unavailable.',
        key_findings: ['Service temporarily unavailable'],
        recommendations: ['Please try again later'],
      });
    } finally {
      setReportLoading(false);
    }
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const eventSource = new EventSource(apiClient.getSSEUrl());
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_complaint') {
          fetchData();
          setNotifications(prev => [{
            id: Date.now().toString(),
            type: 'new_complaint',
            message: 'New complaint received',
            timestamp: new Date(),
          }, ...prev].slice(0, 5));
        }
        if (data.type === 'high_priority_alert') {
          setNotifications(prev => [{
            id: Date.now().toString(),
            type: 'high_priority',
            message: `High priority alert: ${data.data?.category || 'Unknown'} complaint`,
            timestamp: new Date(),
          }, ...prev].slice(0, 5));
        }
      } catch {}
    };
    return () => eventSource.close();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex min-h-screen bg-[var(--color-background)] items-center justify-center">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  const mappedComplaints = complaints.map(c => ({
    id: c.id,
    complaint_text: c.text,
    category: c.category as 'Product' | 'Packaging' | 'Trade',
    priority: c.priority as 'High' | 'Medium' | 'Low',
    sentiment_score: c.sentiment_score,
    source: c.source as 'email' | 'call' | 'walkin',
    product_id: c.product?.name || '',
    status: c.status,
    created_at: c.created_at,
    assigned_team: c.assigned_team,
  }));

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      <Sidebar role="admin" />
      
      <main className="flex-1 p-8 max-h-screen overflow-y-auto">
        <div className="flex items-start justify-between mb-8">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <h1 className="text-3xl font-bold text-[var(--color-secondary)]">Admin Dashboard</h1>
            <p className="text-gray-500 mt-1">Monitor and manage all complaints across the organization</p>
          </motion.div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <motion.button
                className="card-pressed p-2.5 rounded-xl relative"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Bell size={20} className="text-gray-500" />
                {notifications.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-white text-[10px] flex items-center justify-center">
                    {notifications.length}
                  </span>
                )}
              </motion.button>
            </div>
          </div>
        </div>

        <AnimatePresence>
          {notifications.length > 0 && (
            <div className="mb-6 space-y-2">
              {notifications.map((notif) => (
                <motion.div
                  key={notif.id}
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 50 }}
                  className={`flex items-center justify-between p-3 rounded-xl text-sm ${
                    notif.type === 'high_priority' 
                      ? 'bg-red-50 text-red-700 border border-red-200' 
                      : 'bg-blue-50 text-blue-700 border border-blue-200'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {notif.type === 'high_priority' ? <AlertTriangle size={16} /> : <Bell size={16} />}
                    <span>{notif.message}</span>
                  </div>
                  <button onClick={() => dismissNotification(notif.id)}>
                    <X size={14} />
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </AnimatePresence>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Complaints"
              value={stats.total_complaints.toLocaleString()}
              subtitle="All time"
              icon={<MessageSquare className="text-[var(--color-primary)]" size={24} />}
              delay={0}
            />
            <StatCard
              title="Today's Complaints"
              value={stats.today_complaints}
              subtitle="New today"
              icon={<TrendingUp className="text-[var(--color-accent)]" size={24} />}
              delay={0.1}
            />
            <StatCard
              title="High Priority"
              value={stats.high_priority}
              subtitle="Require immediate attention"
              icon={<AlertTriangle className="text-[var(--color-status)]" size={24} />}
              delay={0.2}
            />
            <StatCard
              title="Resolved Today"
              value={stats.resolved_today}
              subtitle="Great job!"
              icon={<CheckCircle className="text-green-500" size={24} />}
              delay={0.3}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <TrendChart data={trendData} title="Complaint Trend (Last 7 Days)" />
          </div>
          <CategoryChart data={categoryData} title="By Category" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <PriorityChart data={priorityData} title="By Priority" />
          
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            <Card>
              <h3 className="text-lg font-semibold mb-6">Performance Metrics</h3>
              
              <div className="space-y-6">
                {stats && (
                  <>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-600 flex items-center gap-2">
                          <Clock size={16} />
                          Avg Resolution Time
                        </span>
                        <span className="text-sm font-semibold">{stats.avg_resolution_time_hours}h</span>
                      </div>
                      <ProgressBar progress={65} />
                    </div>

                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-600 flex items-center gap-2">
                          <Target size={16} />
                          SLA Compliance
                        </span>
                        <span className="text-sm font-semibold">{stats.sla_compliance_percent}%</span>
                      </div>
                      <ProgressBar progress={stats.sla_compliance_percent} variant="success" />
                    </div>

                    <div className="grid grid-cols-3 gap-4 mt-6">
                      <motion.div className="card-pressed p-4 text-center" whileHover={{ scale: 1.02 }}>
                        <p className="text-2xl font-bold text-[var(--color-primary)]">{stats.avg_resolution_time_hours}h</p>
                        <p className="text-xs text-gray-500 mt-1">Avg Response</p>
                      </motion.div>
                      <motion.div className="card-pressed p-4 text-center" whileHover={{ scale: 1.02 }}>
                        <p className="text-2xl font-bold text-[var(--color-accent)]">{Math.round((1 - stats.avg_sentiment) * 50 + 50)}%</p>
                        <p className="text-xs text-gray-500 mt-1">CSAT Score</p>
                      </motion.div>
                      <motion.div className="card-pressed p-4 text-center" whileHover={{ scale: 1.02 }}>
                        <p className="text-2xl font-bold text-[var(--color-status)]">{stats.high_priority}</p>
                        <p className="text-xs text-gray-500 mt-1">Escalated</p>
                      </motion.div>
                    </div>
                  </>
                )}
              </div>
            </Card>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="mb-8"
        >
          <Card className="relative overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600">
                  <FileText size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-[var(--color-secondary)]">AI-Powered Executive Report</h3>
                  <p className="text-sm text-gray-500">Generate insights using GenAI analysis</p>
                </div>
              </div>
              <motion.button
                onClick={handleGenerateReport}
                disabled={reportLoading}
                className="btn-primary-skeuo px-6 py-2.5 flex items-center gap-2 disabled:opacity-50"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {reportLoading ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText size={18} />
                    Generate Report
                  </>
                )}
              </motion.button>
            </div>

            <AnimatePresence>
              {report && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 space-y-4"
                >
                  {report.executive_summary && (
                    <div className="p-4 rounded-xl bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100">
                      <h4 className="text-sm font-semibold text-purple-800 mb-2">Executive Summary</h4>
                      <p className="text-sm text-gray-700 leading-relaxed">{report.executive_summary}</p>
                    </div>
                  )}

                  {report.key_findings && report.key_findings.length > 0 && (
                    <div className="p-4 rounded-xl bg-blue-50 border border-blue-100">
                      <h4 className="text-sm font-semibold text-blue-800 mb-2">Key Findings</h4>
                      <ul className="space-y-1">
                        {report.key_findings.map((finding: string, i: number) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-blue-500 mt-0.5">&#8226;</span>
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.trend_analysis && (
                    <div className="p-4 rounded-xl bg-green-50 border border-green-100">
                      <h4 className="text-sm font-semibold text-green-800 mb-2">Trend Analysis</h4>
                      <p className="text-sm text-gray-700 leading-relaxed">{report.trend_analysis}</p>
                    </div>
                  )}

                  {report.recommendations && report.recommendations.length > 0 && (
                    <div className="p-4 rounded-xl bg-amber-50 border border-amber-100">
                      <h4 className="text-sm font-semibold text-amber-800 mb-2">Recommendations</h4>
                      <ul className="space-y-1">
                        {report.recommendations.map((rec: string, i: number) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-amber-500 mt-0.5">&#10148;</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.risk_flags && report.risk_flags.length > 0 && (
                    <div className="p-4 rounded-xl bg-red-50 border border-red-100">
                      <h4 className="text-sm font-semibold text-red-800 mb-2">Risk Flags</h4>
                      <ul className="space-y-1">
                        {report.risk_flags.map((flag: string, i: number) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <AlertTriangle size={14} className="text-red-500 mt-0.5 flex-shrink-0" />
                            {flag}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="absolute -bottom-16 -right-16 w-32 h-32 rounded-full bg-gradient-to-br from-purple-100 to-indigo-100 opacity-30 blur-xl pointer-events-none" />
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-[var(--color-secondary)]">Recent Complaints</h2>
            <motion.button 
              className="text-sm text-[var(--color-primary)] font-medium hover:underline"
              whileHover={{ x: 4 }}
            >
              View All →
            </motion.button>
          </div>
          <ComplaintTable complaints={mappedComplaints} />
        </motion.div>
      </main>
    </div>
  );
}