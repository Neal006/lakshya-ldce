'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { signOut, useSession } from 'next-auth/react';
import { 
  LayoutDashboard, 
  BarChart3, 
  Headphones, 
  Users, 
  LogOut,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';

interface SidebarProps {
  role: 'admin' | 'operational' | 'call_center' | 'quality_assurance';
}

const navItems = {
  admin: [
    { href: '/admin', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/admin/employees', label: 'Employees', icon: Users },
  ],
  operational: [
    { href: '/operational', label: 'Analytics', icon: BarChart3 },
  ],
  call_center: [
    { href: '/call-center', label: 'New Complaint', icon: Headphones },
  ],
  quality_assurance: [
    { href: '/quality-assurance', label: 'QA Insights', icon: ShieldCheck },
  ],
};

export function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const items = navItems[role] || [];

  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push('/login');
  };

  const initials = session?.user?.name
    ? session.user.name.split(' ').map(n => n[0]).join('').toUpperCase()
    : role.charAt(0).toUpperCase();

  return (
    <motion.aside
      className="w-64 min-h-screen sticky top-0 flex flex-col"
      style={{
        background: 'var(--gradient-surface)',
        boxShadow: 'var(--shadow-card)',
      }}
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="p-6 border-b border-gray-200">
        <motion.div 
          className="flex items-center gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] flex items-center justify-center shadow-lg">
            <AlertCircle className="text-white" size={20} />
          </div>
          <div>
            <h1 className="font-bold text-lg text-[var(--color-secondary)]">SOLV.ai</h1>
            <p className="text-xs text-gray-400">Management System</p>
          </div>
        </motion.div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {items.map((item, index) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <motion.div
              key={item.href}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * index + 0.3 }}
            >
              <Link href={item.href}>
                <motion.div
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </motion.div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200 space-y-3">
        <motion.div 
          className="card-pressed p-3"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-dark)] flex items-center justify-center text-white font-semibold">
              {initials}
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--color-secondary)]">
                {session?.user?.name || 'User'}
              </p>
              <p className="text-xs text-gray-400 capitalize">{role.replace('_', ' ')}</p>
            </div>
          </div>
        </motion.div>

        <motion.button
          onClick={handleLogout}
          className="nav-item w-full text-[var(--color-status)] hover:text-[var(--color-status-dark)]"
          whileHover={{ x: 4 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <LogOut size={20} />
          <span>Logout</span>
        </motion.button>
      </div>
    </motion.aside>
  );
}