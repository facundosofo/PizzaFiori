import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Cargar variables de entorno
  const env = loadEnv(mode, process.cwd(), '')
  const certKeyPath = env.VITE_CERT_KEY_PATH
  const certPath = env.VITE_CERT_PATH
  
  const apiTarget = env.VITE_API_TARGET || 'https://127.0.0.1:8000'
  const proxyRoutes = [
    '/auth',
    '/audit',
    '/dashboard',
    '/gastos',
    '/gastos-categorias',
    '/health',
    '/ofertas',
    '/productos',
    '/productos-categorias',
    '/stock',
    '/uploads',
    '/users',
    '/ventas'
  ]
  const proxy: Record<string, any> = {}
  for (const route of proxyRoutes) {
    proxy[route] = {
      target: apiTarget,
      changeOrigin: true,
      secure: false,
      bypass: (req: any) => {
        if (req.headers.accept?.includes('text/html')) {
          return '/index.html'
        }
      },
      configure: (proxyServer: any) => {
        proxyServer.on('proxyRes', (proxyRes: any) => {
          const loc = proxyRes.headers['location']
          if (loc) {
            try {
              const u = new URL(loc)
              proxyRes.headers['location'] = u.pathname + u.search
            } catch { /* relative URL, leave as-is */ }
          }
        })
      },
    }
  }

  return {
    plugins: [react()],
    server: {
      https: {
        key: fs.readFileSync(path.resolve(__dirname, certKeyPath)),
        cert: fs.readFileSync(path.resolve(__dirname, certPath)),
      },
      host: '0.0.0.0',
      port: 5173,
      proxy,
    },
  }
})
