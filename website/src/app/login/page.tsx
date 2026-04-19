'use client'

import { useState } from 'react'
import { signIn, getSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { dashboardHomeForRole } from '@/lib/roles'
import { motion } from 'framer-motion'
import { Package, Loader2, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
      })

      if (result?.error) {
        setError('Invalid email or password')
        setIsLoading(false)
        return
      }

      router.refresh()
      const session = await getSession()
      router.push(dashboardHomeForRole(session?.user?.role))
      setIsLoading(false)
    } catch {
      setError('An error occurred. Please try again.')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)] p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <Card className="p-8">
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mx-auto mb-4"
            >
              <Package className="text-white" size={32} />
            </motion.div>
            <h1 className="text-2xl font-bold text-[var(--color-secondary)]">
              SOLV.ai
            </h1>
            <p className="text-gray-500 mt-2">Sign in to your account</p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-xl bg-red-50 text-red-700 flex items-center gap-2"
            >
              <AlertCircle size={20} />
              <span className="text-sm">{error}</span>
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@company.com"
                required
                disabled={isLoading}
                className="input w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={isLoading}
                className="input w-full"
              />
            </div>

            <button
              type="submit"
              className="btn-primary-skeuo w-full py-3 flex items-center justify-center gap-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-500">Demo accounts</p>
            <div className="mt-4 space-y-2 text-sm text-gray-600">
              <p className="text-center"><strong>Support executive:</strong> admin@company.com / admin123</p>
              <p className="text-center"><strong>Caller intake:</strong> support@company.com / admin123</p>
              <p className="text-center"><strong>Operations manager:</strong> ops@company.com / admin123</p>
              <p className="text-center"><strong>Quality assurance:</strong> qa@company.com / admin123</p>
            </div>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}