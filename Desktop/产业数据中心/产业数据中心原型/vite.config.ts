import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  // GitHub Pages部署配置
  base: process.env.NODE_ENV === 'production' ? '/Industrial-Data-Center/' : '/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {
      less: {
        modifyVars: {
          // Ant Design主题变量
          '@primary-color': '#409EFF',
          '@dark-primary-color': '#00E5FF',
        },
        javascriptEnabled: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router'],
          antd: ['ant-design-vue'],
        },
      },
    },
  },
  server: {
    port: 3000,
    open: true,
  },
}) 