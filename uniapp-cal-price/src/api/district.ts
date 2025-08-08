import { BASE_URL } from '@/common/config'

// 获取所有行政区（含子区）
export const getDistricts = () => 
  uni.request({ url: `${BASE_URL}/cal_price/districts`, method: 'GET' })

// 新增行政区
export const createDistrict = (data: any) =>
  uni.request({ url: `${BASE_URL}/cal_price/districts`, method: 'POST', data })

// 更新行政区
export const updateDistrict = (id: string | number, data: any) =>
  uni.request({ url: `${BASE_URL}/cal_price/districts/${id}`, method: 'PUT', data })

// 新增子区
export const createSub = (districtId: string | number, data: any) =>
  uni.request({ url: `${BASE_URL}/cal_price/districts/${districtId}/subs`, method: 'POST', data })

// 更新子区
export const updateSub = (subId: string | number, data: any) =>
  uni.request({ url: `${BASE_URL}/cal_price/districts/subs/${subId}`, method: 'PUT', data })

// 切换偏远区
export const toggleRemote = (subId: string | number, is_remote: boolean) =>
  updateSub(subId, { is_remote })