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

      <!-- 区域定价设置 -->
      <view class="card">
        <view class="card-title">区域定价</view>
        
        <!-- Tab 导航 -->
        <view class="region-tabs">
          <scroll-view scroll-x class="tab-scroll">
            <view class="tab-list">
              <view
                v-for="(tab, index) in regionTabs"
                :key="tab.id"
                :class="['tab-item', { active: activeRegionTab === index }]"
                @click="onRegionTabClick(index)"
              >
                <text>{{ tab.label }}</text>
              </view>
            </view>
          </scroll-view>
        </view>
        
        <!-- Tab 内容 -->
        <view class="region-content">
          <!-- 通用规则 -->
          <view v-if="activeRegionTab === 0" class="tab-pane">
            <view class="subtitle">通用规则（适用于所有未特别指定的区域）</view>
            <!-- 运费规则编辑器 -->
            <view class="editor-section">
              <view class="section-title">运费规则</view>
              <RuleFeeEditor
                ref="defaultUnitEditorRef"
                :key="`default-unit-${form.id ?? 'new'}`"
                v-model="form.unit_price_rules"
                dense
                @save="onDefaultUnitSaved"
              />
            </view>
            <!-- 派送费规则编辑器 -->
            <view class="editor-section">
              <view class="section-title">派送费规则</view>
              <RuleFeeEditor
                ref="defaultDeliveryEditorRef"
                :key="`default-delivery-${form.id ?? 'new'}`"
                v-model="form.delivery_fee_rules"
                dense
                @save="onDefaultDeliverySaved"
              />
            </view>
          </view>
          
          <!-- 特定区域规则 (New List View) -->
          <view v-if="activeRegionTab === 1" class="tab-pane">
            <view class="subtitle">特定区域规则列表（优先级高于通用规则）</view>
            
            <view v-if="form.region_rules.length === 0" class="empty-rules">
              <text>暂无特定区域规则</text>
            </view>

            <view class="rule-list">
               <view v-for="(rule, idx) in form.region_rules" :key="idx" class="rule-item">
                  <view class="rule-header">
                     <view class="rule-title">
                        <text class="rule-index">序号{{ idx + 1 }}</text>
                     </view>
                     <view class="rule-actions">
                        <button size="mini" @click="openEditRule(idx)">编辑</button>
                        <button size="mini" type="warn" plain @click="deleteRule(idx)">删除</button>
                     </view>
                  </view>
                  
                  <!-- 规则内容详情 -->
                  <view class="rule-content">
                    <!-- 1. 区域 -->
                     <view class="detail-row">
                        <text class="label">【区域】</text>
                        <view class="tags-wrap">
                          <text v-for="(tag, ti) in getRegionTags(rule)" :key="ti" class="region-tag">{{ tag }}</text>
                          <text v-if="getRegionTags(rule).length === 0" class="val-text">未选择区域</text>
                        </view>
                     </view>

                     <!-- 2. 运费规则表格 -->
                     <view class="detail-block" v-if="rule.unit_price_rules && rule.unit_price_rules.length">
                        <view class="block-label">【运费】</view>
                        <view class="mini-table">
                          <view class="mt-head">
                            <text class="c-unit">计量</text>
                            <text class="c-range">范围</text>
                            <text class="c-desc">价格说明</text>
                          </view>
                          <view class="mt-row" v-for="(r, ri) in rule.unit_price_rules" :key="'u'+ri">
                            <text class="c-unit">{{ unitOf(r) }}</text>
                            <text class="c-range">{{ rangeText(r) }}</text>
                            <text class="c-desc">{{ priceDesc(r) }}</text>
                          </view>
                        </view>
                     </view>

                     <!-- 3. 派送费规则表格 -->
                     <view class="detail-block" v-if="rule.delivery_fee_rules && rule.delivery_fee_rules.length">
                        <view class="block-label">【派送费】</view>
                        <view class="mini-table">
                          <view class="mt-head">
                            <text class="c-unit">计量</text>
                            <text class="c-range">范围</text>
                            <text class="c-desc">价格说明</text>
                          </view>
                          <view class="mt-row" v-for="(r, ri) in rule.delivery_fee_rules" :key="'d'+ri">
                            <text class="c-unit">{{ unitOf(r) }}</text>
                            <text class="c-range">{{ rangeText(r) }}</text>
                            <text class="c-desc">{{ priceDesc(r) }}</text>
                          </view>
                        </view>
                     </view>
                  </view>
               </view>
            </view>

            <view class="add-btn-wrap">
              <button class="add-btn" @click="openAddRule">新增区域规则</button>
            </view>
          </view>
        </view>
      </view>

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
    
    <!-- 弹窗 -->
    <SpecificRuleDialog ref="specificRuleDialog" @confirm="onSpecificRuleConfirm" />

  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import RuleFeeEditor from '@/components/RuleFeeEditor.vue'
import SpecificRuleDialog from '@/components/SpecificRuleDialog.vue'

/* ===== 常量/下拉 ===== */
const STRINGIFY_JSON = false
const transportOptions = ['陆运', '空运', '海运', '快递', '其他']
const warehouseOptions = ['深圳仓', '广州仓', '东莞仓', '香港仓', '其他']
const statusOptions = [
  { value: 0, label: '初始化' },
  { value: 1, label: '启用' },
  { value: 2, label: '停用' }
]

/* ===== 区域定价设置 ===== */
const activeRegionTab = ref(0) // 0=general, 1=specific

// 固定两个标签页：通用规则和特定区域规则
const regionTabs = computed(() => [
  { id: 'default', label: '通用规则' },
  { id: 'specific', label: '特定区域规则' }
])

function onRegionTabClick(index) {
  activeRegionTab.value = index
}

// 默认规则保存回调
function onDefaultUnitSaved(payload) {
  form.unit_price_rules = payload || []
}
function onDefaultDeliverySaved(payload) {
  form.delivery_fee_rules = payload || []
}

// 默认规则编辑器引用
const defaultUnitEditorRef = ref(null)
const defaultDeliveryEditorRef = ref(null)

/* ===== Specific Rule Logic ===== */
const specificRuleDialog = ref(null)
const editingRuleIndex = ref(-1)

function openAddRule() {
  editingRuleIndex.value = -1
  specificRuleDialog.value.open(null)
}

function openEditRule(index) {
  editingRuleIndex.value = index
  const rule = form.region_rules[index]
  // Deep copy to prevent direct mutation before confirm
  specificRuleDialog.value.open(JSON.parse(JSON.stringify(rule)))
}

function deleteRule(index) {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这条规则吗？',
    success: (res) => {
      if (res.confirm) {
        form.region_rules.splice(index, 1)
      }
    }
  })
}

function onSpecificRuleConfirm(payload) {
  if (editingRuleIndex.value >= 0) {
    // Edit
    form.region_rules.splice(editingRuleIndex.value, 1, payload)
  } else {
    // Add
    form.region_rules.push(payload)
  }
}

// Summary Helpers
function getRegionTags(rule) {
  if (!rule || !rule.region_conf || !Array.isArray(rule.region_conf)) return []
  const tags = []
  rule.region_conf.forEach(c => {
      const typeMap = { area_category: '自定义', district: '行政区', sub_district: '子区' }
      const typeName = typeMap[c.regionType] || c.regionType
      const count = c.regionIds ? c.regionIds.length : 0
      if (count > 0) {
        tags.push(`[${typeName}] ${count}个`)
      }
  })
  return tags
}

/* ========= Formatting Helpers (Ported from RuleViewer) ========= */
const DEFAULT_MAX = 99999999

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
  if (U.includes('PCS') || U.includes('件')) return '件'
  return U
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
  return '-'
}

const priceDesc = (r) => {
  // 一口价
  if (r?.prize !== undefined && r?.prize !== null && r?.prize !== '') {
    return `一口价 ${stripZeros(r.prize)} 元`
  }
  // 单价 + 基础费 + 包多少 + 起订量
  const unit = unitOf(r) || ''
  const up = (r?.unit_price ?? r?.price)
  const segs = []
  if (up !== undefined && up !== null && String(up) !== '') {
    let priceText = `单价 ${stripZeros(up)} 元`
    if (unit) {
      const minimumUnit = r?.minimum_unit ?? 0
      if (minimumUnit > 0) {
        priceText += `/${stripZeros(minimumUnit)}${unit}`
      } else {
        priceText += `/${unit}`
      }
    }
    segs.push(priceText)
  }
  if (r?.base_fees !== undefined && r?.base_fees !== '') {
    segs.push(`基础费 ${stripZeros(r.base_fees)} 元`)
  }
  if (r?.deduction_value !== undefined && r?.deduction_value !== '') {
    segs.push(`含 ${stripZeros(r.deduction_value)}${unit}`)
  }
  return segs.length ? segs.join('， ') : '-'
}


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
      region_rules: [],
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
}

/* ===== 保存 ===== */
async function handleSave() {
  await syncChildEditors()

  formRef.value?.validate?.()
    ?.then(() => {
      const payload = normalizeOut(form)
      emit('update:modelValue', payload)
      emit('save', payload)
    })
    .catch((e) => {
        console.error(e)
        uni.showToast({ title: '请检查表单', icon: 'none' })
    })
}

async function syncChildEditors() {
  // 同步默认规则编辑器
  const u = defaultUnitEditorRef.value?.save?.(true)
  if (u && u.ok) form.unit_price_rules = u.data || form.unit_price_rules

  const d = defaultDeliveryEditorRef.value?.save?.(true)
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
function recursiveParse(val) {
  if (typeof val !== 'string') return val
  try {
    const parsed = JSON.parse(val)
    if (typeof parsed === 'string') return recursiveParse(parsed)
    return parsed
  } catch {
    return val
  }
}

function normalizeIn(src) {
  // 1. 处理通用规则 (Root level)
  const unit_price_rules = arr(src.unit_price_rules)
  const delivery_fee_rules = arr(src.delivery_fee_rules)
  const surcharge_fee_rules = arr(src.surcharge_fee_rules)
  
  // 处理 filter_rules
  let filter_rules = src.filter_rules
  if (typeof filter_rules === 'string') {
    filter_rules = recursiveParse(filter_rules)
  }
  if (!filter_rules) filter_rules = []

  // 2. 处理特定区域规则 (region_rules)
  let region_rules = arr(src.region_rules)
  
  // Robustness check for old structure:
  // Old structure: [{ regionType: '...', regionIds: [...], unit_price_rules: [...] }]
  // New structure: [{ region_conf: [{ regionType: '...', ... }], unit_price_rules: [...] }]
  
  region_rules = region_rules.map(r => {
      if (r.region_conf) return r; // Already new format
      
      // Convert old to new
      if (r.regionType && r.regionIds) {
          return {
              region_conf: [{ regionType: r.regionType, regionIds: r.regionIds }],
              unit_price_rules: arr(r.unit_price_rules),
              delivery_fee_rules: arr(r.delivery_fee_rules),
              surcharge_fee_rules: arr(r.surcharge_fee_rules)
          }
      }
      return r
  })

  return {
    ...src,
    unit_price_rules,
    delivery_fee_rules,
    surcharge_fee_rules,
    filter_rules,
    region_rules
  };
}

function normalizeOut(src) {
  const out = { ...src };
  
  out.unit_price_rules = arr(src.unit_price_rules)
  out.delivery_fee_rules = arr(src.delivery_fee_rules)
  out.surcharge_fee_rules = arr(src.surcharge_fee_rules)
  
  if (src.filter_rules && typeof src.filter_rules === 'object') {
     out.filter_rules = JSON.stringify(src.filter_rules)
  } else {
     out.filter_rules = String(src.filter_rules || '')
  }

  // region_rules is already in correct format, just ensure it's an array
  out.region_rules = arr(src.region_rules)
  
  return out;
}

</script>

<style scoped>
.rule-editor-wrap{ padding: 8rpx 12rpx; }
.card{ background:#fff; border:1px solid #eee; border-radius:12rpx; padding:16rpx; margin-bottom:16rpx; }
.card-title{ font-weight:600; color:#333; margin-bottom:12rpx; }

.picker{ min-width:160rpx; padding:8rpx 12rpx; background:#fff; border:1px solid #ddd; border-radius:10rpx; color:#666; }
.actions{ display:flex; justify-content:flex-end; gap:16rpx; margin-top:12rpx; }

/* Review Tab Styles */
.region-tabs {
  margin-bottom: 20rpx;
  border-bottom: 1px solid #eee;
}
.tab-scroll {
  white-space: nowrap;
}
.tab-list {
  display: flex;
  gap: 20rpx;
}
.tab-item {
  padding: 12rpx 20rpx;
  font-size: 28rpx;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}
.tab-item.active {
  color: #007aff;
  border-bottom-color: #007aff;
  font-weight: 600;
}

.editor-section {
  border: 1px solid #f0f0f0;
  border-radius: 8rpx;
  padding: 16rpx;
  margin-top: 16rpx;
  background: #fafafa;
}
.section-title {
  font-weight: bold;
  font-size: 28rpx;
  margin-bottom: 10rpx;
}
.subtitle {
  color: #888;
  font-size: 24rpx;
  margin-bottom: 16rpx;
}

/* List View Styles */
.rule-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.rule-item {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 12rpx;
  padding: 20rpx;
}
.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
  border-bottom: 1px solid #eee;
  padding-bottom: 12rpx;
}
.rule-title {
  font-weight: 600;
  font-size: 30rpx;
}
.rule-actions {
  display: flex;
  gap: 12rpx;
}
.rule-summary-content {
  /* removed */
}
.summary-line {
    /* removed */
}

/* New Detail Styles */
.rule-content {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.detail-row {
  display: flex;
  align-items: flex-start;
  font-size: 26rpx;
}
.detail-row .label {
  font-weight: 600;
  color: #333;
  width: 120rpx;
  flex-shrink: 0;
  margin-top: 4rpx;
}
.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  flex: 1;
}
.region-tag {
  font-size: 22rpx;
  color: #e67e22;
  background: #fff5e6;
  padding: 4rpx 10rpx;
  border-radius: 6rpx;
  border: 1px solid #ffeacc;
}
.val-text {
  color: #999;
}

.detail-block {
  margin-top: 8rpx;
}
.block-label {
  font-size: 26rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 6rpx;
}
.mini-table {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8rpx;
  overflow: hidden;
  font-size: 24rpx;
}
.mt-head {
  display: flex;
  background: #f1f1f1;
  padding: 6rpx 10rpx;
  font-weight: 600;
  color: #555;
}
.mt-row {
  display: flex;
  padding: 6rpx 10rpx;
  border-top: 1px dashed #f5f5f5;
  color: #666;
}
.mt-row:first-child {
  border-top: none;
}
.c-unit { flex: 0 0 80rpx; }
.c-range { flex: 0 0 140rpx; }
.c-desc { flex: 1; }

.add-btn-wrap {
  margin-top: 30rpx;
  text-align: center;
}
.add-btn {
  width: 60%;
  background-color: #f0f9eb;
  color: #67c23a;
  border: 1px solid #b3e19d;
}
.empty-rules {
    text-align: center;
    padding: 40rpx;
    color: #999;
}
</style>
