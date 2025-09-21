<template>
  <view class="rule-editor-wrap">
    <uni-forms :modelValue="form" :rules="rules" ref="formRef" label-width="90px">
      <!-- 基本信息 -->
      <view class="card">
        <view class="card-title">基本信息</view>

        <uni-forms-item name="channel" label="渠道">
          <picker :range="channelOptions" range-key="display" :value="channelIndex" @change="onChannelChange">
            <view class="picker">{{ channelDisplay || '全部' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="category_id" label="分类">
          <picker :range="categoryList" range-key="main_category" :value="categoryIndex" @change="onCategoryChange">
            <view class="picker">{{ categoryDisplay || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="transport_method" label="运输方式">
          <picker :range="transportOptions" :value="transportIndex"
            @change="e=> form.transport_method = transportOptions[e.detail.value]">
            <view class="picker">{{ form.transport_method || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="warehouse" label="仓库">
          <picker :range="warehouseOptions" :value="warehouseIndex"
            @change="e=> form.warehouse = warehouseOptions[e.detail.value]">
            <view class="picker">{{ form.warehouse || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="min_consumption" label="最低消费">
          <uni-easyinput type="number" v-model="form.min_consumption" placeholder="0 表示不限制" />
        </uni-forms-item>

        <uni-forms-item name="status" label="状态">
          <picker :range="statusOptions" range-key="label" :value="statusIndex" @change="onStatusChange">
            <view class="picker">{{ statusLabel }}</view>
          </picker>
        </uni-forms-item>
      </view>

      <!-- 运费 -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">运费（按 KG/CBM）</view>
          <button size="mini" @click="toggleEdit('unit')">{{ isEditing.unit ? '返回' : '编辑' }}</button>
        </view>
        <view v-if="!isEditing.unit" class="summary">
          <template v-if="hasRules(form.unit_price_rules)">
            <view v-for="(line,idx) in rulesToLines(form.unit_price_rules)" :key="'unit-line-'+idx" class="summary-line">
              <text class="chip">{{ line.unit }}</text>
              <text class="text">{{ line.text }}</text>
            </view>
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
        <view v-else>
          <RuleFeeEditor :key="`unit-${form.id ?? 'new'}`" v-model="form.unit_price_rules" dense
            @save="onSectionSaved('unit', $event)" />
        </view>
      </view>

      <!-- 过港费 -->
      <!-- <view class="card">
        <view class="card-head">
          <view class="card-title">过港费（可选）</view>
          <button size="mini" @click="toggleEdit('surcharge')">{{ isEditing.surcharge ? '返回' : '编辑' }}</button>
        </view>
        <view v-if="!isEditing.surcharge" class="summary">
          <template v-if="hasRules(form.surcharge_fee_rules)">
            <view v-for="(line,idx) in rulesToLines(form.surcharge_fee_rules)" :key="'surcharge-line-'+idx" class="summary-line">
              <text class="chip">{{ line.unit }}</text>
              <text class="text">{{ line.text }}</text>
            </view>
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
        <view v-else>
          <RuleFeeEditor :key="`surcharge-${form.id ?? 'new'}`" v-model="form.surcharge_fee_rules" dense
            @save="onSectionSaved('surcharge', $event)" />
        </view>
      </view> -->

      <!-- 派送费 -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">派送费（可选）</view>
          <button size="mini" @click="toggleEdit('delivery')">{{ isEditing.delivery ? '返回' : '编辑' }}</button>
        </view>
        <view v-if="!isEditing.delivery" class="summary">
          <template v-if="hasRules(form.delivery_fee_rules)">
            <view v-for="(line,idx) in rulesToLines(form.delivery_fee_rules)" :key="'delivery-line-'+idx" class="summary-line">
              <text class="chip">{{ line.unit }}</text>
              <text class="text">{{ line.text }}</text>
            </view>
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
        <view v-else>
          <RuleFeeEditor :key="`delivery-${form.id ?? 'new'}`" v-model="form.delivery_fee_rules" dense
            @save="onSectionSaved('delivery', $event)" />
        </view>
      </view>

      <!-- 其它（只保留备注） -->
      <view class="card">
        <view class="card-title">其他</view>
        <uni-forms-item name="remark" label="备注">
          <uni-easyinput v-model="form.remark" type="textarea" placeholder="备注信息" />
        </uni-forms-item>
      </view>
    </uni-forms>

    <view class="actions">
      <button @click="$emit('cancel')">取消</button>
      <button type="primary" @click="handleSave">保存</button>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import RuleFeeEditor from '@/components/RuleFeeEditor.vue'

const STRINGIFY_JSON = false
const transportOptions = ['陆运','空运','海运','快递','其他']
const warehouseOptions = ['深圳仓','广州仓','东莞仓','香港仓','其他']
const statusOptions = [
  {value:0,label:'初始化'},
  {value:1,label:'启用'},
  {value:2,label:'停用'}
]

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      id: null, category_id: 0, channel: '',
      transport_method: '', warehouse: '', min_consumption: 0,
      unit_price_rules: [], surcharge_fee_rules: [], delivery_fee_rules: [],
      remark:'', status: 1
    })
  },
  channelList: { type: Array, default: () => [] },
  categoryList: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue','save','cancel'])

const form = reactive(normalizeIn(props.modelValue))
const formRef = ref(null)

const isEditing = reactive({ unit: false, surcharge: false, delivery: false })
function toggleEdit(key){ isEditing[key] = !isEditing[key] }
function onSectionSaved(key, payload){
  form[ sectionMap[key] ] = payload || []
  isEditing[key] = false
}
const sectionMap = { unit: 'unit_price_rules', surcharge: 'surcharge_fee_rules', delivery: 'delivery_fee_rules' }

watch(() => props.modelValue, v => Object.assign(form, normalizeIn(v || {})), { deep:true })

/** 渠道展示 */
const channelOptions = computed(() => [
  { channel_code: '', channel_name: '', display: '全部' },
  ...(props.channelList || []).map(x => ({ ...x, display: `${x.channel_code} - ${x.channel_name || ''}` }))
])
const channelIndex = computed(() => {
  const i = channelOptions.value.findIndex(opt => String(opt.channel_code) === String(form.channel))
  return i >= 0 ? i : 0
})
const channelDisplay = computed(() => channelOptions.value[channelIndex.value]?.display || '全部')
function onChannelChange(e){ form.channel = channelOptions.value[e.detail.value]?.channel_code || '' }

/** 分类展示 */
const categoryOptions = computed(() => [
  { category_id: 0, main_category: '全部' },
  ...(props.categoryList || [])
])
const categoryIndex = computed(() => {
  const i = categoryOptions.value.findIndex(opt => Number(opt.category_id) === Number(form.category_id))
  return i >= 0 ? i : 0
})
const categoryDisplay = computed(() => categoryOptions.value[categoryIndex.value]?.main_category || '全部')
function onCategoryChange(e){ form.category_id = categoryOptions.value[e.detail.value]?.category_id || 0 }

const transportIndex = computed(() => Math.max(0, transportOptions.findIndex(x => x === form.transport_method)))
const warehouseIndex = computed(() => Math.max(0, warehouseOptions.findIndex(x => x === form.warehouse)))
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex(x => x.value === Number(form.status))))
const statusLabel = computed(() => statusOptions[statusIndex.value]?.label || '初始化')
function onStatusChange(e){ form.status = statusOptions[e.detail.value]?.value ?? 1 }

const rules = {
  channel: [{ required:true, errorMessage:'请选择渠道' }],
  category_id: [{ required:true, errorMessage:'请选择分类' }],
  transport_method: [{ required:true, errorMessage:'请选择运输方式' }],
  warehouse: [{ required:true, errorMessage:'请选择仓库' }],
  unit_price_rules: [{ validateFunction:(_,v)=> Array.isArray(v) && v.length>0, errorMessage:'请配置运费规则' }]
}

function handleSave(){
  formRef.value?.validate?.()?.then(()=>{
    const payload = normalizeOut(form)
    emit('update:modelValue', payload)
    emit('save', payload)
  }).catch(()=> uni.showToast({ title:'请检查表单', icon:'none' }))
}

function arr(val){
  if (Array.isArray(val)) return val
  if (typeof val === 'string') { try { const a = JSON.parse(val); return Array.isArray(a) ? a : [] } catch { return [] } }
  return []
}
function normalizeIn(src){
  return {
    id: src?.id ?? null,
    category_id: Number(src?.category_id ?? 0),
    channel: src?.channel ? String(src.channel) : '',
    transport_method: src?.transport_method ?? '',
    warehouse: src?.warehouse ?? '',
    min_consumption: Number(src?.min_consumption ?? 0),
    unit_price_rules: arr(src?.unit_price_rules),
    surcharge_fee_rules: arr(src?.surcharge_fee_rules),
    delivery_fee_rules: arr(src?.delivery_fee_rules),
    remark: src?.remark ?? '',
    status: Number(src?.status ?? 1)
  }
}
function normalizeOut(src){
  const out = { ...src }
  if (STRINGIFY_JSON) {
    out.unit_price_rules     = JSON.stringify(arr(src.unit_price_rules))
    out.surcharge_fee_rules  = JSON.stringify(arr(src.surcharge_fee_rules))
    out.delivery_fee_rules   = JSON.stringify(arr(src.delivery_fee_rules))
  } else {
    out.unit_price_rules     = arr(src.unit_price_rules)
    out.surcharge_fee_rules  = arr(src.surcharge_fee_rules)
    out.delivery_fee_rules   = arr(src.delivery_fee_rules)
  }
  out.min_consumption = Number(src.min_consumption || 0)
  out.status = Number(src.status || 1)
  return out
}
function hasRules(a){ return Array.isArray(a) && a.length>0 }

/** 修正过的规则展示 */
function rulesToLines(list = []){
  const groups = { KG: [], CBM: [] }
  ;(list || []).forEach(r=>{
    const unit = String(r.prize_type || r.unit || 'KG').toUpperCase().includes('CBM') ? 'CBM' : 'KG'
    if (r.prize !== undefined && r.prize !== null && r.prize !== '') {
      groups[unit].push({ type:'flat', prize: r.prize })
    } else {
      // 🟢 修正 range 显示
      let rangeText = ''
      if (Array.isArray(r.range)) {
        rangeText = `${r.range[0]}-${r.range[1]}`
      } else if (typeof r.range === 'string') {
        rangeText = r.range.replace(/[\[\]]/g,'').replace(',','-')
      } else {
        rangeText = String(r.range || '')
      }

      groups[unit].push({
        type:'tier',
        range: rangeText,
        unit_price: r.unit_price ?? r.price,
        base_fees: r.base_fees ?? r.base_fee,
        deduction_value: r.deduction_value ?? r.deduct
      })
    }
  })
  const out = []
  ;(['KG','CBM']).forEach(u=>{
    const arr = groups[u]
    if (!arr.length) return
    const flat = arr.find(x=>x.type==='flat')
    if (flat) {
      out.push({ unit: u, text: `单价：${flat.prize}` })
      return
    }
    const segs = arr.filter(x=>x.type==='tier').map(x=>{
      const extras = []
      if (x.base_fees !== undefined && x.base_fees !== '') extras.push(`${x.base_fees}元`)
      if (x.deduction_value !== undefined && x.deduction_value !== '') extras.push(`含 ${x.deduction_value}`)
      return `${x.range}:${x.unit_price}(单价)${extras.length?`（${extras.join('，')}）`:''}`
    })
    out.push({ unit: u, text: segs.join('， ') })
  })
  return out
}
</script>



<style scoped>
.rule-editor-wrap{ padding: 8rpx 12rpx; }
.card{ background:#fff; border:1px solid #eee; border-radius:12rpx; padding:16rpx; margin-bottom:16rpx; }
.card-title{ font-weight:600; color:#333; margin-bottom:12rpx; }
.card-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12rpx; }
.card-head .card-title{ margin:0; }
.summary{ display:flex; flex-direction:column; gap:10rpx; }
.summary-line{ display:flex; align-items:flex-start; gap:10rpx; line-height:1.6; }
.chip{ background:#eff4ff; color:#1f6feb; border-radius:999px; padding:4rpx 10rpx; font-size:24rpx; flex:0 0 auto; }
.text{ color:#333; }
.empty{ color:#999; }
.picker{ min-width: 160rpx; padding: 8rpx 12rpx; background:#fff; border:1px solid #ddd; border-radius:10rpx; color:#666; }
.actions{ display:flex; justify-content:flex-end; gap:16rpx; margin-top:12rpx; }
</style>
