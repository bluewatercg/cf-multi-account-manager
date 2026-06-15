/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

declare module 'vue-echarts' {
  import type { DefineComponent } from 'vue'
  const VChart: DefineComponent<object, object, unknown>
  export default VChart
}
