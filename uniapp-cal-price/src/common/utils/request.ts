// /src/common/utils/request.ts
import { BASE_URL } from '@/common/config'

// 请求配置类型
export interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, any>
  header?: Record<string, string>
}

// 剔除空值工具函数
function prune<T extends Record<string, any>>(obj: T): Partial<T> {
  if (!obj || typeof obj !== 'object') return obj
  const out: Partial<T> = {}
  Object.keys(obj).forEach(k => {
    const v = obj[k]
    if (v !== undefined && v !== null && v !== '') {
      out[k as keyof T] = v
    }
  })
  return out
}

// 主请求函数
export function request<T = any>(options: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    const finalUrl = options.url.startsWith('http')
      ? options.url
      : BASE_URL + options.url

    const method = (options.method || 'GET').toUpperCase() as RequestOptions['method']

    const data = method === 'GET'
      ? prune(options.data || {})
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
          uni.reLaunch({ url: '/pages/login/index' })
          return
        }
        resolve(res.data as T) // ★ 给调用方返回类型提示
      },
      fail(err) {
        reject(err)
      }
    })
  })
}
