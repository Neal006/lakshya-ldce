'use client';

import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { apiClient } from '@/lib/api-client';
import {
  Upload,
  Loader2,
  Mic,
  Save,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

type ComplaintRow = {
  id: string;
  complaint_text: string;
  category: string;
  priority: string;
  status: string;
  sentiment_score: number;
  source: string;
  created_at: string;
  products?: { name: string };
};

const STATUSES = ['new', 'assigned', 'in_progress', 'escalated', 'resolved', 'closed'] as const;
const CATEGORIES = ['Product', 'Packaging', 'Trade'] as const;
const PRIORITIES = ['High', 'Medium', 'Low'] as const;

export default function SupportDeskPage() {
  const [complaints, setComplaints] = useState<ComplaintRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ComplaintRow | null>(null);
  const [draftText, setDraftText] = useState('');
  const [category, setCategory] = useState<string>('Product');
  const [priority, setPriority] = useState<string>('Medium');
  const [status, setStatus] = useState<string>('new');
  const [sttBusy, setSttBusy] = useState(false);
  const [saveBusy, setSaveBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.getComplaints({ limit: '80' });
      const rows = (res.complaints || []) as ComplaintRow[];
      setComplaints(rows);
      setSelected((prev) => {
        if (!prev) return null;
        return rows.find((c) => c.id === prev.id) || prev;
      });
    } catch (e) {
      console.error(e);
      setError('Failed to load complaints');
    } finally {
      setLoading(false);
    }
  }, []);

  function applySelection(c: ComplaintRow) {
    setSelected(c);
    setDraftText(c.complaint_text || '');
    setCategory(c.category);
    setPriority(c.priority);
    setStatus(c.status);
  }

  useEffect(() => {
    load();
  }, [load]);

  const onUploadWav = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSttBusy(true);
    setError('');
    try {
      const result = await apiClient.transcribeAudio(file);
      setDraftText(result.text);
    } catch (err) {
      console.error(err);
      setError('Speech-to-text failed. Ensure STT_SERVICE_URL is running and you are logged in.');
    } finally {
      setSttBusy(false);
      e.target.value = '';
    }
  };

  const save = async () => {
    if (!selected) return;
    setSaveBusy(true);
    setError('');
    try {
      await apiClient.updateComplaint(selected.id, {
        complaint_text: draftText,
        category,
        priority,
        status,
      });
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaveBusy(false);
    }
  };

  return (
    <div className="pb-12 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#F5F5F5]">Support desk</h1>
          <p className="text-gray-400 mt-1">
            Transcribe call recordings (.wav), review AI category & priority, then update ticket status after you act.
          </p>
        </div>
        <button
          type="button"
          onClick={() => load()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-[#F5F5F5]"
          style={{
            background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
            boxShadow:
              '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <RefreshCw size={16} />
          Refresh queue
        </button>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div
          className="lg:col-span-2 rounded-2xl overflow-hidden"
          style={{
            background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
            boxShadow:
              '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
          }}
        >
          <div className="px-4 py-3 border-b border-white/5 text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Open queue
          </div>
          <div className="max-h-[560px] overflow-y-auto">
            {loading ? (
              <div className="flex justify-center py-16 text-gray-500">
                <Loader2 className="animate-spin" />
              </div>
            ) : complaints.length === 0 ? (
              <p className="p-6 text-gray-500 text-sm">No complaints yet.</p>
            ) : (
              complaints.map((c) => {
                const active = selected?.id === c.id;
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => applySelection(c)}
                    className={`w-full text-left px-4 py-3 border-b border-white/5 transition-colors ${
                      active ? 'bg-orange-500/10' : 'hover:bg-white/[0.03]'
                    }`}
                  >
                    <p className="text-sm text-[#F5F5F5] line-clamp-2">{c.complaint_text}</p>
                    <div className="flex flex-wrap gap-2 mt-2 text-[11px]">
                      <span className="text-orange-400 font-medium">{c.priority}</span>
                      <span className="text-gray-500">·</span>
                      <span className="text-gray-400">{c.category}</span>
                      <span className="text-gray-500">·</span>
                      <span className="text-gray-500 capitalize">{c.status.replace('_', ' ')}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        <div
          className="lg:col-span-3 rounded-2xl p-6"
          style={{
            background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
            boxShadow:
              '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
          }}
        >
          {!selected ? (
            <p className="text-gray-500 text-sm">Select a ticket from the queue to review and update.</p>
          ) : (
            <div className="space-y-6">
              <div>
                <p className="text-xs text-gray-500 mb-1">Product</p>
                <p className="text-lg font-semibold text-[#F5F5F5]">
                  {selected.products?.name || '—'}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Ticket #{selected.id.slice(0, 8)} · Source {selected.source}
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <Mic size={16} />
                    Transcript & edits
                  </label>
                  <label className="inline-flex items-center gap-2 text-xs text-orange-400 cursor-pointer">
                    <Upload size={14} />
                    <span>Upload .wav</span>
                    <input
                      type="file"
                      accept=".wav,audio/*"
                      className="hidden"
                      onChange={onUploadWav}
                      disabled={sttBusy}
                    />
                  </label>
                </div>
                {sttBusy && (
                  <p className="text-xs text-gray-500 mb-2 flex items-center gap-2">
                    <Loader2 className="animate-spin" size={14} /> Transcribing audio…
                  </p>
                )}
                <textarea
                  value={draftText}
                  onChange={(e) => setDraftText(e.target.value)}
                  rows={8}
                  className="w-full rounded-xl bg-[#2A2A2E] border border-white/10 text-sm text-[#F5F5F5] p-4 outline-none focus:ring-1 focus:ring-orange-500/40"
                  placeholder="Transcript appears here after STT, or type manually."
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl bg-[#2A2A2E] border border-white/10 text-sm text-[#F5F5F5] px-3 py-2.5"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full rounded-xl bg-[#2A2A2E] border border-white/10 text-sm text-[#F5F5F5] px-3 py-2.5"
                  >
                    {PRIORITIES.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full rounded-xl bg-[#2A2A2E] border border-white/10 text-sm text-[#F5F5F5] px-3 py-2.5"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s.replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                <span>Classifier sentiment: {selected.sentiment_score?.toFixed?.(2) ?? '—'}</span>
              </div>

              <motion.button
                type="button"
                onClick={save}
                disabled={saveBusy}
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold text-black"
                style={{
                  background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
                  boxShadow: '0 4px 0 #B8441F, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                }}
                whileTap={{ scale: 0.98 }}
              >
                {saveBusy ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                Save updates
              </motion.button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
