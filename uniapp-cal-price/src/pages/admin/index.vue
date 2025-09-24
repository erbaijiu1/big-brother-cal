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
      </view>
    </view>
  </template>
  
 <script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const nickname = ref(uni.getStorageSync('nickname') || '')

const menuItems = [
  { title: '渠道管理', desc: '配置物流渠道', path: '/pages/admin/channel/index' },
  { title: '分类管理', desc: '管理货物分类', path: '/pages/admin/classify_mgr/index' },
  { title: '行政区管理', desc: '配置区/子区及偏远标记', path: '/pages/admin/district/index' },
  { title: '计价规则', desc: '设置运费及附加费规则', path: '/pages/admin/pricing_mgr/index' },
  { title: '用户管理', desc: '后台用户账号维护', path: '/pages/admin/user_mgr/index' },
]

function goPage(url) {
  uni.navigateTo({ url })
}

// 进入页面或从后台返回前台时触发
onShow(() => {
  const token = uni.getStorageSync('token')
  if (!token) {
    // 用 reLaunch 清栈，防止返回到受限页
    uni.reLaunch({ url: '/pages/login/index' })
    return
  }
  // 刷新欢迎语
  nickname.value = uni.getStorageSync('nickname') || ''
})
</script>


  <style scoped>
  .admin-home {
    padding: 32rpx;
    min-height: 100vh;
    background: #f7f8fa;
  }
  .header {
    margin-bottom: 40rpx;
  }
  .title {
    font-size: 40rpx;
    font-weight: bold;
  }
  .welcome {
    font-size: 28rpx;
    color: #666;
  }
  .menu {
    display: flex;
    flex-direction: column;
    gap: 24rpx;
  }
  .menu-card {
    background: #fff;
    border-radius: 16rpx;
    padding: 28rpx;
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.06);
  }
  .menu-title {
    font-size: 32rpx;
    font-weight: 500;
  }
  .menu-desc {
    font-size: 26rpx;
    color: #999;
    margin-top: 8rpx;
    padding: 8rpx;
  }
  </style>
  