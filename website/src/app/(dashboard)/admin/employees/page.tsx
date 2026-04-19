'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Card, Button, Input, Badge } from '@/components/ui';
import { apiClient } from '@/lib/api-client';
import { Users, Plus, Trash2, Edit2, X } from 'lucide-react';

interface Employee {
  id: string;
  name: string;
  email: string;
  role: string;
  department?: string;
  created_at: string;
}

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'call_center' as const, department: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await apiClient.getEmployees();
      setEmployees(res.employees);
    } catch (err) {
      console.error('Failed to fetch employees:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchEmployees(); }, [fetchEmployees]);

  const handleAddEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await apiClient.createEmployee(formData);
      setShowForm(false);
      setFormData({ name: '', email: '', password: '', role: 'call_center', department: '' });
      fetchEmployees();
    } catch (err: any) {
      setError(err.message || 'Failed to add employee');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this employee?')) return;
    try {
      await apiClient.deleteEmployee(id);
      fetchEmployees();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const roleColors: Record<string, string> = {
    admin: 'bg-red-100 text-red-700',
    operational: 'bg-blue-100 text-blue-700',
    call_center: 'bg-green-100 text-green-700',
  };

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      <Sidebar role="admin" />
      
      <main className="flex-1 p-8">
        <motion.div 
          className="mb-8 flex justify-between items-center"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div>
            <h1 className="text-3xl font-bold text-[var(--color-secondary)]">Employee Management</h1>
            <p className="text-gray-500 mt-1">Add and manage system users</p>
          </div>
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus size={18} />
            Add Employee
          </Button>
        </motion.div>

        <AnimatePresence>
          {showForm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 overflow-hidden"
            >
              <Card className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-[var(--color-secondary)]">New Employee</h3>
                  <button onClick={() => setShowForm(false)}><X size={20} className="text-gray-400" /></button>
                </div>
                {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
                <form onSubmit={handleAddEmployee} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input placeholder="Full Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
                  <Input placeholder="Email" type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} required />
                  <Input placeholder="Password" type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} required />
                  <div>
                    <select
                      value={formData.role}
                      onChange={e => setFormData({...formData, role: e.target.value as any})}
                      className="input appearance-none cursor-pointer"
                    >
                      <option value="call_center">Call Center</option>
                      <option value="operational">Operational</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <Input placeholder="Department (optional)" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} />
                  <div className="flex items-end">
                    <Button type="submit" disabled={submitting}>
                      {submitting ? 'Adding...' : 'Add Employee'}
                    </Button>
                  </div>
                </form>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Loading employees...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {employees.map((employee, index) => (
              <motion.div
                key={employee.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <Card className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center text-white font-bold text-lg">
                        {employee.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h4 className="font-semibold text-[var(--color-secondary)]">{employee.name}</h4>
                        <p className="text-sm text-gray-400">{employee.email}</p>
                      </div>
                    </div>
                    <button onClick={() => handleDelete(employee.id)} className="text-gray-400 hover:text-red-500 transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="mt-4 flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${roleColors[employee.role] || 'bg-gray-100 text-gray-700'}`}>
                      {employee.role.replace('_', ' ')}
                    </span>
                    {employee.department && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">
                        {employee.department}
                      </span>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}