import { BASE_URL } from '@/common/config'

export function request(options) {
  return new Promise((resolve, reject) => {
    // 判断是否要拼 BASE_URL
    const finalUrl = options.url.startsWith("http")
      ? options.url
      : BASE_URL + options.url

    uni.request({
      url: finalUrl,
      method: options.method || "GET",
      data: options.data || {},
      header: {
        "Authorization": "Bearer " + uni.getStorageSync("token"),
        ...(options.header || {})
      },
      success(res) {
        if (res.statusCode === 401) {
          // === 统一处理未登录 ===
          uni.removeStorageSync("token")
          uni.reLaunch({ url: "/pages/login/index" })
          return
        }
        resolve(res.data)
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

function logout() {
  uni.removeStorageSync('token')
  uni.redirectTo({ url: '/pages/login/index' })
}
