<template>
  <view class="rule-editor" :class="{ 'dense': dense }">
    <!-- 计量切换 -->
    <view class="control-grid">
      <view class="row">
        <text class="label">计量</text>
        <view class="radios">
          <label class="radio" @click="setUnit('KG')" :aria-checked="activeUnit === 'KG'" role="radio">
            <view class="dot" :class="{ on: activeUnit === 'KG' }"></view><text>KG</text>
          </label>
          <label class="radio" @click="setUnit('CBM')" :aria-checked="activeUnit === 'CBM'" role="radio">
            <view class="dot" :class="{ on: activeUnit === 'CBM' }"></view><text>CBM</text>
          </label>
          <label class="radio" @click="setUnit('PCS')" :aria-checked="activeUnit === 'PCS'" role="radio">
            <view class="dot" :class="{ on: activeUnit === 'PCS' }"></view><text>件</text>
          </label>
        </view>
      </view>
    </view>

    <!-- 区间表格（KG/CBM/PCS 统一） -->
    <view class="thead sticky">
      <text class="col-range">区间范围</text>
      <text class="col-price">单价(/{{ activeUnit }})</text>
      <text class="col-prize">一口价(总价)</text>
      <text class="col-base">基础费(最低)</text>
      <text class="col-deduct">包多少({{ activeUnit }})</text>
      <text class="col-step" v-if="activeUnit === 'PCS'">最小计费单位</text>
      <text class="col-action"></text>
    </view>

    <view class="row" v-for="(r, i) in curr.rows" :key="`${activeUnit}-${i}`">
      <!-- 双输入区间 -->
      <view class="col-range range-split">
        <uni-easyinput type="number" v-model="r._min" placeholder="起(>=0)" @blur="normalizeRow(i)" />
        <text class="dash">—</text>
        <uni-easyinput type="number" v-model="r._max" placeholder="止(空=∞)" @blur="normalizeRow(i)" />
      </view>

      <!-- 按单价 / 一口价（二选一，均可出现；验证时要求至少填一个） -->
      <uni-easyinput class="col-price" type="number" v-model="r.unit_price" placeholder="单价" />
      <uni-easyinput class="col-prize" type="number" v-model="r._prize" placeholder="总价" />

      <uni-easyinput class="col-base" type="number" v-model="r.base_fees" placeholder="可选" />
      <uni-easyinput class="col-deduct" type="number" v-model="r.deduction_value" placeholder="可选" />
      
      <!-- 最小计费单位（仅件计费显示） -->
      <uni-easyinput v-if="activeUnit === 'PCS'" class="col-step" type="number" v-model="r._minimum_unit" placeholder="默认0(不限制)" />

      <view class="col-action">
        <button size="mini" type="warn" plain @click="removeRow(i)">删</button>
      </view>
    </view>

    <view class="add-row">
      <button size="mini" type="primary" plain @click="addRow">+ 添加区间</button>
    </view>

    <view class="save">
      <button size="default" type="success" @click="save()">保存规则</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, computed, watch, ref } from 'vue'

const DEFAULT_MAX = '99999999'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  dense: { type: Boolean, default: true }
})
const emit = defineEmits(['update:modelValue', 'save'])

/* ---------- utils ---------- */
function firstNonNil(obj, ...keys) {
  for (const k of keys) {
    if (obj?.[k] !== undefined && obj?.[k] !== null && obj?.[k] !== '') return obj[k]
  }
  return undefined
}
function toUpper(str, def = '') {
  if (str === undefined || str === null || str === '') return def
  return String(str).toUpperCase()
}
function pickUnit(obj, def = 'KG') {
  const raw = firstNonNil(obj, 'prize_type', 'unit', 'unit_type', 'price_unit', 'type', '计量', '单位', 'danwei', 'dw')
  const u = toUpper(raw, def)
  if (u.includes('KG')) return 'KG'
  if (u.includes('CBM') || u.includes('M3')) return 'CBM'
  if (u.includes('PCS') || u.includes('件')) return 'PCS'
  return u || def
}
function cleanNumForInput(v) {
  if (v === '' || v === undefined || v === null) return ''
  const m = String(v).match(/-?\d+(\.\d+)?/)
  return m ? m[0] : ''
}
function toNumOrBlank(v) {
  if (v === '' || v === undefined || v === null) return ''
  const n = Number(v)
  return isNaN(n) ? '' : n
}
function parseRangeString(s) {
  if (!s) return null
  const [a, b] = String(s).split('-').map(x => x.trim())
  const min = Number(a)
  const hasB = !(b === undefined || b === null || b === '')
  const max = hasB ? Number(b) : Number(DEFAULT_MAX)
  if (isNaN(min) || isNaN(max)) return null
  return { min, max }
}
function parseRangeFields(minVal, maxVal) {
  const hasMin = !(minVal === '' || minVal === undefined || minVal === null)
  const hasMax = !(maxVal === '' || maxVal === undefined || maxVal === null)
  if (!hasMin && !hasMax) return null
  const min = hasMin ? Number(minVal) : NaN
  const max = hasMax ? Number(maxVal) : Number(DEFAULT_MAX)
  if (Number.isNaN(min) || Number.isNaN(max)) return null
  return { min, max }
}
function stripZerosStr(s) {
  return String(s).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1')
}
function numToInput(n) {
  if (n === '' || n === undefined || n === null) return ''
  const x = Number(n)
  if (!Number.isFinite(x)) return ''
  return stripZerosStr(x)
}
function buildRangeFromRow(r) {
  const p = parseRangeFields(r._min, r._max)
  if (!p) return (r.range || '')
  const { min, max } = p
  return `${stripZerosStr(min)}-${stripZerosStr(max)}`
}
function normalizeRow(idx) {
  const r = curr.value.rows[idx]
  const p = parseRangeFields(r._min, r._max)
  if (!p) return
  const { min, max } = p
  if (min > max) { uni.showToast({ title: '开始不能大于结束', icon: 'none' }); return }
  r.range = buildRangeFromRow(r)
}

/* ✅ 新增：空值&空白行判断（校验/导出会用到） */
function isEmpty(v) {
  return v === '' || v === undefined || v === null
}
function isBlankRow(r) {
  return isEmpty(r._min) &&
         isEmpty(r._max) &&
         isEmpty(r.unit_price) &&
         isEmpty(r._prize) &&
         isEmpty(r.base_fees) &&
         isEmpty(r.deduction_value) &&
         isEmpty(r._minimum_unit) &&
         (!r.range || r.range === '')
}

function validateTierCoverageAndOverlap(group, unitLabel = 'KG') {
  // 仅校验"非空白行"，允许该单位完全为空（CBM 可为空）
  const rows = (group.rows || []).filter(r => !isBlankRow(r))
  const issues = []
  if (rows.length === 0) return issues

  // 解析区间 + 基本校验
  let ranges = rows.map((r, i) => {
    const pr = (r._min !== undefined || r._max !== undefined)
      ? parseRangeFields(r._min, r._max)
      : parseRangeString(r.range)

    if (!pr) {
      issues.push(`${unitLabel} 第 ${i + 1} 行区间格式错误（示例：30-50；上限空=∞）`)
      return null
    }

    const { min, max } = pr
    if (!(Number.isFinite(min) && Number.isFinite(max))) {
      issues.push(`${unitLabel} 第 ${i + 1} 行区间需为数字`)
      return null
    }
    if (min >= max) issues.push(`${unitLabel} 第 ${i + 1} 行区间应满足 min < max`)

    // 至少有"单价"或"一口价"之一
    const hasUnitPrice = r.unit_price !== '' && !isNaN(Number(r.unit_price))
    const hasPrize     = r._prize     !== '' && !isNaN(Number(r._prize))
    if (!hasUnitPrice && !hasPrize) {
      issues.push(`${unitLabel} 第 ${i + 1} 行需填写 单价 或 一口价`)
    }

    return { min, max, i }
  })

  if (issues.length) return issues

  // 仅检查"中间的"：相邻区间不得重叠、不得断档
  ranges = ranges.filter(Boolean).sort((a, b) => a.min - b.min)
  for (let i = 1; i < ranges.length; i++) {
    const p = ranges[i - 1]
    const c = ranges[i]
    if (c.min < p.max) issues.push(`${unitLabel} 第 ${p.i + 1} 与第 ${c.i + 1} 行区间重叠（${p.min}-${p.max} 与 ${c.min}-${c.max}）`)
    if (c.min > p.max) issues.push(`${unitLabel} 在 ${p.max} 与 ${c.min} 之间存在缺口`)
  }

  // 不再要求从 0 开始，也不再要求到 ∞ 结束
  return issues
}


/* ---------- state ---------- */
const state = reactive({
  KG:  { rows: [] },
  CBM: { rows: [] },
  PCS: { rows: [] }
})
const activeUnit = ref('KG')
const curr = computed(() => state[activeUnit.value])

/* ---------- ingest / emit ---------- */
function ingest(arr) {
  state.KG.rows = []
  state.CBM.rows = []
  state.PCS.rows = []

  ;(arr || []).forEach(raw => {
    const unit = pickUnit(raw, 'KG')

    // 区间
    let rangeStr = firstNonNil(raw, 'range', 'range_text', 'rangeStr', '区间')
    if (!rangeStr) {
      const min = firstNonNil(raw, 'min', 'start', 'from', 'lower', 'range_min', 'left', 'begin', '起')
      const max = firstNonNil(raw, 'max', 'end', 'to', 'upper', 'range_max', 'right', 'finish', '止')
      if (min !== undefined) rangeStr = `${min}-${(max ?? DEFAULT_MAX)}`
    }
    const pr = parseRangeString(rangeStr)
    const _min = pr ? numToInput(pr.min) : ''
    const _max = pr ? (pr.max === Number(DEFAULT_MAX) ? '' : numToInput(pr.max)) : ''

    // 行级：单价 or 一口价
    const rowUnitPrice = cleanNumForInput(firstNonNil(raw, 'unit_price', 'price', 'unitPrice', '单价'))
    const rowPrize     = cleanNumForInput(firstNonNil(raw, 'prize', 'flat', 'flat_price', 'fixed_price', '一口价', '固定价'))

    state[unit].rows.push({
      range: pr ? `${stripZerosStr(pr.min)}-${stripZerosStr(pr.max)}` : (rangeStr || ''),
      _min,
      _max,
      unit_price: rowUnitPrice,
      _prize: rowPrize,
      base_fees:        cleanNumForInput(firstNonNil(raw, 'base_fees', 'base_fee', 'basic_fee', '基础费')),
      deduction_value:  cleanNumForInput(firstNonNil(raw, 'deduction_value', 'deduct', 'deduction', '扣减')),
      _minimum_unit:  cleanNumForInput(firstNonNil(raw, 'minimum_unit', 'step_size', 'stepSize', '最小计费单位', '计费步长')) || '0',
    })
  })

  // 如果没有任何数据，给 KG 一行空白占位
  if (state.KG.rows.length === 0 && state.CBM.rows.length === 0 && state.PCS.rows.length === 0) {
    state.KG.rows.push({ range: '', _min: '', _max: '', unit_price: '', _prize: '', base_fees: '', deduction_value: '', _minimum_unit: '0' })
  }
}

function emitOut() {
  const out = []

  // 统一处理：KG/CBM/PCS 区间计费
  const toRows = (unit, group) => {
    (group.rows || []).forEach(r => {
      // ✅ 忽略完全空白行
      if (isBlankRow(r)) return

      const rangeText = buildRangeFromRow(r) || r.range
      if (!rangeText) return

      const item = { range: rangeText, prize_type: unit }
      const prize = toNumOrBlank(r._prize)
      const up    = toNumOrBlank(r.unit_price)
      if (prize !== '') item.prize = prize
      if (prize === '' && up !== '') item.unit_price = up   // 二选一：优先"一口价"
      const bf = toNumOrBlank(r.base_fees);       if (bf !== '') item.base_fees = bf
      const dv = toNumOrBlank(r.deduction_value); if (dv !== '') item.deduction_value = dv
      const mu = toNumOrBlank(r._minimum_unit);     if (mu !== '' && mu !== 0) item.minimum_unit = mu  // 只有非0时才保存，兼容老数据
      out.push(item)
    })
  }
  toRows('KG',  state.KG)
  toRows('CBM', state.CBM)
  toRows('PCS', state.PCS)

  emit('update:modelValue', out)
  return out
}

watch(() => props.modelValue, v => ingest(v), { immediate: true, deep: true })

/* ---------- interactions ---------- */
function setUnit(u) { activeUnit.value = u }
function addRow() {
  curr.value.rows.push({
    range: '', _min: '', _max: '',
    unit_price: '', _prize: '',
    base_fees: '', deduction_value: '', _minimum_unit: '0'
  })
}
function removeRow(i) { curr.value.rows.splice(i, 1); emitOut() }

/* ---------- save ---------- */
function save(silent = false) {
  // ✅ 至少 KG/CBM/PCS 有一侧存在"非空白行"
  const hasAnyRows =
    (state.KG.rows  || []).some(r => !isBlankRow(r)) ||
    (state.CBM.rows || []).some(r => !isBlankRow(r)) ||
    (state.PCS.rows || []).some(r => !isBlankRow(r))

  if (!hasAnyRows) {
    uni.showToast({ title: '请至少配置 KG、CBM 或 件 的规则', icon: 'none' })
    return { ok: false }
  }

  const problems = [
    ...validateTierCoverageAndOverlap(state.KG,  'KG'),
    ...validateTierCoverageAndOverlap(state.CBM, 'CBM'),
    ...validateTierCoverageAndOverlap(state.PCS, '件'),
  ]
  if (problems.length) {
    uni.showToast({ title: problems[0], icon: 'none' })
    return { ok: false }
  }

  const out = emitOut()
  emit('save', out)
  if (!silent) uni.showToast({ title: '规则已保存', icon: 'success' })
  return { ok: true, data: out }
}

defineExpose({ save })
</script>


<style scoped>
.rule-editor {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.rule-editor.dense .thead,
.rule-editor.dense .row {
  font-size: 24rpx;
}

.thead,
.row {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.thead {
  font-weight: 600;
  background: #f6f8fa;
  padding: 8rpx 10rpx;
  border-radius: 8rpx;
  margin-right: 20px;
}

.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
}

.col-range {
  flex: 1 1 220rpx;
  min-width: 200rpx;
  /* max-width: 400rpx; */
}

.col-price {
  flex: 0 0 160rpx;
  text-align: center;
}

.col-prize {
  flex: 0 0 160rpx;
  text-align: center;
}

.col-base {
  flex: 0 0 140rpx;
  text-align: center;
}

.col-deduct {
  flex: 0 0 140rpx;
  text-align: center;
}

.col-step {
  flex: 0 0 120rpx;
  text-align: center;
}

.col-action {
  flex: 0 0 80rpx;
  text-align: right;
}

.add-row {
  margin-top: 8rpx;
}

.save {
  text-align: right;
  margin-top: 8rpx;
}

::v-deep .uni-easyinput {
  width: 100%;
  margin-right: 10rpx;
}

@media (max-width: 750px) {
  .thead {
    display: none;
  }

  .row {
    flex-wrap: wrap;
    gap: 8rpx 12rpx;
    padding: 8rpx 0;
    border-bottom: 1px dashed #eee;
  }

  .col-range,
  .col-price,
  .col-prize,
  .col-base,
  .col-deduct,
  .col-step {
    flex: 1 1 calc(50% - 12rpx);
    min-width: 42%;
    text-align: left;
  }

  .col-action {
    flex: 0 0 100%;
    text-align: right;
  }
}

/* 顶部计量单选 */
.control-grid {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin: 4rpx 0 12rpx;
}

.control-grid .row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.control-grid .label {
  width: 140rpx;
  color: #333;
  font-weight: 600;
}

.radios {
  display: flex;
  gap: 28rpx;
  align-items: center;
}

.radio {
  display: flex;
  align-items: center;
  gap: 10rpx;
  user-select: none;
}

.dot {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  border: 2rpx solid #c0c4cc;
  background: #fff;
  position: relative;
}

.dot.on {
  border-color: #1f7ae0;
}

.dot.on::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: #1f7ae0;
  transform: translate(-50%, -50%);
}

/* 区间双输入 */
.range-split {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.dash {
  width: 24rpx;
  text-align: center;
  color: #666;
}
</style>
