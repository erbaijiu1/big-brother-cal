/**
 * 价格计算工具类
 * 提取公共的计算逻辑，避免在多个页面中重复
 */

/**
 * 计算体积重
 * @param {number} volume 体积（立方米）
 * @returns {number|null} 体积重（kg）
 */
export function calculateVolumetricWeight(volume) {
  if (!volume && volume !== 0) return null
  const v = parseFloat(volume)
  return isNaN(v) ? null : +(v * 200).toFixed(2)
}

/**
 * 计算计费重量
 * @param {number} weight 实重（kg）
 * @param {number} volumetricWeight 体积重（kg）
 * @returns {number|null} 计费重量（kg）
 */
export function calculateChargeWeight(weight, volumetricWeight) {
  if (volumetricWeight === null || weight === null) return null
  const w = parseFloat(weight)
  if (isNaN(w)) return null
  return Math.max(w, volumetricWeight).toFixed(2)
}

/**
 * 验证表单数据
 * @param {Object} formData 表单数据
 * @returns {Object} 验证结果 { valid: boolean, message: string }
 */
export function validateFormData(formData) {
  const { weight, volume, pieces, selectedDistrict } = formData

  // 验证分类
  if (!formData.selectedCategory) {
    return { valid: false, message: '请选择分类' }
  }

  // 验证重量和体积（必填其一）
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

  // 验证件数（选填，但如果填写了要验证）
  if (pieces !== null && pieces > 1) {
    if (isNaN(pieces) || pieces < 1) {
      return { valid: false, message: '件数必须大于0' }
    }
    if (pieces > 10000) {
      return { valid: false, message: '件数超出合理范围（最大10000件）' }
    }
  }

  // 验证地址
  if (!selectedDistrict) {
    return { valid: false, message: '请选择收货地区' }
  }

  return { valid: true, message: '' }
}

/**
 * 清理请求数据
 * @param {Object} formData 表单数据
 * @returns {Object} 清理后的请求数据
 */
export function cleanRequestData(formData) {
  const extra = {
    type: '袋装',
    need_go_upstairs: formData.needGoUpstairs,
    district: formData.selectedDistrict || '',
    sub_district: formData.selectedSubDistrict || '',
    is_remote: formData.isRemote,
    has_elevator: formData.hasElevator,
    need_stairs: formData.needStairs
  }

  let baseData = {
    category_id: Number(formData.selectedCategory),
    extra_fee_data: extra
  }

  // 重量：必填，没有填写传0
  if (formData.weight !== null) {
    baseData.weight = Math.max(0, Number(formData.weight))
  } else {
    baseData.weight = 0
  }

  // 体积：必填，没有填写传0
  if (formData.volume !== null) {
    baseData.volume = Math.max(0, Number(formData.volume))
  } else {
    baseData.volume = 0
  }

  // 件数：可选，大于1件时才传递
  if (formData.pieces && formData.pieces > 1) {
    baseData.pieces = Math.max(1, Number(formData.pieces))
  }

  return baseData
}