// vite.config.js
import { defineConfig } from 'vite'
import { resolve } from 'path'
import uni from '@dcloudio/vite-plugin-uni'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [uni()],
  base: '/cal_static/',           // 末尾保留 /
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')   // 让 @ 指向 src
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['legacy-js-api', 'global-builtin', 'import']
      }
    }
  }
})
