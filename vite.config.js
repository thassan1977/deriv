import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // This fixes the "Uncaught ReferenceError: global is not defined" error
    global: 'window',
  },
})
