'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui';
import { Complaint } from '@/lib/data';
import { AlertTriangle, Package, ShoppingCart, MessageSquare } from 'lucide-react';

interface ComplaintTableProps {
  complaints: Complaint[];
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  assigned: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-purple-100 text-purple-700',
  resolved: 'bg-green-100 text-green-700',
  escalated: 'bg-red-100 text-red-700',
  closed: 'bg-gray-100 text-gray-700',
};

const priorityIcons: Record<string, React.ReactNode> = {
  High: <AlertTriangle size={14} className="text-[var(--color-status)]" />,
  Medium: <MessageSquare size={14} className="text-[var(--color-primary)]" />,
  Low: <MessageSquare size={14} className="text-[var(--color-accent)]" />,
};

const categoryIcons: Record<string, React.ReactNode> = {
  Product: <Package size={16} />,
  Packaging: <Package size={16} />,
  Trade: <ShoppingCart size={16} />,
};

export function ComplaintTable({ complaints }: ComplaintTableProps) {
  return (
    <motion.div
      className="card overflow-hidden"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600">ID</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600">Complaint</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600">Category</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600">Priority</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600">Status</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600">Team</th>
            </tr>
          </thead>
          <tbody>
            {complaints.map((complaint, index) => (
              <motion.tr
                key={complaint.id}
                className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors cursor-pointer"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ 
                  duration: 0.4, 
                  delay: index * 0.05,
                  ease: [0.22, 1, 0.36, 1]
                }}
                whileHover={{ x: 4 }}
              >
                <td className="py-4 px-4 text-sm font-medium text-gray-500">
                  #{complaint.id.padStart(3, '0')}
                </td>
                <td className="py-4 px-4">
                  <p className="text-sm font-medium text-[var(--color-secondary)] line-clamp-1">
                    {complaint.complaint_text}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(complaint.created_at).toLocaleDateString()}
                  </p>
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center gap-2">
                    {categoryIcons[complaint.category]}
                    <span className="text-sm text-gray-600">{complaint.category}</span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center gap-2">
                    {priorityIcons[complaint.priority]}
                    <Badge 
                      variant={
                        complaint.priority === 'High' ? 'urgent' : 
                        complaint.priority === 'Medium' ? 'priority' : 
                        'default'
                      }
                    >
                      {complaint.priority}
                    </Badge>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColors[complaint.status]}`}>
                    {complaint.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="py-4 px-4 text-sm text-gray-600">
                  {complaint.assigned_team}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
