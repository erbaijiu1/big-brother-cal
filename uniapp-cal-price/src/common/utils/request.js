// /src/common/utils/request.js
import { BASE_URL } from '@/common/config'

function prune(obj) {
  if (!obj || typeof obj !== 'object') return obj
  const out = {}
  Object.keys(obj).forEach(k => {
    const v = obj[k]
    // 这里我把 undefined / null / '' 都去掉；如果你有查询必须传空字符串的场景，可以按需调整
    if (v !== undefined && v !== null && v !== '') out[k] = v
  })
  return out
}

export function request(options) {
  return new Promise((resolve, reject) => {
    const finalUrl = options.url.startsWith('http') ? options.url : BASE_URL + options.url
    const method = (options.method || 'GET').toUpperCase()

    const data = method === 'GET'
      ? prune(options.data || {})  // ★★★ 关键：GET 参数剔除空值
      : (options.data || {})

    uni.request({
      url: finalUrl,
      method,
      data,
      header: {
        'Authorization': 'Bearer ' + uni.getStorageSync('token'),
        ...(options.header || {})
      },
      success(res) {
        if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          // 确保路径与你项目实际一致
          uni.reLaunch({ url: '/pages/login/index' })
          return
        }
        resolve(res.data)
      },
      fail(err) { reject(err) }
    })
  })
}
