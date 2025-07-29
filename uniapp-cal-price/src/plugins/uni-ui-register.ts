import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'
import uniTransition from '@dcloudio/uni-ui/lib/uni-transition/uni-transition.vue'

import { createSSRApp } from 'vue'

/**
 * 注册需要用到的 uni-ui 组jj
 * 调用方式：在 main.ts 中执行 registerUniUi(app)
 */
export function registerUniUi(app: ReturnType<typeof createSSRApp>) {
  app.component('uniPopup', uniPopup)
  app.component('uniTransition', uniTransition)
}
