import { BASE_URL } from '@/common/config'

// 定义数据接口类型
interface CategoryData {
  name: string;
  // 根据实际API添加其他字段
}

interface SubIds {
  sub_ids: number[];
}

// 类别
export const getCats   = () => uni.request({ url: `${BASE_URL}/cal_price/area_categories` })
export const addCat    = (data: CategoryData) => uni.request({ url: `${BASE_URL}/cal_price/area_categories`,  method: 'POST', data })
export const updCat    = (id: number | string, data: CategoryData) => uni.request({ url: `${BASE_URL}/cal_price/area_categories/${id}`, method: 'PUT', data })
export const delCat    = (id: number | string)  => uni.request({ url: `${BASE_URL}/cal_price/area_categories/${id}`, method: 'DELETE' })

// 绑定子区
export const bindSubs  = (id: number | string, sub_ids: SubIds) => uni.request({ url: `${BASE_URL}/cal_price/area_categories/${id}/subs`, method: 'POST', data: sub_ids })
export const unbindSub = (id: number | string, sub_id: number | string)  => uni.request({ url: `${BASE_URL}/cal_price/area_categories/${id}/subs/${sub_id}`, method: 'DELETE' })