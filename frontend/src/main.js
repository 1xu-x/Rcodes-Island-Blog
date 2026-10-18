import { createApp } from 'vue'
import { createIcons, icons } from 'lucide'
import axios from 'axios'
import './style.css'
import App from './App.vue'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')
if (apiBaseUrl) {
  // GitHub Pages has no /api reverse proxy; point requests at Render directly.
  axios.defaults.baseURL = apiBaseUrl
}

// 让各组件里的 window.lucide.createIcons() 可用，同时图标打包进前端产物
window.lucide = {
  createIcons: () => createIcons({ icons })
}
createIcons({ icons })

createApp(App).mount('#app')
