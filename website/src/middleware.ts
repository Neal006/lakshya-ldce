import { auth } from '@/lib/auth'
import { NextResponse } from 'next/server'

const publicRoutes = ['/login']
const publicApiRoutes = ['/api/health', '/api/webhooks', '/api/sse', '/api/auth']

const roleRoutes: Record<string, string[]> = {
  admin: ['/admin'],
  operational: ['/operational'],
  call_center: ['/call-center'],
}

const DEMO_MODE = process.env.DEMO_MODE === 'true'

export async function middleware(request: Request) {
  const { pathname } = new URL(request.url)
  
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next()
  }

  if (publicApiRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next()
  }

  if (DEMO_MODE && pathname.startsWith('/api/')) {
    return NextResponse.next()
  }

  const session = await auth()

  if (!session) {
    if (pathname.startsWith('/api/')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const userRole = session.user.role

  if (!pathname.startsWith('/api/')) {
    for (const [role, routes] of Object.entries(roleRoutes)) {
      for (const route of routes) {
        if (pathname.startsWith(route) && userRole !== role && userRole !== 'admin') {
          if (userRole === 'operational') {
            return NextResponse.redirect(new URL('/operational', request.url))
          }
          if (userRole === 'call_center') {
            return NextResponse.redirect(new URL('/call-center', request.url))
          }
          return NextResponse.redirect(new URL('/login', request.url))
        }
      }
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/admin/:path*',
    '/operational/:path*',
    '/call-center/:path*',
    '/api/:path*',
  ],
}