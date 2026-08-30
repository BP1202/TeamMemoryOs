import { defineConfig } from 'vitest/config';
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
      '@tests': path.resolve(__dirname, './tests'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: [
        'components/**/*.{ts,tsx}',
        'features/**/*.{ts,tsx}',
        'layouts/**/*.{ts,tsx}',
        'stores/**/*.{ts,tsx}',
        'lib/**/*.{ts,tsx}',
        'utils/**/*.{ts,tsx}',
      ],
      exclude: [
        '**/*.d.ts',
        '**/*.test.{ts,tsx}',
        '**/index.{ts,tsx}',
      ],
    },
  },
});
