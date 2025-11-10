<template>
  <view class="admin-home">
    <view class="header">
      <text class="title">管理后台</text>
      <text class="welcome">欢迎，{{ nickname || '管理员' }}</text>
    </view>

    <view class="menu">
      <view
        v-for="item in menuItems"
        :key="item.path"
        class="menu-card"
        @click="goPage(item.path)"
      >
        <text class="menu-title">{{ item.title }}</text>
        <text class="menu-desc">{{ item.desc }}</text>
      </view>

      <view v-if="!loading && menuItems.length === 0" class="menu-empty">
        暂无可用菜单，请联系管理员开通权限
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request' // ✅ 统一封装（401 自动跳登录）

const nickname = ref(uni.getStorageSync('nickname') || '')
const menuItems = ref([])
const loading = ref(false)

function goPage(url) {
  if (!url) return
  uni.navigateTo({ url })
}

async function loadMenu() {
  loading.value = true
  try {
    // 建议后端返回数组：[{title, desc, path, order}, ...]
    const res = await request({ url: '/cal_price/menu_mgr/menu_list', method: 'GET' })
    if (Array.isArray(res?.data)) {
      // 可选：按 order 或 title 排序
      menuItems.value = [...res.data].sort((a,b) => (a.order||9999) - (b.order||9999))
    } else {
      menuItems.value = []
    }
  } catch (e) {
    menuItems.value = []
    uni.showToast({ title: '菜单加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 进入页面或从后台返回前台时触发
onShow(() => {
  nickname.value = uni.getStorageSync('nickname') || ''
  loadMenu()
})
</script>

<style scoped>
.admin-home { padding: 32rpx; min-height: 100vh; background: #f7f8fa; }
.header { margin-bottom: 40rpx; }
.title { font-size: 40rpx; font-weight: bold; }
.welcome { font-size: 28rpx; color: #666; }
.menu { display: flex; flex-direction: column; gap: 24rpx; }
.menu-card { background: #fff; border-radius: 16rpx; padding: 28rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.06); }
.menu-title { font-size: 32rpx; font-weight: 500; }
.menu-desc { font-size: 26rpx; color: #999; margin-top: 8rpx; padding: 8rpx; }
.menu-empty { text-align: center; color: #999; padding: 40rpx 0; }
</style>
