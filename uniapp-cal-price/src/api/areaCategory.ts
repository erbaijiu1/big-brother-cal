import { request } from '@/common/utils/request'

// 定义数据接口类型
export interface CategoryData {
  name: string
  // 根据实际API补充其他字段
}

export interface SubIds {
  sub_ids: number[]
}

// 类别
export const getCats = () => {
  return request({
    url: '/cal_price/area_categories',
    method: 'GET'
  })
}

export const addCat = (data: CategoryData) => {
  return request({
    url: '/cal_price/area_categories',
    method: 'POST',
    data
  })
}

export const updCat = (id: number | string, data: CategoryData) => {
  return request({
    url: `/cal_price/area_categories/${id}`,
    method: 'PUT',
    data
  })
}

export const delCat = (id: number | string) => {
  return request({
    url: `/cal_price/area_categories/${id}`,
    method: 'DELETE'
  })
}

// 绑定子区
export const bindSubs = (id: number | string, sub_ids: SubIds) => {
  return request({
    url: `/cal_price/area_categories/${id}/subs`,
    method: 'POST',
    data: sub_ids
  })
}

export const unbindSub = (id: number | string, sub_id: number | string) => {
  return request({
    url: `/cal_price/area_categories/${id}/subs/${sub_id}`,
    method: 'DELETE'
  })
}
