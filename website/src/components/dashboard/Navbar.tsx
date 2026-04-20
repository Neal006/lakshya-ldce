'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  BarChart3, 
  Headphones, 
  Users, 
  LogOut,
  AlertCircle,
  Bell,
  ChevronDown,
  Menu,
  X,
  Settings,
  Search,
  ClipboardList,
  ShieldCheck,
  Mic,
} from 'lucide-react';
import gsap from 'gsap';
import type { AppRole } from '@/lib/roles';
import { homeHrefForRole } from '@/lib/roles';

interface NavbarProps {
  role: AppRole;
}

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const panelSubtitle: Record<AppRole, string> = {
  admin: 'Support executive',
  operational: 'Operations manager',
  call_center: 'Caller intake',
  quality_assurance: 'Quality assurance',
};

const navItems: Record<string, NavItem[]> = {
  admin: [
    { href: '/admin', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { href: '/admin/support', label: 'Support desk', icon: <ClipboardList size={20} /> },
    { href: '/voice-agent', label: 'Voice Agent', icon: <Mic size={20} /> },
    { href: '/admin/employees', label: 'Employees', icon: <Users size={20} /> },
  ],
  operational: [
    { href: '/operational', label: 'Command center', icon: <BarChart3 size={20} /> },
    { href: '/voice-agent', label: 'Voice Agent', icon: <Mic size={20} /> },
  ],
  call_center: [
    { href: '/call-center', label: 'New complaint', icon: <Headphones size={20} /> },
    { href: '/voice-agent', label: 'Voice Agent', icon: <Mic size={20} /> },
  ],
  quality_assurance: [
    { href: '/quality-assurance', label: 'QA insights', icon: <ShieldCheck size={20} /> },
    { href: '/voice-agent', label: 'Voice Agent', icon: <Mic size={20} /> },
  ],
};

export function Navbar({ role }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [notifications] = useState(3);
  
  const profileRef = useRef<HTMLDivElement>(null);
  const items = navItems[role] || [];

  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push('/login');
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    const button = e.currentTarget;
    gsap.to(button, {
      y: 4,
      scale: 0.98,
      duration: 0.1,
      ease: 'power2.inOut',
    });
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLButtonElement>) => {
    const button = e.currentTarget;
    gsap.to(button, {
      y: 0,
      scale: 1,
      duration: 0.15,
      ease: 'power3.out',
    });
  };

  const initials = session?.user?.name
    ? session.user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : role.charAt(0).toUpperCase();

  const fullName = session?.user?.name || 'User Name';

  return (
    <>
      {/* Main Navbar */}
      <motion.nav
        className="fixed top-0 left-0 right-0 z-50 h-16"
        style={{
          background: 'linear-gradient(165deg, #252528 0%, #1A1A1D 100%)',
          boxShadow: '0 4px 0 rgba(0, 0, 0, 0.5), 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
        }}
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="h-full max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          {/* Left Section: Logo + Navigation */}
          <div className="flex items-center gap-8">
            {/* Logo */}
            <Link href={homeHrefForRole(role)}>
              <motion.div 
                className="flex items-center gap-3"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{
                    background: 'linear-gradient(145deg, #FF6B35 0%, #FF4500 50%, #CC3700 100%)',
                    boxShadow: '0 2px 0 #CC3700, 0 4px 8px rgba(255, 69, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                  }}
                >
                  <AlertCircle className="text-white" size={20} />
                </div>
                <div className="hidden sm:block">
                  <h1 className="font-bold text-lg text-[#F5F5F5]">SOLV.ai</h1>
                  <p className="text-xs text-gray-400 -mt-0.5">{panelSubtitle[role]}</p>
                </div>
              </motion.div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-1">
              {items.map((item, index) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                
                return (
                  <motion.div
                    key={item.href}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 * index + 0.2 }}
                  >
                    <Link href={item.href}>
                      <motion.div
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
                        style={{
                          background: isActive 
                            ? 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)' 
                            : 'transparent',
                          color: isActive ? '#FF4500' : '#9CA3AF',
                          boxShadow: isActive 
                            ? 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)' 
                            : 'none',
                          border: isActive ? '1px solid rgba(255, 69, 0, 0.3)' : '1px solid transparent',
                        }}
                        whileHover={{ 
                          background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                          color: '#F5F5F5',
                          boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
                        }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {item.icon}
                        <span>{item.label}</span>
                      </motion.div>
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Right Section: Search, Notifications, Profile */}
          <div className="flex items-center gap-3">
            {/* Search - Hidden on mobile */}
            <motion.div 
              className="hidden md:flex items-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <div 
                className="flex items-center gap-2 px-4 py-2 rounded-xl"
                style={{
                  background: '#2A2A2E',
                  boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
                }}
              >
                <Search size={16} className="text-gray-500" />
                <input 
                  type="text"
                  placeholder="Search..."
                  className="bg-transparent border-none outline-none text-sm text-[#F5F5F5] placeholder-gray-500 w-32 lg:w-48"
                />
              </div>
            </motion.div>

            {/* Notifications */}
            <motion.button
              className="relative p-2.5 rounded-xl"
              style={{
                background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                boxShadow: '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
              whileHover={{ 
                boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.7), -4px -4px 8px rgba(255, 255, 255, 0.03)',
                y: -1,
              }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <Bell size={20} className="text-gray-400" />
              {notifications > 0 && (
                <span 
                  className="absolute -top-1 -right-1 w-5 h-5 rounded-full text-white text-[10px] flex items-center justify-center font-bold"
                  style={{
                    background: 'linear-gradient(145deg, #EF4444 0%, #DC2626 100%)',
                    boxShadow: '0 2px 4px rgba(239, 68, 68, 0.4)',
                  }}
                >
                  {notifications}
                </span>
              )}
            </motion.button>

            {/* Profile Dropdown */}
            <motion.div 
              className="relative"
              ref={profileRef}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              <motion.button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center gap-3 pl-2 pr-3 py-1.5 rounded-xl"
                style={{
                  background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                  boxShadow: '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
                whileHover={{ 
                  boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.7), -4px -4px 8px rgba(255, 255, 255, 0.03)',
                }}
                whileTap={{ scale: 0.98 }}
              >
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                  style={{
                    background: 'linear-gradient(145deg, #FF6B35 0%, #CC3700 100%)',
                    boxShadow: '0 2px 0 #CC3700, inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                  }}
                >
                  {initials}
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-semibold text-[#F5F5F5] leading-tight">{fullName}</p>
                  <p className="text-[10px] text-gray-400 capitalize leading-tight">{role.replace('_', ' ')}</p>
                </div>
                <ChevronDown 
                  size={16} 
                  className="text-gray-400 transition-transform duration-200" 
                  style={{ transform: isProfileOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
                />
              </motion.button>

              {/* Profile Dropdown Menu */}
              <AnimatePresence>
                {isProfileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -10, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    className="absolute right-0 mt-2 w-56 rounded-xl overflow-hidden z-50"
                    style={{
                      background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                      boxShadow: '12px 12px 24px rgba(0, 0, 0, 0.7), -12px -12px 24px rgba(255, 255, 255, 0.02), inset 1px 1px 2px rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.03)',
                    }}
                  >
                    <div className="p-4 border-b border-gray-700">
                      <p className="text-sm font-semibold text-[#F5F5F5]">{fullName}</p>
                      <p className="text-xs text-gray-400">{session?.user?.email || 'user@example.com'}</p>
                    </div>
                    <div className="p-2">
                      <button 
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-[#F5F5F5] hover:bg-orange-500/10 transition-colors"
                      >
                        <Settings size={16} />
                        <span>Settings</span>
                      </button>
                      <button 
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[#EF4444] hover:bg-red-500/10 transition-colors"
                      >
                        <LogOut size={16} />
                        <span>Logout</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Mobile Menu Toggle */}
            <motion.button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2.5 rounded-xl"
              style={{
                background: 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                boxShadow: '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
              whileTap={{ scale: 0.95 }}
            >
              {isMobileMenuOpen ? <X size={20} className="text-gray-400" /> : <Menu size={20} className="text-gray-400" />}
            </motion.button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="fixed inset-y-0 right-0 w-80 z-40 lg:hidden pt-20"
            style={{
              background: 'linear-gradient(165deg, #1A1A1D 0%, #0D0D0F 100%)',
              boxShadow: '-8px 0 32px rgba(0, 0, 0, 0.5)',
            }}
          >
            <div className="p-6">
              {/* Mobile Search */}
              <div 
                className="flex items-center gap-2 px-4 py-3 rounded-xl mb-6"
                style={{
                  background: '#2A2A2E',
                  boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.6), inset -4px -4px 8px rgba(255, 255, 255, 0.02)',
                }}
              >
                <Search size={18} className="text-gray-500" />
                <input 
                  type="text"
                  placeholder="Search..."
                  className="bg-transparent border-none outline-none text-sm text-[#F5F5F5] placeholder-gray-500 w-full"
                />
              </div>

              {/* Mobile Navigation */}
              <div className="space-y-2">
                {items.map((item, index) => {
                  const isActive = pathname === item.href;
                  
                  return (
                    <motion.div
                      key={item.href}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * index }}
                    >
                      <Link href={item.href} onClick={() => setIsMobileMenuOpen(false)}>
                        <motion.div
                          className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all"
                          style={{
                            background: isActive 
                              ? 'linear-gradient(165deg, #FF6B35 0%, #FF4500 50%, #CC3700 100%)' 
                              : 'linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%)',
                            color: isActive ? '#000' : '#9CA3AF',
                            boxShadow: isActive 
                              ? '0 4px 0 #CC3700, 0 8px 16px rgba(255, 69, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)' 
                              : '6px 6px 12px rgba(0, 0, 0, 0.6), -6px -6px 12px rgba(255, 255, 255, 0.04), inset 1px 1px 1px rgba(255, 255, 255, 0.1)',
                          }}
                          whileTap={{ scale: 0.98, y: 2 }}
                        >
                          {item.icon}
                          <span className="font-medium">{item.label}</span>
                        </motion.div>
                      </Link>
                    </motion.div>
                  );
                })}
              </div>

              {/* Mobile Logout */}
              <motion.button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl mt-6"
                style={{
                  background: 'linear-gradient(165deg, #EF4444 0%, #DC2626 50%, #B91C1C 100%)',
                  color: '#fff',
                  boxShadow: '0 4px 0 #B91C1C, 0 8px 16px rgba(239, 68, 68, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
                }}
                whileTap={{ scale: 0.98, y: 4, boxShadow: '0 0 0 #B91C1C, 0 2px 8px rgba(239, 68, 68, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)' }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <LogOut size={20} />
                <span className="font-medium">Logout</span>
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backdrop for mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsMobileMenuOpen(false)}
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          />
        )}
      </AnimatePresence>
    </>
  );
}
