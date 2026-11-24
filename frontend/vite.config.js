import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/visitors': 'http://127.0.0.1:5000',
      '/auth': 'http://127.0.0.1:5000',
      '/inventory': 'http://127.0.0.1:5000',
      '/reservations': 'http://127.0.0.1:5000',
      '/reports': 'http://127.0.0.1:5000',
      '/sales': 'http://127.0.0.1:5000',
      '/fines': 'http://127.0.0.1:5000',
    },
  },
})
