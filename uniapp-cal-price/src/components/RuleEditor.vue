<template>
  <view class="rule-editor-wrap">
    <uni-forms :modelValue="form" :rules="rules" ref="formRef" label-width="90px">
      <!-- 基本信息 -->
      <view class="card">
        <view class="card-title">基本信息</view>

        <uni-forms-item name="channel" label="渠道">
          <picker :range="channelList" range-key="channel_name" :value="channelIndex" @change="onChannelChange">
            <view class="picker">{{ channelName || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="category_id" label="分类">
          <picker :range="categoryList" range-key="main_category" :value="categoryIndex" @change="onCategoryChange">
            <view class="picker">{{ categoryName || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="transport_method" label="运输方式">
          <picker :range="transportOptions" :value="transportIndex" @change="e=> form.transport_method = transportOptions[e.detail.value]">
            <view class="picker">{{ form.transport_method || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="warehouse" label="仓库">
          <picker :range="warehouseOptions" :value="warehouseIndex" @change="e=> form.warehouse = warehouseOptions[e.detail.value]">
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

      <!-- 运费（展示/编辑双态） -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">运费（按 KG/CBM）</view>
          <button size="mini" @click="toggleEdit('unit')">{{ isEditing.unit ? '返回' : '编辑' }}</button>
        </view>

        <!-- 展示态 -->
        <view v-if="!isEditing.unit" class="summary">
          <template v-if="hasRules(form.unit_price_rules)">
            <view v-for="(line,idx) in rulesToLines(form.unit_price_rules)" :key="'unit-line-'+idx" class="summary-line">
              <text class="chip">{{ line.unit }}</text>
              <text class="text">{{ line.text }}</text>
            </view>
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>

        <!-- 编辑态 -->
        <view v-else>
          <RuleFeeEditor
            :key="`unit-${form.id ?? 'new'}`"
            v-model="form.unit_price_rules"
            dense
            @save="onSectionSaved('unit', $event)"
          />
        </view>
      </view>

      <!-- 过港费（展示/编辑双态） -->
      <view class="card">
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
          <RuleFeeEditor
            :key="`surcharge-${form.id ?? 'new'}`"
            v-model="form.surcharge_fee_rules"
            dense
            @save="onSectionSaved('surcharge', $event)"
          />
        </view>
      </view>

      <!-- 派送费（展示/编辑双态） -->
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
          <RuleFeeEditor
            :key="`delivery-${form.id ?? 'new'}`"
            v-model="form.delivery_fee_rules"
            dense
            @save="onSectionSaved('delivery', $event)"
          />
        </view>
      </view>

      <!-- 其他信息 -->
      <view class="card">
        <view class="card-title">其他</view>

        <uni-forms-item name="discount_price" label="优惠价">
          <uni-easyinput v-model="form.discount_price" placeholder="可留空；结构自定(如满减、折扣等)" />
        </uni-forms-item>

        <uni-forms-item name="delivery_time" label="交货时效">
          <uni-easyinput v-model="form.delivery_time" placeholder="例如：2-3个工作日" />
        </uni-forms-item>

        <uni-forms-item name="packaging_requirement" label="包装要求">
          <uni-easyinput v-model="form.packaging_requirement" placeholder="例如：冷链、加固等" />
        </uni-forms-item>

        <uni-forms-item name="compensation_policy" label="赔付规则">
          <uni-easyinput v-model="form.compensation_policy" type="textarea" placeholder="如破损/丢失的赔付说明" />
        </uni-forms-item>

        <uni-forms-item name="filter_rules" label="过滤规则">
          <uni-easyinput v-model="form.filter_rules" type="textarea" placeholder="禁运品、尺寸限制等（JSON或文本）" />
        </uni-forms-item>

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

/** === 可配置项 === */
const STRINGIFY_JSON = false
const transportOptions = ['陆运','空运','海运','快递','其他']
const warehouseOptions = ['深圳仓','广州仓','东莞仓','香港仓','其他']
const statusOptions = [{value:0,label:'初始化'},{value:1,label:'启用'},{value:2,label:'停用'}]

/** === Props / Emits === */
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      id: null, category_id: 0, channel: '',
      transport_method: '', warehouse: '', min_consumption: 0,
      unit_price_rules: [], surcharge_fee_rules: [], delivery_fee_rules: [],
      discount_price:'', delivery_time:'', packaging_requirement:'',
      remark:'', compensation_policy:'', status: 1, filter_rules:''
    })
  },
  channelList: { type: Array, default: () => [] },
  categoryList: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue','save','cancel'])

/** === 本地表单副本 === */
const form = reactive(normalizeIn(props.modelValue))
const formRef = ref(null)

/** 编辑态开关 */
const isEditing = reactive({
  unit: false,
  surcharge: false,
  delivery: false
})
function toggleEdit(key){ isEditing[key] = !isEditing[key] }
function onSectionSaved(key, payload){
  // 子组件校验通过，会把最新规则回传；我们更新本地值并回到展示态
  form[ sectionMap[key] ] = payload || []
  isEditing[key] = false
}
const sectionMap = { unit: 'unit_price_rules', surcharge: 'surcharge_fee_rules', delivery: 'delivery_fee_rules' }

/** 外部变更时同步 */
watch(() => props.modelValue, v => Object.assign(form, normalizeIn(v || {})), { deep:true })

/** 选择器索引与标签（渠道名/码兼容） */
const channelIndex = computed(() => {
  const list = props.channelList || []
  const idx = list.findIndex(x =>
    String(x.channel_code) === String(form.channel) || String(x.channel_name) === String(form.channel)
  )
  return idx >= 0 ? idx : 0
})
const channelName = computed(() => {
  const hit = (props.channelList || []).find(x =>
    String(x.channel_code) === String(form.channel) || String(x.channel_name) === String(form.channel)
  )
  return hit?.channel_name || ''
})

const categoryIndex = computed(() =>
  Math.max(0, props.categoryList.findIndex(x => Number(x.category_id) === Number(form.category_id))))
const categoryName = computed(() =>
  props.categoryList.find(x => Number(x.category_id) === Number(form.category_id))?.main_category || '')

const transportIndex = computed(() => Math.max(0, transportOptions.findIndex(x => x === form.transport_method)))
const warehouseIndex = computed(() => Math.max(0, warehouseOptions.findIndex(x => x === form.warehouse)))
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex(x => x.value === Number(form.status))))
const statusLabel = computed(() => statusOptions[statusIndex.value]?.label || '初始化')

function onChannelChange(e){ form.channel = props.channelList[e.detail.value]?.channel_code || '' }
function onCategoryChange(e){ form.category_id = props.categoryList[e.detail.value]?.category_id || 0 }
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

/** === 规范化 in/out === */
function arr(val){
  if (Array.isArray(val)) return val
  if (typeof val === 'string') { try { const a = JSON.parse(val); return Array.isArray(a) ? a : [] } catch { return [] } }
  return []
}
function normalizeIn(src){
  return {
    id: src?.id ?? null,
    category_id: Number(src?.category_id ?? 0),
    channel: src?.channel !== undefined && src?.channel !== null ? String(src.channel) : '',
    transport_method: src?.transport_method ?? '',
    warehouse: src?.warehouse ?? '',
    min_consumption: Number(src?.min_consumption ?? 0),
    unit_price_rules: arr(src?.unit_price_rules),
    surcharge_fee_rules: arr(src?.surcharge_fee_rules),
    delivery_fee_rules: arr(src?.delivery_fee_rules),
    discount_price: src?.discount_price ?? '',
    delivery_time: src?.delivery_time ?? '',
    packaging_requirement: src?.packaging_requirement ?? '',
    remark: src?.remark ?? '',
    compensation_policy: src?.compensation_policy ?? '',
    status: Number(src?.status ?? 1),
    filter_rules: src?.filter_rules ?? ''
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

/** === 展示态：把规则转为可读的一行摘要 === */
function rulesToLines(list = []){
  // 分组：KG / CBM
  const groups = { KG: [], CBM: [] }
  ;(list || []).forEach(r=>{
    const unit = String(r.prize_type || r.unit || 'KG').toUpperCase().includes('CBM') ? 'CBM' : 'KG'
    if (r.prize !== undefined && r.prize !== null && r.prize !== '') {
      groups[unit].push({ type:'flat', prize: r.prize })
    } else {
      groups[unit].push({
        type:'tier',
        range: r.range || '',
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
    // 若有 flat，直接显示
    const flat = arr.find(x=>x.type==='flat')
    if (flat) {
      out.push({ unit: u, text: `单价：${flat.prize}` })
      return
    }
    // tier 拼成：0-300:5，300-500:4.5，500-∞:4（附带基础费/扣减简写）
    const segs = arr
      .filter(x=>x.type==='tier')
      .map(x=>{
        const extras = []
        if (x.base_fees !== undefined && x.base_fees !== '') extras.push(`基 ${x.base_fees}`)
        if (x.deduction_value !== undefined && x.deduction_value !== '') extras.push(`扣 ${x.deduction_value}`)
        return `${x.range}:${x.unit_price}${extras.length?`（${extras.join('，')}）`:''}`
      })
    out.push({ unit: u, text: segs.join('， ') })
  })
  return out
}
</script>

<style scoped>
.rule-editor-wrap{ padding: 8rpx 12rpx; }

/* 卡片 */
.card{ background:#fff; border:1px solid #eee; border-radius:12rpx; padding:16rpx; margin-bottom:16rpx; }
.card-title{ font-weight:600; color:#333; margin-bottom:12rpx; }
.card-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12rpx; }
.card-head .card-title{ margin:0; }

/* 展示态 */
.summary{ display:flex; flex-direction:column; gap:10rpx; }
.summary-line{ display:flex; align-items:flex-start; gap:10rpx; line-height:1.6; }
.chip{
  background:#eff4ff; color:#1f6feb; border-radius:999px;
  padding:4rpx 10rpx; font-size:24rpx; flex:0 0 auto;
}
.text{ color:#333; }
.empty{ color:#999; }

/* 通用控件 */
.picker{ min-width: 160rpx; padding: 8rpx 12rpx; background:#fff; border:1px solid #ddd; border-radius:10rpx; color:#666; }
.actions{ display:flex; justify-content:flex-end; gap:16rpx; margin-top:12rpx; }
</style>
