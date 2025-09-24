<template>
  <view class="login-wrap">
    <view class="card">
      <view class="title">后台登录</view>

      <uni-easyinput
        v-model="username"
        placeholder="账号"
        clearable
        @confirm="handleLogin"
      />
      <uni-easyinput
        v-model="password"
        type="password"
        placeholder="密码"
        @confirm="handleLogin"
      />

      <button
        class="btn"
        :loading="loading"
        :disabled="loading"
        @click="handleLogin"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { request } from '@/common/utils/request' // ✅ 使用统一封装

// ===== 若你后端已拆分：用 /auth/login =====
const LOGIN_API = '/cal_price/auth/login'

// ===== 如果你暂时还是旧路径，请改为下面这一行 =====
// const LOGIN_API = '/cal_price/login/admin'

const username = ref('')
const password = ref('')
const loading  = ref(false)

async function handleLogin () {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请输入账号和密码', icon: 'none' })
    return
  }

  try {
    loading.value = true
    const res = await request({
      url: LOGIN_API,
      method: 'POST',
      data: { username: username.value, password: password.value }
    })

    // 期望后端返回：{ token, id, username, nickname }
    if (res && res.token) {
      uni.setStorageSync('token', res.token)
      res.nickname && uni.setStorageSync('nickname', res.nickname)
      res.username && uni.setStorageSync('login_username', res.username)
      res.id && uni.setStorageSync('login_uid', res.id)

      // 登录成功：进后台首页（你也可以改去别的首页）
      uni.reLaunch({ url: '/pages/admin/index' }) // ✅ 改这里
    } else {
      uni.showToast({ title: res?.message || '账号或密码错误', icon: 'none' })
    }
  } catch (e) {
    // 这里不会处理 401 的跳转，request() 已经全局兜底
    uni.showToast({ title: '登录失败，请稍后再试', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f6f8fa;
  padding: 40rpx 24rpx;
}
.card {
  width: 92vw;
  max-width: 720rpx;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.06);
  padding: 40rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.title {
  font-size: 34rpx;
  font-weight: 600;
  margin-bottom: 8rpx;
  text-align: center;
}
.btn {
  margin-top: 8rpx;
}
</style>
