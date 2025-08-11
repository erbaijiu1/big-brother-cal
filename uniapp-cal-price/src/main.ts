import { createSSRApp } from "vue";
import App from "./App.vue";
import { registerUniUi } from '@/plugins/uni-ui-register'
import '@/assets/css/global.scss';


export function createApp() {
  const app = createSSRApp(App);

  registerUniUi(app)

  return {
    app,
  };
}
