<template>
  <view class="rule-editor" :class="{'dense': dense}">
    <!-- 顶部：计量 -->
    <view class="control-grid">
      <view class="row">
        <text class="label">计量</text>
        <view class="radios">
          <label class="radio" @click="setUnit('KG')" :aria-checked="activeUnit === 'KG'" role="radio">
            <view class="dot" :class="{ on: activeUnit === 'KG' }"></view>
            <text>KG</text>
          </label>
          <label class="radio" @click="setUnit('CBM')" :aria-checked="activeUnit === 'CBM'" role="radio">
            <view class="dot" :class="{ on: activeUnit === 'CBM' }"></view>
            <text>CBM</text>
          </label>
        </view>
      </view>
    </view>

    <!-- 一口价 -->
    <view v-if="curr.mode==='flat'" class="flat-row">
      <text class="label">一口价（总价）</text>
      <uni-easyinput type="number" v-model="curr.flat.prize" placeholder="请输入总价" />
    </view>

    <!-- 区间价 -->
    <template v-else>
      <view class="thead sticky">
        <text class="col-range">区间范围</text>
        <text class="col-price">单价(/{{ activeUnit }})</text>
        <text class="col-base">基础费(最低)</text>
        <text class="col-deduct">包多少</text>
        <text class="col-action"></text>
      </view>

      <view class="row" v-for="(r,i) in curr.rows" :key="`${activeUnit}-${i}`">
        <!-- ✅ 双输入：起止都为数字；止留空视为 ∞ -->
        <view class="col-range range-split">
          <uni-easyinput
            type="number"
            v-model="r._min"
            placeholder="起(>=0)"
            @blur="normalizeRow(i)"
          />
          <text class="dash">—</text>
          <uni-easyinput
            type="number"
            v-model="r._max"
            placeholder="止(空=∞)"
            @blur="normalizeRow(i)"
          />
        </view>

        <uni-easyinput class="col-price" type="number" v-model="r.unit_price" placeholder="单价" />
        <uni-easyinput class="col-base"  type="number" v-model="r.base_fees" placeholder="可选" />
        <uni-easyinput class="col-deduct" type="number" v-model="r.deduction_value" placeholder="可选" />
        <view class="col-action">
          <button size="mini" type="warn" plain @click="removeRow(i)">删</button>
        </view>
      </view>

      <view class="add-row">
        <button size="mini" type="primary" plain @click="addRow">+ 添加区间</button>
      </view>
    </template>

    <!-- 上面的保存：可点可不点；父页可静默调用 save(true) -->
    <view class="save">
      <button size="default" type="success" @click="save()">保存规则</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, computed, watch, ref } from 'vue'

/** ====== 配置 ====== */
const DEFAULT_MAX = '99999999'
const DEBUG = false

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  dense: { type: Boolean, default: true }
})
const emit = defineEmits(['update:modelValue','save'])

/** ====== 工具函数 ====== */
function firstNonNil(obj, ...keys){
  for (const k of keys){
    if (obj?.[k] !== undefined && obj?.[k] !== null && obj?.[k] !== '') return obj[k]
  }
  return undefined
}
function toUpper(str, def=''){ if (str===undefined || str===null || str==='') return def; return String(str).toUpperCase() }
function pickUnit(obj, def='KG'){
  const raw = firstNonNil(obj,'prize_type','unit','unit_type','price_unit','type','计价方式','单位','danwei','dw')
  const u = toUpper(raw, def)
  if (u.includes('KG')) return 'KG'
  if (u.includes('CBM') || u.includes('M3')) return 'CBM'
  return u || def
}
function cleanNumForInput(v){ if (v===''||v===undefined||v===null) return ''; const m = String(v).match(/-?\d+(\.\d+)?/); return m?m[0]:'' }
function toNumOrBlank(v){ if (v===''||v===undefined||v===null) return ''; const n=Number(v); return isNaN(n)?'':n }
function parseRangeString(s){
  if (!s) return null
  const [a,b] = String(s).split('-').map(x=>x.trim())
  const min = Number(a)
  const hasB = !(b===undefined || b===null || b==='')
  const max = hasB ? Number(b) : Number(DEFAULT_MAX)
  if (isNaN(min) || isNaN(max)) return null
  return { min, max }
}

/** ====== 双输入区间工具 ====== */
function parseRangeFields(minVal, maxVal){
  const hasMin = !(minVal===''||minVal===undefined||minVal===null)
  const hasMax = !(maxVal===''||maxVal===undefined||maxVal===null)
  if (!hasMin && !hasMax) return null
  const min = hasMin ? Number(minVal) : NaN
  const max = hasMax ? Number(maxVal) : Number(DEFAULT_MAX)
  if (Number.isNaN(min) || Number.isNaN(max)) return null
  return { min, max }
}
function stripZerosStr(s){ return String(s).replace(/\.0+$/,'').replace(/(\.\d*[1-9])0+$/,'$1') }
function numToInput(n){
  if (n===''||n===undefined||n===null) return ''
  const x = Number(n); if (!Number.isFinite(x)) return ''
  return stripZerosStr(x)
}
function buildRangeFromRow(r){
  const p = parseRangeFields(r._min, r._max)
  if (!p) return (r.range || '')
  const { min, max } = p
  return `${stripZerosStr(min)}-${stripZerosStr(max)}`
}
function normalizeRow(idx){
  const r = curr.value.rows[idx]
  const p = parseRangeFields(r._min, r._max)
  if (!p) return
  const { min, max } = p
  if (min > max){ uni.showToast({ title:'开始不能大于结束', icon:'none' }); return }
  r.range = buildRangeFromRow(r)
}

/** ====== 覆盖/重叠校验 ====== */
function validateTierCoverageAndOverlap(group, unitLabel='KG'){
  if (group.mode==='flat') return []
  const issues=[]
  if (!group.rows.length){ issues.push(`${unitLabel} 需至少一条区间`); return issues }

  let ranges = group.rows.map((r,i)=>{
    const pr = (r._min!==undefined || r._max!==undefined)
      ? parseRangeFields(r._min, r._max)
      : parseRangeString(r.range)
    if (!pr){ issues.push(`${unitLabel} 第 ${i+1} 行区间格式错误（请填数字，示例：0~40；上限空=∞）`); return null }
    const { min, max } = pr
    if (!(Number.isFinite(min) && Number.isFinite(max))){ issues.push(`${unitLabel} 第 ${i+1} 行区间需为数字`); return null }
    if (min >= max) issues.push(`${unitLabel} 第 ${i+1} 行区间应满足 min < max`)
    if (r.unit_price==='' || isNaN(Number(r.unit_price))) issues.push(`${unitLabel} 第 ${i+1} 行单价未填写或非法`)
    return { min, max, i }
  })
  if (issues.length) return issues

  ranges = ranges.filter(Boolean).sort((a,b)=>a.min-b.min)
  if (ranges[0].min !== 0) issues.push(`${unitLabel} 区间应从 0 开始（当前最小为 ${ranges[0].min}）`)
  for (let i=1;i<ranges.length;i++){
    const p = ranges[i-1], c = ranges[i]
    if (c.min < p.max) issues.push(`${unitLabel} 第 ${p.i+1} 与第 ${c.i+1} 行区间重叠（${p.min}-${p.max} 与 ${c.min}-${c.max}）`)
    if (c.min > p.max) issues.push(`${unitLabel} 在 ${p.max} 与 ${c.min} 之间存在缺口`)
  }
  const lastMax = ranges[ranges.length-1].max
  if (lastMax !== Number(DEFAULT_MAX)) issues.push(`${unitLabel} 末尾未覆盖到 ${DEFAULT_MAX}（当前截止到 ${lastMax}）`)
  return issues
}

/** ====== 状态 ====== */
const state = reactive({
  KG:  { mode:'tiered', rows:[], flat:{ prize:'' } },
  CBM: { mode:'tiered', rows:[], flat:{ prize:'' } },
})
const activeUnit = ref('KG')
const curr = computed(()=> state[activeUnit.value])

/** ====== ingest / emit ====== */
function ingest(arr){
  state.KG  = { mode:'tiered', rows:[], flat:{ prize:'' } }
  state.CBM = { mode:'tiered', rows:[], flat:{ prize:'' } }

  if (DEBUG) console.log('[RuleFeeEditor] ingest raw:', JSON.parse(JSON.stringify(arr||[])))

  ;(arr||[]).forEach(raw=>{
    const unit = pickUnit(raw,'KG')

    // 一口价
    const flatVal = firstNonNil(raw,'prize','flat','flat_price','fixed_price','一口价','固定价')
    const hasFlat = flatVal!==undefined && flatVal!==null && flatVal!==''
    if (hasFlat){ state[unit].mode='flat'; state[unit].flat.prize=cleanNumForInput(flatVal); return }

    // 区间
    let rangeStr = firstNonNil(raw,'range','range_text','rangeStr','区间')
    if (!rangeStr){
      const min = firstNonNil(raw,'min','start','from','lower','range_min','left','begin','起')
      const max = firstNonNil(raw,'max','end','to','upper','range_max','right','finish','止')
      if (min !== undefined) rangeStr = `${min}-${(max ?? DEFAULT_MAX)}`
    }

    const pr = parseRangeString(rangeStr)
    const _min = pr ? numToInput(pr.min) : ''
    const _max = pr ? (pr.max===Number(DEFAULT_MAX)?'':numToInput(pr.max)) : ''

    state[unit].rows.push({
      range: pr ? `${stripZerosStr(pr.min)}-${stripZerosStr(pr.max)}` : (rangeStr || ''),
      _min, _max,
      unit_price: cleanNumForInput(firstNonNil(raw,'unit_price','price','unitPrice','单价')),
      base_fees:  cleanNumForInput(firstNonNil(raw,'base_fees','base_fee','basic_fee','基础费')),
      deduction_value: cleanNumForInput(firstNonNil(raw,'deduction_value','deduct','deduction','扣减')),
    })
  })

  if (state.KG.mode==='tiered' && state.KG.rows.length===0 &&
      state.CBM.mode==='tiered' && state.CBM.rows.length===0){
    state.KG.rows.push({ range:'', _min:'', _max:'', unit_price:'', base_fees:'', deduction_value:'' })
  }

  if (DEBUG) console.log('[RuleFeeEditor] state ->', JSON.parse(JSON.stringify(state)))
}

function emitOut(){
  const out=[]
  const toRows=(unit, group)=>{
    if (group.mode==='flat'){
      const p = toNumOrBlank(group.flat.prize)
      if (p!=='') out.push({ range:`0-${DEFAULT_MAX}`, prize: p, prize_type: unit })
    } else {
      group.rows.forEach(r=>{
        const rangeText = buildRangeFromRow(r) || r.range
        if (!rangeText) return
        const item = { range: rangeText, prize_type: unit }
        const up = toNumOrBlank(r.unit_price); if (up!=='') item.unit_price = up
        const bf = toNumOrBlank(r.base_fees);  if (bf!=='') item.base_fees  = bf
        const dv = toNumOrBlank(r.deduction_value); if (dv!=='') item.deduction_value = dv
        out.push(item)
      })
    }
  }
  toRows('KG', state.KG); toRows('CBM', state.CBM)
  emit('update:modelValue', out)
  return out
}

watch(()=>props.modelValue, v=> ingest(v), { immediate:true, deep:true })

/** ====== 交互 ====== */
function setUnit(u){ activeUnit.value = u }
function setMode(mode){ curr.value.mode = mode; if (mode==='flat') curr.value.rows = []; emitOut() }
function addRow(){ curr.value.rows.push({ range:'', _min:'', _max:'', unit_price:'', base_fees:'', deduction_value:'' }) }
function removeRow(i){ curr.value.rows.splice(i,1); emitOut() }

/** ====== 保存（可静默） ====== */
function save(silent = false){
  const quick = g => g.mode==='flat'
    ? (g.flat.prize==='' || isNaN(Number(g.flat.prize)) ? '请输入一口价' : null)
    : (g.rows.some(r=>{
        const p = parseRangeFields(r._min, r._max) || parseRangeString(r.range)
        return !p || r.unit_price==='' || isNaN(Number(r.unit_price))
      }) ? '区间或单价未填写' : null)

  const err = quick(state.KG) || quick(state.CBM)
  if (err){ uni.showToast({ title: err, icon: 'none' }); return { ok:false } }

  const problems = [
    ...validateTierCoverageAndOverlap(state.KG, 'KG'),
    // 如需校验 CBM，解除下一行注释
    // ...validateTierCoverageAndOverlap(state.CBM, 'CBM'),
  ]
  if (problems.length){ uni.showToast({ title: problems[0], icon: 'none' }); return { ok:false } }

  const out = emitOut()
  emit('save', out)
  if (!silent) uni.showToast({ title:'规则已保存', icon:'success' })
  return { ok:true, data: out }
}

defineExpose({ save })
</script>

<style scoped>
.rule-editor{ display:flex; flex-direction:column; gap:16rpx; }
.rule-editor.dense .card, .rule-editor.dense .thead, .rule-editor.dense .row{ font-size:24rpx; }

.thead,.row{ display:flex; align-items:center; margin-bottom:8rpx; }
.thead{ font-weight:bold; background:#f6f8fa; padding:8rpx 10rpx; border-radius:8rpx; }
.sticky{ position: sticky; top: 0; z-index: 1; }

.col-range{ flex: 1 1 220rpx; min-width: 180rpx; }
.col-price{ flex: 0 0 160rpx; text-align:center; }
.col-base{  flex: 0 0 140rpx; text-align:center; }
.col-deduct{flex: 0 0 140rpx; text-align:center; }
.col-action{flex: 0 0 80rpx; text-align:right; }

.add-row{ margin-top:8rpx; }
.save{ text-align:right; margin-top:8rpx; }

::v-deep .uni-easyinput { width:100%; }

@media (max-width: 750px){
  .thead{ display:none; }
  .row{ flex-wrap:wrap; gap:8rpx 12rpx; padding:8rpx 0; border-bottom:1px dashed #eee; }
  .col-range,.col-price,.col-base,.col-deduct{ flex:1 1 calc(50% - 12rpx); min-width:42%; text-align:left; }
  .col-action{ flex:0 0 100%; text-align:right; }
}

/* 单选外观 */
.control-grid{ display:flex; flex-direction:column; gap:14rpx; margin:4rpx 0 12rpx; }
.control-grid .row{ display:flex; align-items:center; gap:12rpx; }
.control-grid .label{ width:140rpx; color:#333; font-weight:600; }
.radios{ display:flex; gap:28rpx; align-items:center; }
.radio{ display:flex; align-items:center; gap:10rpx; user-select:none; }
.dot{ width:32rpx;height:32rpx;border-radius:50%;border:2rpx solid #c0c4cc; background:#fff; position:relative; }
.dot.on{ border-color:#1f7ae0; }
.dot.on::after{ content:''; position:absolute; left:50%; top:50%; width:18rpx; height:18rpx; border-radius:50%; background:#1f7ae0; transform:translate(-50%,-50%); }

/* 区间双输入 */
.range-split{ display:flex; align-items:center; gap:8rpx; }
.range-split .uni-easyinput{ flex:1 1 0; }
.dash{ width:24rpx; text-align:center; color:#666; }
</style>
