<template>
  <view class="login-wrap">
    <uni-easyinput v-model="username" placeholder="账号" />
    <uni-easyinput v-model="password" type="password" placeholder="密码" />
    <button @click="handleLogin">登录</button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { request } from '@/common/utils/request.js'   // ✅ 用统一封装

const username = ref('')
const password = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请输入账号和密码', icon: 'none' })
    return
  }

  try {
    const res = await request({
      url: '/login/admin',   // ✅ 改成你的后端登录接口路径
      method: 'POST',
      data: { username: username.value, password: password.value }
    })

    if (res.token) {
      uni.setStorageSync('token', res.token)
      uni.setStorageSync('nickname', res.nickname || '')  // 保存昵称备用
      uni.reLaunch({ url: '/pages/admin/channel/index' }) // 跳后台首页
    } else {
      uni.showToast({ title: '账号或密码错误', icon: 'none' })
    }
  } catch (err) {
    uni.showToast({ title: '登录失败，请稍后再试', icon: 'none' })
  }
}
</script>

<style scoped>
.login-wrap {
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
button {
  margin-top: 20rpx;
}
</style>
