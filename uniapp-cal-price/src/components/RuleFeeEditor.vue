<template>
    <view class="rule-editor">
      <!-- KG 分区 -->
      <view class="card">
        <view class="card-head">
          <text class="title">KG 规则</text>
          <picker :range="modeOptions" range-key="label" :value="kgModeIndex" @change="e=>setMode('KG', e)">
            <view class="picker">{{ kgModeLabel }}</view>
          </picker>
        </view>
  
        <!-- KG 一口价 -->
        <view v-if="kg.mode==='flat'" class="flat-row">
          <text class="label">一口价（总价）</text>
          <uni-easyinput type="number" v-model="kg.flat.prize" placeholder="请输入总价" />
        </view>
  
        <!-- KG 区间价 -->
        <template v-else>
          <view class="thead">
            <text class="col-range">区间</text>
            <text class="col-price">单价(/KG)</text>
            <text class="col-base">基础费</text>
            <text class="col-deduct">扣减</text>
            <text class="col-action"></text>
          </view>
          <view class="row" v-for="(r,i) in kg.rows" :key="'kg-'+i">
            <input class="col-range" v-model="r.range" placeholder="如 0-40" />
            <uni-easyinput class="col-price" type="number" v-model="r.unit_price" placeholder="单价" />
            <uni-easyinput class="col-base" type="number" v-model="r.base_fees" placeholder="可选" />
            <uni-easyinput class="col-deduct" type="number" v-model="r.deduction_value" placeholder="可选" />
            <view class="col-action">
              <button size="mini" type="warn" plain @click="removeRow('KG', i)">删</button>
            </view>
          </view>
          <view class="add-row">
            <button size="mini" type="primary" plain @click="addRow('KG')">+ 添加区间</button>
          </view>
        </template>
      </view>
  
      <!-- CBM 分区 -->
      <view class="card">
        <view class="card-head">
          <text class="title">CBM 规则</text>
          <picker :range="modeOptions" range-key="label" :value="cbmModeIndex" @change="e=>setMode('CBM', e)">
            <view class="picker">{{ cbmModeLabel }}</view>
          </picker>
        </view>
  
        <!-- CBM 一口价 -->
        <view v-if="cbm.mode==='flat'" class="flat-row">
          <text class="label">一口价（总价）</text>
          <uni-easyinput type="number" v-model="cbm.flat.prize" placeholder="请输入总价" />
        </view>
  
        <!-- CBM 区间价 -->
        <template v-else>
          <view class="thead">
            <text class="col-range">区间</text>
            <text class="col-price">单价(/CBM)</text>
            <text class="col-base">基础费</text>
            <text class="col-deduct">扣减</text>
            <text class="col-action"></text>
          </view>
          <view class="row" v-for="(r,i) in cbm.rows" :key="'cbm-'+i">
            <input class="col-range" v-model="r.range" placeholder="如 0-1" />
            <uni-easyinput class="col-price" type="number" v-model="r.unit_price" placeholder="单价" />
            <uni-easyinput class="col-base" type="number" v-model="r.base_fees" placeholder="可选" />
            <uni-easyinput class="col-deduct" type="number" v-model="r.deduction_value" placeholder="可选" />
            <view class="col-action">
              <button size="mini" type="warn" plain @click="removeRow('CBM', i)">删</button>
            </view>
          </view>
          <view class="add-row">
            <button size="mini" type="primary" plain @click="addRow('CBM')">+ 添加区间</button>
          </view>
        </template>
      </view>
  
      <view class="save">
        <button size="default" type="success" @click="save">保存规则</button>
      </view>
    </view>
  </template>
  
  <script setup>
  import { reactive, computed, watch } from 'vue'
  
  const DEFAULT_MAX = '99999999'

/** 把 'A-B' 解析为数字区间；若 B 为空，取 DEFAULT_MAX */
function parseRangeString(s) {
    if (!s) return null
    const [a, b] = String(s).split('-').map(x => x.trim())
    const min = Number(a)
    const hasB = !(b === undefined || b === null || b === '')
    const max = hasB ? Number(b) : Number(DEFAULT_MAX)
    if (isNaN(min) || isNaN(max)) return null
    return { min, max }
}

/** 校验一个单位分组（区间价模式）：
 *  1) 数字合法且 min < max
 *  2) 区间按 [min,max) 互不重叠
 *  3) 从 0 开始且连续覆盖到 DEFAULT_MAX
 */
function validateTierCoverageAndOverlap(group, unitLabel = 'KG') {
    if (group.mode === 'flat') return []  // 一口价无需区间校验
    const issues = []
    if (!group.rows.length) {
        issues.push(`${unitLabel} 需至少一条区间`)
        return issues
    }

    // 解析+标准化
    let ranges = group.rows.map((r, i) => {
        const pr = parseRangeString(r.range)
        if (!pr) {
            issues.push(`${unitLabel} 第 ${i + 1} 行区间格式错误（示例：0-40 或 40-${DEFAULT_MAX}）`)
            return null
        }
        const { min, max } = pr
        if (!(Number.isFinite(min) && Number.isFinite(max))) {
            issues.push(`${unitLabel} 第 ${i + 1} 行区间需为数字`)
            return null
        }
        if (min >= max) {
            issues.push(`${unitLabel} 第 ${i + 1} 行区间应满足 min < max`)
        }
        // 单价校验
        if (r.unit_price === '' || isNaN(Number(r.unit_price))) {
            issues.push(`${unitLabel} 第 ${i + 1} 行单价未填写或非法`)
        }
        return { min, max, i }
    })

    if (issues.length) return issues
    ranges = ranges.filter(Boolean)

    // 按 min 排序
    ranges.sort((a, b) => a.min - b.min)

    // 覆盖：从 0 开始
    if (ranges[0].min !== 0) {
        issues.push(`${unitLabel} 区间应从 0 开始（当前最小为 ${ranges[0].min}）`)
    }

    // 连续与不重叠（右开区间：前一段 max == 下一段 min 视为连续）
    for (let i = 1; i < ranges.length; i++) {
        const prev = ranges[i - 1]
        const curr = ranges[i]
        if (curr.min < prev.max) {
            issues.push(`${unitLabel} 第 ${prev.i + 1} 与第 ${curr.i + 1} 行区间重叠（${prev.min}-${prev.max} 与 ${curr.min}-${curr.max}）`)
        }
        if (curr.min > prev.max) {
            issues.push(`${unitLabel} 在 ${prev.max} 与 ${curr.min} 之间存在缺口`)
        }
    }

    // 末尾覆盖到 DEFAULT_MAX
    const lastMax = ranges[ranges.length - 1].max
    const maxNum = Number(DEFAULT_MAX)
    if (lastMax !== maxNum) {
        issues.push(`${unitLabel} 末尾未覆盖到 ${DEFAULT_MAX}（当前截止到 ${lastMax}）`)
    }

    return issues
}

  
  const props = defineProps({
    /** v-model：数组格式 */
    modelValue: { type: Array, default: () => [] }
  })
  const emit = defineEmits(['update:modelValue','save'])
  
  const modeOptions = [
    { value:'tiered', label:'区间价' },
    { value:'flat',   label:'一口价' },
  ]
  
  /** 内部状态：按单位分区管理 */
  const state = reactive({
    KG: { mode:'tiered', rows:[], flat:{ prize:'' } },
    CBM:{ mode:'tiered', rows:[], flat:{ prize:'' } },
  })
  
  /** 将外部数组 => 内部状态 */
  function ingest(arr){
    // 先清空
    state.KG = { mode:'tiered', rows:[], flat:{ prize:'' } }
    state.CBM= { mode:'tiered', rows:[], flat:{ prize:'' } }
  
    (arr||[]).forEach(r=>{
      const unit = (r.prize_type||'KG').toUpperCase()
      if(r.prize!==undefined && r.prize!==null && r.prize!==''){
        state[unit].mode = 'flat'
        state[unit].flat.prize = r.prize
      }else{
        state[unit].rows.push({
          range: r.range || '',
          unit_price: r.unit_price ?? '',
          base_fees: r.base_fees ?? '',
          deduction_value: r.deduction_value ?? '',
        })
      }
    })
  }
  
  /** 将内部状态 => 外部数组 */
  function emitOut(){
    const out = []
  
    const toRows = (unit, group)=>{
      if(group.mode==='flat'){
        const p = Number(group.flat.prize)
        if(!isNaN(p) && group.flat.prize!==''){
          out.push({ range:`0-${DEFAULT_MAX}`, prize: p, prize_type: unit })
        }
      }else{
        group.rows.forEach(r=>{
          // 基础校验
          if(!r.range) return
          const item = {
            range: r.range,
            unit_price: r.unit_price === '' ? undefined : Number(r.unit_price),
            prize_type: unit,
          }
          if(r.base_fees !== '') item.base_fees = Number(r.base_fees)
          if(r.deduction_value !== '') item.deduction_value = Number(r.deduction_value)
          out.push(item)
        })
      }
    }
  
    toRows('KG', state.KG)
    toRows('CBM', state.CBM)
  
    emit('update:modelValue', out)
    return out
  }
  
  watch(()=>props.modelValue, (v)=> ingest(v), { immediate:true, deep:true })
  
  /** 计算属性：picker 展示 */
  const kgModeIndex  = computed(()=> modeOptions.findIndex(m=>m.value===state.KG.mode))
  const cbmModeIndex = computed(()=> modeOptions.findIndex(m=>m.value===state.CBM.mode))
  const kgModeLabel  = computed(()=> modeOptions[kgModeIndex.value]?.label || '区间价')
  const cbmModeLabel = computed(()=> modeOptions[cbmModeIndex.value]?.label || '区间价')
  
  function setMode(unit, e){
    const v = modeOptions[e.detail.value]?.value || 'tiered'
    state[unit].mode = v
    if(v==='flat'){ state[unit].rows = [] }
    emitOut()
  }
  
  function addRow(unit){
    state[unit].rows.push({ range:'', unit_price:'', base_fees:'', deduction_value:'' })
  }
  function removeRow(unit, i){
    state[unit].rows.splice(i,1)
    emitOut()
  }
  
  function save(){
    // 校验
    const check = (g, unit)=>{
      if(g.mode==='flat'){
        if(g.flat.prize==='' || isNaN(Number(g.flat.prize))){
          return `请输入 ${unit} 一口价`
        }
      }else{
        for(const r of g.rows){
          if(!r.range) return `${unit} 有未填写的区间`
          if(r.unit_price==='' || isNaN(Number(r.unit_price))) return `${unit} 有未填写的单价`
        }
      }
      return null
    }
    const err = check(state.KG,'KG') || check(state.CBM,'CBM')
    if(err){ uni.showToast({ title: err, icon:'none' }); return }


      // 区间覆盖/重叠校验
  const problems = [
    ...validateTierCoverageAndOverlap(state.KG, 'KG'),
    ...validateTierCoverageAndOverlap(state.CBM, 'CBM'),
  ]
  if (problems.length) {
    // 这里只弹第一条；也可以用 showModal 展示全部
    uni.showToast({ title: problems[0], icon: 'none' })
    return
  }
  
    const out = emitOut()
    emit('save', out)
    uni.showToast({ title:'规则已保存', icon:'success' })
  }
  </script>
  
  <style scoped>
  .rule-editor{ display:flex; flex-direction:column; gap:24rpx; }
  .card{ background:#fff; border:1px solid #eee; border-radius:12rpx; padding:16rpx; }
  .card-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12rpx; }
  .title{ font-weight:600; }
  .picker{ padding:10rpx 14rpx; background:#fff; border:1px solid #eee; border-radius:10rpx; min-width:160rpx; color:#666; }
  
  .flat-row{ display:flex; align-items:center; gap:12rpx; }
  .label{ width:220rpx; color:#333; }
  
  .thead,.row{ display:flex; align-items:center; font-size:26rpx; margin-bottom:8rpx; }
  .thead{ font-weight:bold; background:#f6f8fa; padding:8rpx 0; }
  .col-range{ flex: 1 1 220rpx; }
  .col-price{ flex: 1 1 140rpx; text-align:center; }
  .col-base{  flex: 1 1 120rpx; text-align:center; }
  .col-deduct{flex: 1 1 120rpx; text-align:center; }
  .col-action{flex: 0 0 80rpx; text-align:right; }
  
  .add-row{ margin-top:8rpx; }
  .save{ text-align:right; margin-top:8rpx; }
  
  input{ border:1px solid #eee; border-radius:6rpx; padding:4rpx 10rpx; font-size:26rpx; background:#fff; width:90%; }
  :deep(.uni-easyinput){ width:100%; }
  </style>
  