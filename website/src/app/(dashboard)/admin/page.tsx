'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  X,
  Users,
  Zap,
  Filter,
  Download,
  FileDown
} from 'lucide-react';
import { generateReportPDF, captureChart } from '@/lib/generate-report-pdf';
import type { ChartImages } from '@/lib/generate-report-pdf';
import { Card, ProgressBar } from '@/components/ui';
import gsap from 'gsap';

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
  const [activeFilter, setActiveFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const headerRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);
  const chartsRef = useRef<HTMLDivElement>(null);
  const trendChartRef = useRef<HTMLDivElement>(null);
  const categoryChartRef = useRef<HTMLDivElement>(null);
  const priorityChartRef = useRef<HTMLDivElement>(null);

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
        color: p.name === 'High' ? '#EF4444' : p.name === 'Medium' ? '#3B82F6' : '#22C55E',
      })));
      setTrendData(trendsRes.daily);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const captureCharts = async (): Promise<ChartImages> => {
    const [trendChart, categoryChart, priorityChart] = await Promise.all([
      captureChart(trendChartRef.current),
      captureChart(categoryChartRef.current),
      captureChart(priorityChartRef.current),
    ])
    return { trendChart, categoryChart, priorityChart }
  }

  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      const result = await apiClient.getAnalyticsReport();
      const reportData = result.report || result;
      setReport(reportData);
      const charts = await captureCharts()
      generateReportPDF(reportData, charts);
    } catch (error) {
      console.error('Failed to generate report:', error);
      const fallbackReport = {
        executive_summary: 'Unable to generate AI report at this time. The GenAI service may be unavailable.',
        key_findings: ['Service temporarily unavailable'],
        recommendations: ['Please try again later'],
      };
      setReport(fallbackReport);
      const charts = await captureCharts()
      generateReportPDF(fallbackReport, charts);
    } finally {
      setReportLoading(false);
    }
  };

  const handleGetPDF = async () => {
    if (report) {
      const charts = await captureCharts()
      generateReportPDF(report, charts);
    } else {
      handleGenerateReport();
    }
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // GSAP Animations
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Header animation
      gsap.fromTo('.dashboard-header',
        { opacity: 0, y: -20 },
        { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out', delay: 0.1 }
      );

      // Stats cards stagger
      gsap.fromTo('.stat-card',
        { opacity: 0, y: 30, scale: 0.95 },
        { 
          opacity: 1, 
          y: 0, 
          scale: 1, 
          duration: 0.6, 
          stagger: 0.1, 
          ease: 'power3.out',
          delay: 0.3 
        }
      );

      // Charts animation
      gsap.fromTo('.chart-card',
        { opacity: 0, y: 40, rotateX: -10 },
        { 
          opacity: 1, 
          y: 0, 
          rotateX: 0, 
          duration: 0.7, 
          stagger: 0.15, 
          ease: 'power3.out',
          delay: 0.6 
        }
      );
    });

    return () => ctx.revert();
  }, []);

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
      <div className="min-h-screen flex items-center justify-center">
        <motion.div 
          className="flex flex-col items-center gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-12 h-12 rounded-xl animate-spin"
            style={{
              background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
              boxShadow: '0 4px 12px rgba(255, 107, 53, 0.4)',
            }}
          />
          <p className="text-gray-400">Loading dashboard...</p>
        </motion.div>
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

  const filteredComplaints = activeFilter === 'all' 
    ? mappedComplaints 
    : mappedComplaints.filter(c => c.priority.toLowerCase() === activeFilter);

  return (
    <div className="min-h-screen pb-12">
      {/* Header Section */}
      <div ref={headerRef} className="dashboard-header mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <motion.h1 
              className="text-3xl sm:text-4xl font-bold text-[#F5F5F5]"
              style={{ fontFamily: "'SF Pro Display', -apple-system, sans-serif" }}
            >
              Dashboard
            </motion.h1>
            <p className="text-gray-400 mt-1">Welcome back! Here's what's happening today.</p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Filter Buttons */}
            <div 
              className="flex items-center gap-1 p-1 rounded-xl"
              style={{
                background: '#2A2A2E',
                boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
              }}
            >
              {(['all', 'high', 'medium', 'low'] as const).map((filter) => (
                <motion.button
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                  className="px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all"
                  style={{
                    background: activeFilter === filter 
                      ? 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)' 
                      : 'transparent',
                    color: activeFilter === filter ? '#000' : '#9CA3AF',
                    boxShadow: activeFilter === filter 
                      ? '0 2px 0 #B8441F, inset 0 1px 0 rgba(255, 255, 255, 0.3)' 
                      : 'none',
                  }}
                  whileHover={{ scale: activeFilter === filter ? 1 : 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {filter}
                </motion.button>
              ))}
            </div>

            {/* Export Button */}
            <motion.button
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium"
              style={{
                background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                color: '#F5F5F5',
                boxShadow: '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
              whileHover={{ 
                boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.7), -4px -4px 8px rgba(255, 255, 255, 0.03)',
                y: -1,
              }}
              whileTap={{ scale: 0.98 }}
            >
              <Download size={16} />
              <span className="hidden sm:inline">Export</span>
            </motion.button>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <AnimatePresence>
        {notifications.length > 0 && (
          <div className="mb-6 space-y-2">
            {notifications.map((notif) => (
              <motion.div
                key={notif.id}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 50 }}
                className={`flex items-center justify-between p-4 rounded-xl text-sm ${
                  notif.type === 'high_priority' 
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20' 
                    : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                }`}
                style={{
                  boxShadow: notif.type === 'high_priority'
                    ? 'inset 0 1px 0 rgba(239, 68, 68, 0.1)'
                    : 'inset 0 1px 0 rgba(59, 130, 246, 0.1)',
                }}
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="p-2 rounded-lg"
                    style={{
                      background: notif.type === 'high_priority' 
                        ? 'rgba(239, 68, 68, 0.2)' 
                        : 'rgba(59, 130, 246, 0.2)',
                    }}
                  >
                    {notif.type === 'high_priority' ? <AlertTriangle size={16} /> : <Bell size={16} />}
                  </div>
                  <span className="font-medium">{notif.message}</span>
                </div>
                <button 
                  onClick={() => dismissNotification(notif.id)}
                  className="p-1 rounded-lg hover:bg-white/5 transition-colors"
                >
                  <X size={16} />
                </button>
              </motion.div>
            ))}
          </div>
        )}
      </AnimatePresence>

      {/* Stats Grid */}
      {stats && (
        <div ref={statsRef} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Complaints"
            value={stats.total_complaints.toLocaleString()}
            subtitle="All time"
            icon={<MessageSquare className="text-[#FF6B35]" size={24} />}
            trend="+12%"
            trendUp={true}
            className="stat-card"
          />
          <StatCard
            title="Today's Complaints"
            value={stats.today_complaints}
            subtitle="New today"
            icon={<TrendingUp className="text-[#3B82F6]" size={24} />}
            trend="+5"
            trendUp={true}
            className="stat-card"
          />
          <StatCard
            title="High Priority"
            value={stats.high_priority}
            subtitle="Require immediate attention"
            icon={<AlertTriangle className="text-[#EF4444]" size={24} />}
            trend="-2"
            trendUp={false}
            className="stat-card"
          />
          <StatCard
            title="Resolved Today"
            value={stats.resolved_today}
            subtitle="Great job!"
            icon={<CheckCircle className="text-[#22C55E]" size={24} />}
            trend="92%"
            trendUp={true}
            className="stat-card"
          />
        </div>
      )}

      {/* Charts Section */}
      <div ref={chartsRef} className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 chart-card">
          <div 
            ref={trendChartRef}
            className="p-6 rounded-2xl h-full"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.03)',
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div 
                  className="p-2.5 rounded-xl"
                  style={{
                    background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
                    boxShadow: '0 2px 0 #B8441F, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                  }}
                >
                  <TrendingUp size={20} className="text-white" />
                </div>
                <h3 className="text-lg font-semibold text-[#F5F5F5]">Complaint Trends</h3>
              </div>
              <span className="text-sm text-gray-400">Last 7 Days</span>
            </div>
            <TrendChart data={trendData} title="" />
          </div>
        </div>

        <div className="chart-card">
          <div 
            ref={categoryChartRef}
            className="p-6 rounded-2xl h-full"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.03)',
            }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div 
                className="p-2.5 rounded-xl"
                style={{
                  background: 'linear-gradient(145deg, #3B82F6 0%, #1D4ED8 100%)',
                  boxShadow: '0 2px 0 #1E40AF, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                }}
              >
                <Zap size={20} className="text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[#F5F5F5]">By Category</h3>
            </div>
            <CategoryChart data={categoryData} title="" />
          </div>
        </div>
      </div>

      {/* Performance Metrics & Priority */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="chart-card">
          <div 
            ref={priorityChartRef}
            className="p-6 rounded-2xl h-full"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.03)',
            }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div 
                className="p-2.5 rounded-xl"
                style={{
                  background: 'linear-gradient(145deg, #22C55E 0%, #15803D 100%)',
                  boxShadow: '0 2px 0 #166534, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                }}
              >
                <Filter size={20} className="text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[#F5F5F5]">By Priority</h3>
            </div>
            <PriorityChart data={priorityData} title="" />
          </div>
        </div>

        <div className="chart-card">
          <div 
            className="p-6 rounded-2xl h-full"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.03)',
            }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div 
                className="p-2.5 rounded-xl"
                style={{
                  background: 'linear-gradient(145deg, #8B5CF6 0%, #6D28D9 100%)',
                  boxShadow: '0 2px 0 #5B21B6, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                }}
              >
                <Target size={20} className="text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[#F5F5F5]">Performance Metrics</h3>
            </div>
            
            <div className="space-y-6">
              {stats && (
                <>
                  <div>
                    <div className="flex justify-between mb-3">
                      <span className="text-sm text-gray-400 flex items-center gap-2">
                        <Clock size={16} className="text-[#FF6B35]" />
                        Avg Resolution Time
                      </span>
                      <span className="text-sm font-semibold text-[#F5F5F5]">{stats.avg_resolution_time_hours}h</span>
                    </div>
                    <div 
                      className="h-3 rounded-full overflow-hidden"
                      style={{
                        background: '#2A2A2E',
                        boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <motion.div 
                        className="h-full rounded-full"
                        style={{
                          background: 'linear-gradient(90deg, #FF6B35 0%, #CC3700 100%)',
                          boxShadow: '0 1px 2px rgba(255, 107, 53, 0.3)',
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min((stats.avg_resolution_time_hours / 24) * 100, 100)}%` }}
                        transition={{ duration: 1, delay: 0.8, ease: 'easeOut' }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-3">
                      <span className="text-sm text-gray-400 flex items-center gap-2">
                        <Target size={16} className="text-[#22C55E]" />
                        SLA Compliance
                      </span>
                      <span className="text-sm font-semibold text-[#F5F5F5]">{stats.sla_compliance_percent}%</span>
                    </div>
                    <div 
                      className="h-3 rounded-full overflow-hidden"
                      style={{
                        background: '#2A2A2E',
                        boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <motion.div 
                        className="h-full rounded-full"
                        style={{
                          background: 'linear-gradient(90deg, #22C55E 0%, #16A34A 100%)',
                          boxShadow: '0 1px 2px rgba(34, 197, 94, 0.3)',
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${stats.sla_compliance_percent}%` }}
                        transition={{ duration: 1, delay: 0.9, ease: 'easeOut' }}
                      />
                    </div>
                  </div>

                  <div 
                    className="grid grid-cols-3 gap-4 mt-6"
                  >
                    {[
                      { label: 'Avg Response', value: `${stats.avg_resolution_time_hours}h`, color: '#FF6B35' },
                      { label: 'CSAT Score', value: `${Math.round((1 - stats.avg_sentiment) * 50 + 50)}%`, color: '#3B82F6' },
                      { label: 'Escalated', value: stats.high_priority.toString(), color: '#EF4444' },
                    ].map((metric, idx) => (
                      <motion.div 
                        key={metric.label}
                        className="p-4 rounded-xl text-center"
                        style={{
                          background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                          boxShadow: 'inset 6px 6px 12px rgba(0, 0, 0, 0.6), inset -6px -6px 12px rgba(255, 255, 255, 0.02)',
                          border: '1px solid rgba(255, 255, 255, 0.03)',
                        }}
                        whileHover={{ scale: 1.02 }}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1 + idx * 0.1 }}
                      >
                        <p 
                          className="text-2xl font-bold"
                          style={{ color: metric.color }}
                        >
                          {metric.value}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{metric.label}</p>
                      </motion.div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* AI Report Section */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.8 }}
      >
        <div 
          className="p-6 rounded-2xl relative overflow-hidden"
          style={{
            background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
            boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
          }}
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div className="flex items-center gap-4">
              <div 
                className="p-3 rounded-xl"
                style={{
                  background: 'linear-gradient(145deg, #8B5CF6 0%, #6D28D9 100%)',
                  boxShadow: '0 4px 0 #5B21B6, 0 8px 16px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                }}
              >
                <FileText size={24} className="text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-[#F5F5F5]">AI-Powered Executive Report</h3>
                <p className="text-sm text-gray-400">Generate insights using GenAI analysis</p>
              </div>
            </div>
            <motion.button
              onClick={handleGenerateReport}
              disabled={reportLoading}
              className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm disabled:opacity-50"
              style={{
                background: 'linear-gradient(145deg, #FF6B35 0%, #FF4500 50%, #CC3700 100%)',
                color: '#000',
                boxShadow: '0 4px 0 #B8441F, 0 8px 16px rgba(255, 107, 53, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
              }}
              whileHover={{ 
                boxShadow: '0 5px 0 #B8441F, 0 10px 20px rgba(255, 107, 53, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                y: -1,
              }}
              whileTap={{ 
                y: 4, 
                boxShadow: '0 0 0 #B8441F, 0 2px 8px rgba(255, 107, 53, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)',
              }}
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

            <motion.button
              onClick={handleGetPDF}
              disabled={reportLoading}
              className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm disabled:opacity-50"
              style={{
                background: 'linear-gradient(145deg, #22C55E 0%, #16A34A 100%)',
                color: '#fff',
                boxShadow: '0 4px 0 #15803D, 0 8px 16px rgba(34, 197, 94, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
              }}
              whileHover={{ 
                boxShadow: '0 5px 0 #15803D, 0 10px 20px rgba(34, 197, 94, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                y: -1,
              }}
              whileTap={{ 
                y: 4, 
                boxShadow: '0 0 0 #15803D, 0 2px 8px rgba(34, 197, 94, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)',
              }}
            >
              <FileDown size={18} />
              Get PDF
            </motion.button>
          </div>

          <AnimatePresence>
            {report && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-4"
              >
                {report.executive_summary && (
                  <div 
                    className="p-4 rounded-xl border border-purple-500/20"
                    style={{
                      background: 'linear-gradient(165deg, rgba(139, 92, 246, 0.1) 0%, rgba(109, 40, 217, 0.05) 100%)',
                    }}
                  >
                    <h4 className="text-sm font-semibold text-purple-400 mb-2">Executive Summary</h4>
                    <p className="text-sm text-gray-300 leading-relaxed">{report.executive_summary}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {report.key_findings && report.key_findings.length > 0 && (
                    <div 
                      className="p-4 rounded-xl border border-blue-500/20"
                      style={{
                        background: 'linear-gradient(165deg, rgba(59, 130, 246, 0.1) 0%, rgba(29, 78, 216, 0.05) 100%)',
                      }}
                    >
                      <h4 className="text-sm font-semibold text-blue-400 mb-2">Key Findings</h4>
                      <ul className="space-y-2">
                        {report.key_findings.map((finding: string, i: number) => (
                          <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-blue-400 mt-1">•</span>
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.recommendations && report.recommendations.length > 0 && (
                    <div 
                      className="p-4 rounded-xl border border-amber-500/20"
                      style={{
                        background: 'linear-gradient(165deg, rgba(245, 158, 11, 0.1) 0%, rgba(180, 83, 9, 0.05) 100%)',
                      }}
                    >
                      <h4 className="text-sm font-semibold text-amber-400 mb-2">Recommendations</h4>
                      <ul className="space-y-2">
                        {report.recommendations.map((rec: string, i: number) => (
                          <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-amber-400 mt-1">→</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {report.risk_flags && report.risk_flags.length > 0 && (
                  <div 
                    className="p-4 rounded-xl border border-red-500/20"
                    style={{
                      background: 'linear-gradient(165deg, rgba(239, 68, 68, 0.1) 0%, rgba(185, 28, 28, 0.05) 100%)',
                    }}
                  >
                    <h4 className="text-sm font-semibold text-red-400 mb-2">Risk Flags</h4>
                    <ul className="space-y-2">
                      {report.risk_flags.map((flag: string, i: number) => (
                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                          <AlertTriangle size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
                          {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Decorative gradient */}
          <div 
            className="absolute -bottom-16 -right-16 w-32 h-32 rounded-full opacity-20 blur-3xl pointer-events-none"
            style={{
              background: 'linear-gradient(145deg, #8B5CF6 0%, #6D28D9 100%)',
            }}
          />
        </div>
      </motion.div>

      {/* Recent Complaints */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.9 }}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="p-2.5 rounded-xl"
              style={{
                background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
                boxShadow: '0 2px 0 #B8441F, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
              }}
            >
              <Users size={20} className="text-white" />
            </div>
            <h2 className="text-xl font-bold text-[#F5F5F5]">Recent Complaints</h2>
          </div>
          <motion.button 
            className="flex items-center gap-2 text-sm text-[#FF6B35] font-medium hover:text-[#FF8C5A] transition-colors"
            whileHover={{ x: 4 }}
          >
            View All →
          </motion.button>
        </div>
        
        <div 
          className="rounded-2xl overflow-hidden"
          style={{
            background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
            boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
          }}
        >
          <ComplaintTable complaints={filteredComplaints} />
        </div>
      </motion.div>
    </div>
  );
}
