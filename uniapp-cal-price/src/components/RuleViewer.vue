<template>
  <view class="rule-viewer">
    <view class="viewer-table-head">
      <text class="col-unit">计价方式</text>
      <!-- <text class="col-type">计价方式</text> -->
      <text class="col-range">区间范围</text>
      <text class="col-desc">价格说明</text>
    </view>

    <view v-for="(rule, idx) in ruleArr" :key="idx" class="viewer-row">
      <text class="col-unit">{{ unitOf(rule) || '-' }}</text>
      <!-- <text class="col-type">{{ rule.prize ? '一口价' : '按区间' }}</text> -->
      <text class="col-range">{{ rangeText(rule) }}</text>
      <text class="col-desc">{{ priceDesc(rule) }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const DEFAULT_MAX = 99999999

const props = defineProps({
  rules: { type: [Array, String], default: () => [] }
})

/* ========= utils ========= */
const toArray = (val) => {
  if (Array.isArray(val)) return val
  if (typeof val === 'string') {
    try { const a = JSON.parse(val); return Array.isArray(a) ? a : [] } catch { return [] }
  }
  return []
}
const stripZeros = (v) => {
  if (v === '' || v === undefined || v === null) return ''
  const n = Number(v)
  if (!Number.isFinite(n)) return String(v ?? '')
  return String(n).replace(/\.0+$/,'').replace(/(\.\d*[1-9])0+$/,'$1')
}
const unitOf = (r) => {
  const raw = (r?.prize_type ?? r?.unit ?? r?.unit_type ?? r?.price_unit ?? r?.type ?? '') + ''
  const U = raw.toUpperCase()
  if (!U) return ''
  if (U.includes('CBM') || U.includes('M3')) return 'CBM'
  if (U.includes('KG')) return 'KG'
  return U   // 兜底展示原值（极少数自定义单位）
}
const rangeText = (r) => {
  // 支持 [min,max] / "min-max" / "[min,max]"
  if (Array.isArray(r?.range)) {
    const [a, b] = r.range
    const right = Number(b) === DEFAULT_MAX ? '∞' : stripZeros(b)
    return `${stripZeros(a)}-${right}`
  }
  if (typeof r?.range === 'string') {
    const s = r.range.replace(/[\[\]\s]/g, '').replace(',', '-')
    const parts = s.split('-')
    if (parts.length === 2) {
      const a = stripZeros(parts[0])
      const rb = Number(parts[1])
      const b = (rb === DEFAULT_MAX) ? '∞' : stripZeros(parts[1])
      return `${a}-${b}`
    }
    return s || '-'
  }
  // 一口价通常无区间，显示 "-"
  return '-'
}
const priceDesc = (r) => {
  // 一口价
  if (r?.prize !== undefined && r?.prize !== null && r?.prize !== '') {
    return `一口价 ${stripZeros(r.prize)} 元`
  }
  // 单价 + 基础费 + 包多少
  const unit = unitOf(r) || ''
  const up = (r?.unit_price ?? r?.price)
  const segs = []
  if (up !== undefined && up !== null && String(up) !== '') {
    segs.push(`单价 ${stripZeros(up)} 元${unit ? '/' + unit : ''}`)
  }
  if (r?.base_fees !== undefined && r?.base_fees !== '') {
    segs.push(`${stripZeros(r.base_fees)} 元`)
  }
  if (r?.deduction_value !== undefined && r?.deduction_value !== '') {
    segs.push(`含 ${stripZeros(r.deduction_value)}${unit}`)
  }
  return segs.length ? segs.join('， ') : '-'
}

/* ========= data ========= */
const ruleArr = computed(() => toArray(props.rules))
</script>

<style scoped>
.viewer-table-head,
.viewer-row {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  margin-bottom: 8rpx;
}

.viewer-table-head {
  font-weight: bold;
  background: #f6f8fa;
}

.viewer-table-head text,
.viewer-row text {
  padding: 0 6rpx;
}

.col-unit {  flex: 0 0 120rpx; }
.col-type {  flex: 0 0 120rpx; }
.col-range { flex: 1 1 250rpx; }
.col-desc  {
  flex: 3 3 800rpx;
  color: #34495e;
  word-break: break-all;
}
</style>
