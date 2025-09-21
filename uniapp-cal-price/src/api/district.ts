import { request } from '@/common/utils/request'

// 获取所有行政区（含子区）
export const getDistricts = () => {
  return request({
    url: '/cal_price/districts',
    method: 'GET'
  })
}

// 新增行政区
export const createDistrict = (data) => {
  return request({
    url: '/cal_price/districts',
    method: 'POST',
    data
  })
}

// 更新行政区
export const updateDistrict = (id, data) => {
  return request({
    url: `/cal_price/districts/${id}`,
    method: 'PUT',
    data
  })
}

// 新增子区
export const createSub = (districtId, data) => {
  return request({
    url: `/cal_price/districts/${districtId}/subs`,
    method: 'POST',
    data
  })
}

// 更新子区
export const updateSub = (subId, data) => {
  return request({
    url: `/cal_price/districts/subs/${subId}`,
    method: 'PUT',
    data
  })
}

// 切换偏远区
export const toggleRemote = (subId, is_remote) => {
  return updateSub(subId, { is_remote })
}
