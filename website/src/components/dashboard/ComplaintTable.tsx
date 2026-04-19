'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui';
import { AlertTriangle, Package, ShoppingCart, MessageSquare, Clock, User } from 'lucide-react';

interface Complaint {
  id: string;
  complaint_text: string;
  category: 'Product' | 'Packaging' | 'Trade';
  priority: 'High' | 'Medium' | 'Low';
  status: string;
  sentiment_score: number;
  source: string;
  product_id: string;
  created_at: string;
  assigned_team?: string;
}

interface ComplaintTableProps {
  complaints: Complaint[];
}

const statusStyles: Record<string, { bg: string; text: string; border: string }> = {
  new: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  assigned: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
  in_progress: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
  resolved: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
  escalated: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
  closed: { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20' },
};

const categoryIcons: Record<string, React.ReactNode> = {
  Product: <Package size={16} className="text-[#FF6B35]" />,
  Packaging: <Package size={16} className="text-[#8B5CF6]" />,
  Trade: <ShoppingCart size={16} className="text-[#3B82F6]" />,
};

export function ComplaintTable({ complaints }: ComplaintTableProps) {
  if (complaints.length === 0) {
    return (
      <motion.div
        className="p-8 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
          style={{
            background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
            boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
          }}
        >
          <MessageSquare size={24} className="text-gray-500" />
        </div>
        <p className="text-gray-400">No complaints found</p>
      </motion.div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left py-4 px-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">ID</th>
            <th className="text-left py-4 px-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">Complaint</th>
            <th className="text-left py-4 px-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">Category</th>
            <th className="text-left py-4 px-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">Priority</th>
            <th className="text-left py-4 px-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">Status</th>
            <th className="text-left py-4 px-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">Team</th>
          </tr>
        </thead>
        <tbody>
          {complaints.map((complaint, index) => {
            const statusStyle = statusStyles[complaint.status] || statusStyles.new;
            
            return (
              <motion.tr
                key={complaint.id}
                className="border-t border-gray-800 hover:bg-white/[0.02] transition-colors cursor-pointer group"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.3, 
                  delay: index * 0.05,
                  ease: [0.22, 1, 0.36, 1]
                }}
                whileHover={{ 
                  backgroundColor: 'rgba(255, 107, 53, 0.03)',
                }}
              >
                <td className="py-4 px-4">
                  <span className="text-sm font-mono text-gray-500">
                    #{complaint.id.slice(0, 8)}
                  </span>
                </td>
                <td className="py-4 px-4">
                  <p className="text-sm font-medium text-[#F5F5F5] line-clamp-1 group-hover:text-[#FF6B35] transition-colors">
                    {complaint.complaint_text}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock size={12} className="text-gray-500" />
                    <span className="text-xs text-gray-500">
                      {new Date(complaint.created_at).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric', 
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center gap-2">
                    <div 
                      className="p-1.5 rounded-lg"
                      style={{
                        background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                        boxShadow: 'inset 2px 2px 4px rgba(0, 0, 0, 0.6), inset -2px -2px 4px rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      {categoryIcons[complaint.category]}
                    </div>
                    <span className="text-sm text-gray-300">{complaint.category}</span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center gap-2">
                    {complaint.priority === 'High' && (
                      <AlertTriangle size={14} className="text-[#EF4444]" />
                    )}
                    <span 
                      className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
                      style={{
                        background: complaint.priority === 'High' 
                          ? 'linear-gradient(145deg, #EF4444 0%, #DC2626 100%)'
                          : complaint.priority === 'Medium'
                          ? 'linear-gradient(145deg, #3B82F6 0%, #2563EB 100%)'
                          : 'linear-gradient(145deg, #22C55E 0%, #16A34A 100%)',
                        color: '#fff',
                        boxShadow: complaint.priority === 'High'
                          ? '0 2px 0 #B91C1C, 0 4px 8px rgba(239, 68, 68, 0.3)'
                          : complaint.priority === 'Medium'
                          ? '0 2px 0 #1D4ED8, 0 4px 8px rgba(59, 130, 246, 0.3)'
                          : '0 2px 0 #166534, 0 4px 8px rgba(34, 197, 94, 0.3)',
                      }}
                    >
                      {complaint.priority}
                    </span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                    {complaint.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold"
                      style={{
                        background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
                      }}
                    >
                      <User size={12} className="text-white" />
                    </div>
                    <span className="text-sm text-gray-400">
                      {complaint.assigned_team || 'Unassigned'}
                    </span>
                  </div>
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
