import { request } from '@/common/utils/request'

// 获取渠道附加费
export const getChannelSurcharges = (id) => {
  return request({
    url: `/cal_price/channel_mgr/${id}/surcharges`,
    method: 'GET'
  })
}

// 保存渠道附加费
export const saveChannelSurcharges = (id, payload) => {
  return request({
    url: `/cal_price/channel_mgr/${id}/surcharges`,
    method: 'PUT',
    data: payload
  })
}

// 获取区域分类
export const getAreaCategories = () => {
  return request({
    url: '/cal_price/area_categories',
    method: 'GET'
  })
}

// 获取地区及子区
export const getDistricts = () => {
  return request({
    url: '/cal_price/districts/',
    method: 'GET'
  })
}
