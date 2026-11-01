import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// During development the API runs on :4000; proxying keeps the browser on one origin.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:4000' } },
  preview: { port: 5173, proxy: { '/api': 'http://localhost:4000' } },
});
