import { request } from '@/common/utils/request'
import { RegionRule } from '@/types/region'

// 获取所有区域规则
export const getRegionRules = () => {
  return request<RegionRule[]>({
    url: '/cal_price/region_rules/',
    method: 'GET'
  })
}

// 获取单个区域规则
export const getRegionRule = (id: string | number) => {
  return request<RegionRule>({
    url: `/cal_price/region_rules/${id}`,
    method: 'GET'
  })
}

// 创建区域规则
export const createRegionRule = (data: Partial<RegionRule>) => {
  return request<RegionRule>({
    url: '/cal_price/region_rules/',
    method: 'POST',
    data
  })
}

// 更新区域规则
export const updateRegionRule = (id: string | number, data: Partial<RegionRule>) => {
  return request<RegionRule>({
    url: `/cal_price/region_rules/${id}`,
    method: 'PUT',
    data
  })
}

// 删除区域规则
export const deleteRegionRule = (id: string | number) => {
  return request({
    url: `/cal_price/region_rules/${id}`,
    method: 'DELETE'
  })
}