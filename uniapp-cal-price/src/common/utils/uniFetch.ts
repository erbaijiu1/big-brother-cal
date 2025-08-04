// 简易 Promise 封装，可按需扩展拦截器 / 统一报错
export default function uniFetch(opts: UniApp.RequestOptions) {
  return new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
    uni.request({
      timeout: 15000,
      ...opts,
      success: res => {
        if (res.statusCode === 200) {
          resolve(res)
        } else {
          uni.showToast({ title:`HTTP ${res.statusCode}`, icon:'none' })
          reject(res)
        }
      },
      fail: err => {
        uni.showToast({ title:'网络错误', icon:'none' })
        reject(err)
      }
    })
  })
}
