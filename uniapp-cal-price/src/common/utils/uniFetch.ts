// /common/utils/uniFetch.js
export default function uniFetch(opts) {
  // 自动带 token（如有）
  const token = uni.getStorageSync('token')
  const headers = opts.header || {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  return new Promise((resolve, reject) => {
    uni.request({
      timeout: 15000,
      ...opts,
      header: headers,
      success: res => {
        // 未登录或过期，自动跳转登录
        if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.showToast({ title: '请重新登录', icon: 'none' })
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/login/index' })
          }, 700)
          reject(res)
        } else if (res.statusCode === 200) {
          resolve(res) // 这里可以直接resolve(res.data)也行
        } else {
          uni.showToast({ title: `HTTP ${res.statusCode}`, icon: 'none' })
          reject(res)
        }
      },
      fail: err => {
        uni.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      }
    })
  })
}


// import uniFetch from '@/common/utils/uniFetch'

// // 使用
// uniFetch({
//   url: '/api/some/path',
//   method: 'GET'
// }).then(res => {
//   // res.data 处理
// }).catch(err => {
//   // 错误已统一 toast
// })