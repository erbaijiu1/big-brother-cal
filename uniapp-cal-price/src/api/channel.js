// src/api/channel.js  (js/ts 都可)
import { BASE_URL } from '@/common/config'

// 渠道列表等你已有，这里只补附加费接口
export const getChannelSurcharges = (id) =>
  uni.request({ url: `${BASE_URL}/cal_price/channel_mgr/${id}/surcharges`, method: 'GET' })

export const saveChannelSurcharges = (id, payload) =>
  uni.request({ url: `${BASE_URL}/cal_price/channel_mgr/${id}/surcharges`, method: 'PUT', data: payload })

// 供选择用的数据（按你前面的接口命名，可调整为你的实际路径）
export const getAreaCategories = () =>
  uni.request({ url: `${BASE_URL}/cal_price/area_categories`, method: 'GET' })

export const getDistricts = () =>
  uni.request({ url: `${BASE_URL}/cal_price/districts`, method: 'GET' })
