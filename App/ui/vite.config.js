import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8555',
      '/files': 'http://localhost:8555',
      '/files-records': 'http://localhost:8555',
    },
  },
})
