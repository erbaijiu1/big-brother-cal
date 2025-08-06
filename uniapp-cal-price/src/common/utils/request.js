export function request(opt) {
  const token = uni.getStorageSync('token')
  opt.header = opt.header || {}
  if (token) opt.header.Authorization = 'Bearer ' + token
  return uni.request(opt)
}

function logout() {
  uni.removeStorageSync('token')
  uni.redirectTo({ url: '/pages/login/index' })
}
