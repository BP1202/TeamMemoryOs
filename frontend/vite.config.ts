import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@app': path.resolve(__dirname, './app'),
      '@components': path.resolve(__dirname, './components'),
      '@config': path.resolve(__dirname, './config'),
      '@features': path.resolve(__dirname, './features'),
      '@hooks': path.resolve(__dirname, './hooks'),
      '@layouts': path.resolve(__dirname, './layouts'),
      '@lib': path.resolve(__dirname, './lib'),
      '@providers': path.resolve(__dirname, './providers'),
      '@services': path.resolve(__dirname, './services'),
      '@stores': path.resolve(__dirname, './stores'),
      '@styles': path.resolve(__dirname, './styles'),
      '@typedefs': path.resolve(__dirname, './types'),
      '@utils': path.resolve(__dirname, './utils'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
