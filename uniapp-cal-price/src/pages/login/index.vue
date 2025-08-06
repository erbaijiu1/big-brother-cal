<template>
  <view>
    <uni-easyinput v-model="username" placeholder="账号" />
    <uni-easyinput v-model="password" type="password" placeholder="密码" />
    <button @click="login">登录</button>
  </view>
</template>
<script setup>
import { ref } from 'vue'
const username = ref('')
const password = ref('')

function login() {
  uni.request({
    url: 'http://127.0.0.1:8000/admin/login',
    method: 'POST',
    data: { username: username.value, password: password.value },
    success(res) {
      if(res.data.token) {
        uni.setStorageSync('token', res.data.token)
        uni.redirectTo({ url: '/pages/admin/channel/index' }) // 跳后台首页
      } else {
        uni.showToast({ title: '账号或密码错误', icon: 'none' })
      }
    }
  })
}
</script>
