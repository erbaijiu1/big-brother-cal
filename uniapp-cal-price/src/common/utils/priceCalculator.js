/**
 * 价格计算相关的公共逻辑
 */

// 体积重计算常量
export const VOLUMETRIC_RATIO = 200

/**
 * 计算体积重
 * @param {number|null} volume 体积（m³）
 * @returns {number|null} 体积重（kg）
 */
export function calculateVolumetricWeight(volume) {
  if (volume === null || volume === undefined) return null
  const v = parseFloat(volume)
  if (isNaN(v)) return null
  return +(v * VOLUMETRIC_RATIO).toFixed(2)
}

/**
 * 计算计费重量（取体积重和实重的较大值）
 * @param {number|null} weight 实重（kg）
 * @param {number|null} volume 体积（m³）
 * @returns {number|null} 计费重量（kg）
 */
export function calculateChargeWeight(weight, volume) {
  const realWeight = weight !== null ? parseFloat(weight) : null
  const volumetricWeight = calculateVolumetricWeight(volume)
  
  if (realWeight === null || volumetricWeight === null) return null
  if (isNaN(realWeight)) return null
  
  return Math.max(realWeight, volumetricWeight).toFixed(2)
}

/**
 * 生成计费重量提示文本
 * @param {number|null} weight 实重（kg）
 * @param {number|null} volume 体积（m³）
 * @returns {string} 提示文本
 */
export function getChargeWeightTip(weight, volume) {
  const chargeWeight = calculateChargeWeight(weight, volume)
  const volumetricWeight = calculateVolumetricWeight(volume)
  
  if (chargeWeight === null) return ''
  
  return `计费重量：${chargeWeight} kg（体积重 ${volumetricWeight} kg / 实重 ${weight} kg，取其大）`
}

/**
 * 验证基础表单数据
 * @param {Object} formData 表单数据
 * @returns {Object} 验证结果 {valid: boolean, message: string}
 */
export function validateBasicForm(formData) {
  const { weight, volume, categoryId, district } = formData
  
  // 验证分类
  if (!categoryId) {
    return { valid: false, message: '请选择分类' }
  }
  
  // 验证重量或体积至少填写一个
  if (weight === null && volume === null) {
    return { valid: false, message: '请填写重量或体积' }
  }
  
  // 验证重量
  if (weight !== null) {
    if (isNaN(weight) || weight < 0) {
      return { valid: false, message: '重量必须是非负数' }
    }
    if (weight > 10000) {
      return { valid: false, message: '重量超出合理范围（最大10000kg）' }
    }
  }
  
  // 验证体积
  if (volume !== null) {
    if (isNaN(volume) || volume < 0) {
      return { valid: false, message: '体积必须是非负数' }
    }
    if (volume > 100) {
      return { valid: false, message: '体积超出合理范围（最大100m³）' }
    }
  }
  
  // 验证地址
  if (!district) {
    return { valid: false, message: '请选择收货地区' }
  }
  
  return { valid: true, message: '' }
}

/**
 * 清理和标准化请求数据
 * @param {Object} formData 原始表单数据
 * @param {string} packageType 包裹类型
 * @returns {Object} 清理后的请求数据
 */
export function cleanRequestData(formData, packageType = '袋装') {
  return {
    category_id: Number(formData.categoryId),
    weight: formData.weight !== null ? Math.max(0, Number(formData.weight)) : null,
    volume: formData.volume !== null ? Math.max(0, Number(formData.volume)) : null,
    extra_fee_data: {
      type: packageType,
      need_go_upstairs: formData.needGoUpstairs,
      district: formData.selectedDistrict || '',
      sub_district: formData.selectedSubDistrict || '',
      is_remote: formData.isRemote,
      has_elevator: formData.hasElevator,
      need_stairs: formData.needStairs
    }
  }
}