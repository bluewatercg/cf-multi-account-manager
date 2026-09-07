import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig(({ mode }) => ({
  // Python server serves the bundle below /static/dist; Pages serves it at root.
  base: (globalThis as any).process?.env?.PAGES_BUILD === '1' ? '/' : (mode === 'production' ? '/static/dist/' : '/'),
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: false,
    }),
    Components({
      resolvers: [
        ElementPlusResolver({ importStyle: 'css' }),
      ],
      dts: false,
    }),
  ],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  optimizeDeps: {
    include: [
      'element-plus',
      '@element-plus/icons-vue',
    ],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        // 注意：不要用 manualChunks 强制合并 element-plus / echarts。
        // 该应用通过 unplugin 按需引入 EP 组件 + 路由懒加载图表，Rollup 的
        // 标准自动分包能正确生成无环的 chunk 图；强制合并会触发跨 chunk
        // 循环引用，导致运行时 “X is not a function” 初始化错误。
        manualChunks: undefined,
      },
    },
  },
}))
