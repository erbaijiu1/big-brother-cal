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
          <picker :range="transportOptions" :value="transportIndex" @change="e => form.transport_method = transportOptions[e.detail.value]">
            <view class="picker">{{ form.transport_method || '请选择' }}</view>
          </picker>
        </uni-forms-item>

        <uni-forms-item name="warehouse" label="仓库">
          <picker :range="warehouseOptions" :value="warehouseIndex" @change="e => form.warehouse = warehouseOptions[e.detail.value]">
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

      <!-- 运费（弹窗编辑 + 摘要用 RuleViewer 多行展示） -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">运费（按 KG/CBM）</view>
          <button size="mini" @click="openUnitPopup">编辑</button>
        </view>

        <view class="summary">
          <template v-if="hasRules(form.unit_price_rules)">
            <RuleViewer :rules="form.unit_price_rules" />
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
      </view>

      <!-- 弹窗：运费规则 -->
      <uni-popup ref="unitPopup" type="center" :mask-click="false" background-color="#fff">
        <view class="popup-card popup-lg">
          <view class="popup-head">
            <text class="popup-title">编辑运费规则</text>
            <button size="mini" @click="closeUnitPopup">关闭</button>
          </view>
          <view class="popup-body">
            <RuleFeeEditor
              ref="unitEditorRef"
              :key="`unit-${form.id ?? 'new'}-${unitKey}`"
              v-model="form.unit_price_rules"
              dense
              @save="onUnitPopupSaved"
            />
          </view>
        </view>
      </uni-popup>

      <!-- 派送费（弹窗编辑 + 摘要用 RuleViewer 多行展示） -->
      <view class="card">
        <view class="card-head">
          <view class="card-title">派送费（可选）</view>
          <button size="mini" @click="openDeliveryPopup">编辑</button>
        </view>

        <view class="summary">
          <template v-if="hasRules(form.delivery_fee_rules)">
            <RuleViewer :rules="form.delivery_fee_rules" />
          </template>
          <view v-else class="empty">暂无规则，点击右上角“编辑”添加</view>
        </view>
      </view>

      <!-- 弹窗：派送费规则 -->
      <uni-popup ref="deliveryPopup" type="center" :mask-click="false" background-color="#fff">
        <view class="popup-card popup-lg">
          <view class="popup-head">
            <text class="popup-title">编辑派送费规则</text>
            <button size="mini" @click="closeDeliveryPopup">关闭</button>
          </view>
          <view class="popup-body">
            <RuleFeeEditor
              ref="deliveryEditorRef"
              :key="`delivery-${form.id ?? 'new'}-${deliveryKey}`"
              v-model="form.delivery_fee_rules"
              dense
              @save="onDeliveryPopupSaved"
            />
          </view>
        </view>
      </uni-popup>

      <!-- 其它（备注） -->
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
import { computed, reactive, ref, watch, nextTick } from 'vue'
import RuleFeeEditor from '@/components/RuleFeeEditor.vue'
import RuleViewer from '@/components/RuleViewer.vue'

/* ===== 常量/下拉 ===== */
const STRINGIFY_JSON = false
const transportOptions = ['陆运', '空运', '海运', '快递', '其他']
const warehouseOptions = ['深圳仓', '广州仓', '东莞仓', '香港仓', '其他']
const statusOptions = [
  { value: 0, label: '初始化' },
  { value: 1, label: '启用' },
  { value: 2, label: '停用' }
]

/* ===== props / emits ===== */
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      id: null,
      category_id: 0,
      channel: '',
      transport_method: '',
      warehouse: '',
      min_consumption: 0,
      unit_price_rules: [],
      surcharge_fee_rules: [],
      delivery_fee_rules: [],
      remark: '',
      status: 1
    })
  },
  channelList: { type: Array, default: () => [] },
  categoryList: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

/* ===== 表单 ===== */
const form = reactive(normalizeIn(props.modelValue))
const formRef = ref(null)

watch(
  () => props.modelValue,
  (v) => { Object.assign(form, normalizeIn(v || {})) },
  { deep: true }
)

/* ===== 弹窗：运费 ===== */
const unitPopup = ref(null)
const unitEditorRef = ref(null)
const unitKey = ref(0)

function openUnitPopup() {
  unitKey.value++
  nextTick(() => unitPopup.value?.open?.())
}
function closeUnitPopup() { unitPopup.value?.close?.() }
function onUnitPopupSaved(payload) {
  form.unit_price_rules = payload || []
  closeUnitPopup()
  uni.showToast({ title: '已更新运费规则', icon: 'success' })
}

/* ===== 弹窗：派送费 ===== */
const deliveryPopup = ref(null)
const deliveryEditorRef = ref(null)
const deliveryKey = ref(0)

function openDeliveryPopup() {
  deliveryKey.value++
  nextTick(() => deliveryPopup.value?.open?.())
}
function closeDeliveryPopup() { deliveryPopup.value?.close?.() }
function onDeliveryPopupSaved(payload) {
  form.delivery_fee_rules = payload || []
  closeDeliveryPopup()
  uni.showToast({ title: '已更新派送费规则', icon: 'success' })
}

/* ===== 下拉展示 ===== */
const channelOptions = computed(() => [
  { channel_code: '', channel_name: '', display: '全部' },
  ...(props.channelList || []).map((x) => ({
    ...x,
    display: `${x.channel_code} - ${x.channel_name || ''}`
  }))
])
const channelIndex = computed(() => {
  const i = channelOptions.value.findIndex(
    (opt) => String(opt.channel_code) === String(form.channel)
  )
  return i >= 0 ? i : 0
})
const channelDisplay = computed(
  () => channelOptions.value[channelIndex.value]?.display || '全部'
)
function onChannelChange(e) {
  form.channel = channelOptions.value[e.detail.value]?.channel_code || ''
}

const categoryOptions = computed(() => [
  { category_id: 0, main_category: '全部' },
  ...(props.categoryList || [])
])
const categoryIndex = computed(() => {
  const i = categoryOptions.value.findIndex(
    (opt) => Number(opt.category_id) === Number(form.category_id)
  )
  return i >= 0 ? i : 0
})
const categoryDisplay = computed(
  () => categoryOptions.value[categoryIndex.value]?.main_category || '全部'
)
function onCategoryChange(e) {
  form.category_id = categoryOptions.value[e.detail.value]?.category_id || 0
}

const transportIndex = computed(() =>
  Math.max(0, transportOptions.findIndex((x) => x === form.transport_method))
)
const warehouseIndex = computed(() =>
  Math.max(0, warehouseOptions.findIndex((x) => x === form.warehouse))
)
const statusIndex = computed(() =>
  Math.max(0, statusOptions.findIndex((x) => x.value === Number(form.status)))
)
const statusLabel = computed(
  () => statusOptions[statusIndex.value]?.label || '初始化'
)
function onStatusChange(e) {
  form.status = statusOptions[e.detail.value]?.value ?? 1
}

/* ===== 校验 ===== */
const rules = {
  channel: [{ required: true, errorMessage: '请选择渠道' }],
  category_id: [{ required: true, errorMessage: '请选择分类' }],
  transport_method: [{ required: true, errorMessage: '请选择运输方式' }],
  warehouse: [{ required: true, errorMessage: '请选择仓库' }],
  unit_price_rules: [{
    validateFunction: (_, v) => Array.isArray(v) && v.length > 0,
    errorMessage: '请配置运费规则'
  }]
}

/* ===== 保存：父级点击保存时静默同步两个编辑器 ===== */
async function handleSave() {
  await syncChildEditors()

  formRef.value?.validate?.()
    ?.then(() => {
      const payload = normalizeOut(form)
      emit('update:modelValue', payload)
      emit('save', payload)
    })
    .catch(() => uni.showToast({ title: '请检查表单', icon: 'none' }))
}
async function syncChildEditors() {
  const u = unitEditorRef.value?.save?.(true)
  if (u && u.ok) form.unit_price_rules = u.data || form.unit_price_rules

  const d = deliveryEditorRef.value?.save?.(true)
  if (d && d.ok) form.delivery_fee_rules = d.data || form.delivery_fee_rules
}

/* ===== 工具/兼容 ===== */
function arr(val) {
  if (Array.isArray(val)) return val
  if (typeof val === 'string') {
    try {
      const a = JSON.parse(val)
      return Array.isArray(a) ? a : []
    } catch { return [] }
  }
  return []
}
function normalizeIn(src) {
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
function normalizeOut(src) {
  const out = { ...src }
  if (STRINGIFY_JSON) {
    out.unit_price_rules    = JSON.stringify(arr(src.unit_price_rules))
    out.surcharge_fee_rules = JSON.stringify(arr(src.surcharge_fee_rules))
    out.delivery_fee_rules  = JSON.stringify(arr(src.delivery_fee_rules))
  } else {
    out.unit_price_rules    = arr(src.unit_price_rules)
    out.surcharge_fee_rules = arr(src.surcharge_fee_rules)
    out.delivery_fee_rules  = arr(src.delivery_fee_rules)
  }
  out.min_consumption = Number(src.min_consumption || 0)
  out.status          = Number(src.status || 1)
  return out
}
function hasRules(a) { return Array.isArray(a) && a.length > 0 }
</script>

<style scoped>
.rule-editor-wrap{ padding: 8rpx 12rpx; }
.card{ background:#fff; border:1px solid #eee; border-radius:12rpx; padding:16rpx; margin-bottom:16rpx; }
.card-title{ font-weight:600; color:#333; margin-bottom:12rpx; }
.card-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12rpx; }
.card-head .card-title{ margin:0; }

.summary{ display:flex; flex-direction:column; gap:10rpx; }
.empty{ color:#999; }

.picker{ min-width:160rpx; padding:8rpx 12rpx; background:#fff; border:1px solid #ddd; border-radius:10rpx; color:#666; }
.actions{ display:flex; justify-content:flex-end; gap:16rpx; margin-top:12rpx; }

/* 弹窗样式 */
.popup-card{
  display:flex; flex-direction:column; background:#fff; border-radius:16rpx;
  overflow:hidden; border:1px solid #eee; max-height:85vh;
}
.popup-head{
  display:flex; justify-content:space-between; align-items:center;
  padding:16rpx 20rpx; border-bottom:1px solid #f0f0f0;
}
.popup-title{ font-weight:600; color:#333; }
.popup-body{ padding:16rpx 20rpx 20rpx; overflow-y:auto; }

/* 覆盖 uni-popup 默认 wrapper 限制 */
::v-deep .uni-popup__wrapper{ max-width:none !important; width:auto !important; }

/* 宽版 */
.popup-lg{ width:92vw; max-width:1100px; }
@media (min-width:1440px){ .popup-lg{ width:70vw; max-width:none; } }
</style>
