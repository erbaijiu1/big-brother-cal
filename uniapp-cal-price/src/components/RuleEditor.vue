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
          <picker :range="categoryOptions" range-key="main_category" :value="categoryIndex" @change="onCategoryChange">
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

      <!-- 运费（弹窗编辑） -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">运费（按 KG/CBM）</view>
          <button size="mini" @click="openUnitPopup">编辑</button>
        </view>
        <view class="summary">
          <template v-if="hasRules(form.unit_price_rules)">
            <view v-for="(line, idx) in rulesToLines(form.unit_price_rules)" :key="'unit-line-' + idx" class="summary-line">
              <text class="chip">{{ line.unit }}</text>
              <text class="text">{{ line.text }}</text>
            </view>
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
      </view>

      <!-- ✅ 弹窗：运费规则 -->
      <uni-popup ref="unitPopup" type="center" :mask-click="false" background-color="#fff">
        <view class="popup-card popup-lg">
          <view class="popup-head">
            <text class="popup-title">编辑运费规则</text>
            <button size="mini" @click="closeUnitPopup">关闭</button>
          </view>
          <view class="popup-body">
            <RuleFeeEditor
              :key="`unit-${form.id ?? 'new'}`"
              v-model="form.unit_price_rules"
              dense
              @save="onUnitPopupSaved"
            />
          </view>
        </view>
      </uni-popup>

      <!-- 派送费（弹窗编辑） -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">派送费（可选）</view>
          <button size="mini" @click="openDeliveryPopup">编辑</button>
        </view>
        <view class="summary">
          <template v-if="hasRules(form.delivery_fee_rules)">
            <view v-for="(line,idx) in rulesToLines(form.delivery_fee_rules)" :key="'delivery-line-'+idx" class="summary-line">
              <text class="chip">{{ line.unit }}</text>
              <text class="text">{{ line.text }}</text>
            </view>
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
      </view>

      <!-- ✅ 弹窗：派送费规则 -->
      <uni-popup ref="deliveryPopup" type="center" :mask-click="false" background-color="#fff">
        <view class="popup-card popup-lg">
          <view class="popup-head">
            <text class="popup-title">编辑派送费规则</text>
            <button size="mini" @click="closeDeliveryPopup">关闭</button>
          </view>
          <view class="popup-body">
            <RuleFeeEditor
              :key="`delivery-${form.id ?? 'new'}`"
              v-model="form.delivery_fee_rules"
              dense
              @save="onDeliveryPopupSaved"
            />
          </view>
        </view>
      </uni-popup>

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

/** ========== 运费弹窗 ========== */
const unitPopup = ref(null)
function openUnitPopup(){ unitPopup.value?.open?.() }
function closeUnitPopup(){ unitPopup.value?.close?.() }
function onUnitPopupSaved(payload){
  form.unit_price_rules = payload || []
  closeUnitPopup()
  uni.showToast({ title:'已更新运费规则', icon:'success' })
}

/** ========== 派送费弹窗 ========== */
const deliveryPopup = ref(null)
function openDeliveryPopup(){ deliveryPopup.value?.open?.() }
function closeDeliveryPopup(){ deliveryPopup.value?.close?.() }
function onDeliveryPopupSaved(payload){
  form.delivery_fee_rules = payload || []
  closeDeliveryPopup()
  uni.showToast({ title:'已更新派送费规则', icon:'success' })
}

/** 同步外部 v-model 到内部表单 */
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

/** 分类展示（含“全部”） */
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

/** 其它下拉 */
const transportIndex = computed(() => Math.max(0, transportOptions.findIndex(x => x === form.transport_method)))
const warehouseIndex = computed(() => Math.max(0, warehouseOptions.findIndex(x => x === form.warehouse)))
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex(x => x.value === Number(form.status))))
const statusLabel = computed(() => statusOptions[statusIndex.value]?.label || '初始化')
function onStatusChange(e){ form.status = statusOptions[e.detail.value]?.value ?? 1 }

/** 校验 */
const rules = {
  channel: [{ required:true, errorMessage:'请选择渠道' }],
  category_id: [{ required:true, errorMessage:'请选择分类' }],
  transport_method: [{ required:true, errorMessage:'请选择运输方式' }],
  warehouse: [{ required:true, errorMessage:'请选择仓库' }],
  unit_price_rules: [{ validateFunction:(_,v)=> Array.isArray(v) && v.length>0, errorMessage:'请配置运费规则' }]
}

/** 保存 */
function handleSave(){
  formRef.value?.validate?.()?.then(()=>{
    const payload = normalizeOut(form)
    emit('update:modelValue', payload)
    emit('save', payload)
  }).catch(()=> uni.showToast({ title:'请检查表单', icon:'none' }))
}

/** 工具函数 */
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

/** 摘要行渲染 */
function rulesToLines(list = []){
  const groups = { KG: [], CBM: [] }
  ;(list || []).forEach(r=>{
    const unit = String(r.prize_type || r.unit || 'KG').toUpperCase().includes('CBM') ? 'CBM' : 'KG'
    if (r.prize !== undefined && r.prize !== null && r.prize !== '') {
      groups[unit].push({ type:'flat', prize: r.prize })
    } else {
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

/* 弹窗样式（通用） */
.popup-card{
  width: 88vw;
  max-width: 720rpx;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  border: 1px solid #eee;
}
.popup-head{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 20rpx;
  border-bottom: 1px solid #f0f0f0;
}
.popup-title{ font-weight: 600; color: #333; }
.popup-body{
  padding: 16rpx 20rpx 20rpx;
  overflow-y: auto;
}

/* 覆盖 uni-popup 默认 wrapper 的宽度限制（H5 有时会限制到 80%） */
::v-deep .uni-popup__wrapper {
  max-width: none !important;
  width: auto !important;
}

/* 基础弹窗外观（保留你原来的） */
.popup-card{
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  border: 1px solid #eee;
  max-height: 85vh;          /* 稍微提高可视高度 */
}

/* ✅ 加宽版本：移动端仍用视口宽度，桌面端设更大上限 */
.popup-lg{
  width: 92vw;               /* 小屏：贴边一些 */
  max-width: 1100px;         /* 桌面：更宽上限（原来只有 ~720rpx） */
}

/* 更宽屏幕进一步放开（可按需调整） */
@media (min-width: 1440px){
  /* .popup-lg{ max-width: 1280px; } */
  .popup-lg{ width: 70vw; max-width: none; }
}

/* 弹窗头/体保持不变 */
.popup-head{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 20rpx;
  border-bottom: 1px solid #f0f0f0;
}
.popup-title{ font-weight: 600; color: #333; }
.popup-body{
  padding: 16rpx 20rpx 20rpx;
  overflow-y: auto;          /* 内容过长可滚动 */
}

</style>
