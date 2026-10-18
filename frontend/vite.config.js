import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendTarget = process.env.VITE_BACKEND_PROXY || 'http://127.0.0.1:8000'
const proxy = {
  '/api': {
    target: backendTarget,
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  },
  '/uploads': {
    target: backendTarget,
    changeOrigin: true
  }
}

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [vue()],
  server: {
    proxy
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    allowedHosts: ['.trycloudflare.com'],
    proxy
  }
})
