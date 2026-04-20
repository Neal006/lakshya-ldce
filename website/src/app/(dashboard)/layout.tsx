'use client';

import { Navbar } from '@/components/dashboard/Navbar';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import type { AppRole } from '@/lib/roles';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-[#0D0D0F] flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  const role = (session?.user?.role || 'admin') as AppRole;

  return (
    <div className="min-h-screen bg-[#0D0D0F]">
      <Navbar role={role} />
      <main className="pt-20 px-4 sm:px-6 lg:px-8 max-w-[1920px] mx-auto">
        {children}
      </main>
    </div>
  );
}
