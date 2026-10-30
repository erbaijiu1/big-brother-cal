// vite.config.js
import { defineConfig, loadEnv } from 'vite'
import { resolve } from 'path'
import uni from '@dcloudio/vite-plugin-uni'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [uni()],
    // 管理端继续部署在 /cal_static/；官网报价页可通过 h5public 模式部署在域名根目录。
    base: env.VITE_PUBLIC_BASE || '/cal_static/',
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
  }
})
