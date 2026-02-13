import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Cargar variables de entorno
  const env = loadEnv(mode, process.cwd(), '')
  const certKeyPath = env.VITE_CERT_KEY_PATH
  const certPath = env.VITE_CERT_PATH
  
  return {
    plugins: [react()],
    server: {
      https: {
        key: fs.readFileSync(path.resolve(__dirname, certKeyPath)),
        cert: fs.readFileSync(path.resolve(__dirname, certPath)),
      },
      port: 5173,
    },
  }
})
