<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

// 应用主组件，所有路由页面将在这里渲染

// 强制设置深色主题
onMounted(() => {
  document.documentElement.setAttribute('data-theme', 'dark')
  document.body.setAttribute('data-theme', 'dark')
})
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
}
</style> 