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
                <view v-if="tab.closable" class="tab-close" @click.stop="removeRegionRuleTab(index)">
                  <uni-icons type="closeempty" size="14" color="#999"></uni-icons>
                </view>
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
          
          <!-- 特定区域规则 -->
          <view v-if="activeRegionTab === 1" class="tab-pane">
            <view class="rule-card">
              <view class="rule-row">
                <text class="section-title">选择区域类型与具体区域：</text>
                <view class="region-sel-box">
                  <RegionSelector
                    v-model="combinedSelectedRegions"
                    :regionType="currentRegionRuleType"
                    @update:regionType="onRegionTypeSwitch"
                  />
                </view>
              </view>

              <!-- 对应分类的规则编辑器 -->
              <view v-show="currentRegionRuleType === 'category'">
                <view class="editor-section">
                  <view class="section-title">【类别】运费规则</view>
                  <RuleFeeEditor
                    key="cat-unit"
                    v-model="typeRules.category.unit_price_rules"
                    dense
                  />
                </view>
                <view class="editor-section" style="margin-top:20rpx;">
                  <view class="section-title">【类别】派送费规则</view>
                  <RuleFeeEditor
                    key="cat-delivery"
                    v-model="typeRules.category.delivery_fee_rules"
                    dense
                  />
                </view>
              </view>

              <!-- 对应行政区的规则编辑器 -->
              <view v-show="currentRegionRuleType === 'district'">
                <view class="editor-section">
                  <view class="section-title">【行政区】运费规则</view>
                  <RuleFeeEditor
                    key="dist-unit"
                    v-model="typeRules.district.unit_price_rules"
                    dense
                  />
                </view>
                <view class="editor-section" style="margin-top:20rpx;">
                  <view class="section-title">【行政区】派送费规则</view>
                  <RuleFeeEditor
                    key="dist-delivery"
                    v-model="typeRules.district.delivery_fee_rules"
                    dense
                  />
                </view>
              </view>

              <!-- 对应子区的规则编辑器 -->
              <view v-show="currentRegionRuleType === 'sub_district'">
                <view class="editor-section">
                  <view class="section-title">【子区】运费规则</view>
                  <RuleFeeEditor
                    key="sub-unit"
                    v-model="typeRules.sub_district.unit_price_rules"
                    dense
                  />
                </view>
                <view class="editor-section" style="margin-top:20rpx;">
                  <view class="section-title">【子区】派送费规则</view>
                  <RuleFeeEditor
                    key="sub-delivery"
                    v-model="typeRules.sub_district.delivery_fee_rules"
                    dense
                  />
                </view>
              </view>

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
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import RuleFeeEditor from '@/components/RuleFeeEditor.vue'
import RegionSelector from '@/components/RegionSelector.vue'

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

// 当前选中的特定规则类型：category | district | sub_district
const currentRegionRuleType = ref('category')

// 存储三种类型的单例规则
const typeRules = reactive({
  category:     { unit_price_rules: [], delivery_fee_rules: [], _selectedRegions: [] },
  district:     { unit_price_rules: [], delivery_fee_rules: [], _selectedRegions: [] },
  sub_district: { unit_price_rules: [], delivery_fee_rules: [], _selectedRegions: [] }
})

// 固定两个标签页：通用规则和特定区域规则
const regionTabs = computed(() => [
  { id: 'default', label: '通用规则', closable: false },
  { id: 'specific', label: '特定区域规则', closable: false }
])

// 点击标签
function onRegionTabClick(index) {
  activeRegionTab.value = index
}

// 切换 RegionSelector 类型
function onRegionTypeSwitch(type) {
  currentRegionRuleType.value = type
}

// 聚合所有类型的选中项给 RegionSelector 显示
const combinedSelectedRegions = computed({
  get() {
    return [
      ...typeRules.category._selectedRegions,
      ...typeRules.district._selectedRegions,
      ...typeRules.sub_district._selectedRegions
    ]
  },
  set(val) {
    // RegionSelector 返回的是所有选中的项（含 updated list）
    // 我们需要按类型拆回 typeRules
    const cats = val.filter(x => x.type === 'category')
    const dists = val.filter(x => x.type === 'district')
    const subs = val.filter(x => x.type === 'sub_district')
    
    typeRules.category._selectedRegions = cats
    typeRules.district._selectedRegions = dists
    typeRules.sub_district._selectedRegions = subs
  }
})

// 默认规则保存回调
function onDefaultUnitSaved(payload) {
  form.unit_price_rules = payload || []
}
function onDefaultDeliverySaved(payload) {
  form.delivery_fee_rules = payload || []
}



// 同步 typeRules 到 form.region_rules（保存时会用到 normalizeOut，但为了保持 form 实时性也可同步）
// 这里其实不需要实时双向同步回 form.region_rules，因为 handleSave 时会重新组装
// 只要保证 form.region_rules 初始加载正确即可

// 默认规则编辑器引用
const defaultUnitEditorRef = ref(null)
const defaultDeliveryEditorRef = ref(null)

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

// 同步 form.region_rules 到 typeRules（初始化）
watch(() => form.region_rules, (rules) => {
  if (!Array.isArray(rules)) return
  
  // 清空现有
  typeRules.category = { unit_price_rules: [], delivery_fee_rules: [], _selectedRegions: [] }
  typeRules.district = { unit_price_rules: [], delivery_fee_rules: [], _selectedRegions: [] }
  typeRules.sub_district = { unit_price_rules: [], delivery_fee_rules: [], _selectedRegions: [] }

  // 遍历填充。所有 rules 都是特定规则。
  rules.forEach(r => {
    const type = r.regionType
    // 忽略未知的 type 或已经填充过的 type (Singleton)
    if (type && typeRules[type] && typeRules[type].unit_price_rules.length === 0) {
      typeRules[type].unit_price_rules = arr(r.unit_price_rules)
      typeRules[type].delivery_fee_rules = arr(r.delivery_fee_rules)
      typeRules[type]._selectedRegions = (r.regionIds || []).map(id => ({ id, type }))
    }
  })
  
  // 初始化 Tab：如果有数据，默认选中第一个有数据的 Tab；否则默认 category
  if (typeRules.sub_district.unit_price_rules.length > 0) currentRegionRuleType.value = 'sub_district'
  else if (typeRules.district.unit_price_rules.length > 0) currentRegionRuleType.value = 'district'
  else currentRegionRuleType.value = 'category'
  
}, { immediate: true })



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
  
  // 处理 filter_rules: 递归解析直到拿到对象或原始值
  let filter_rules = src.filter_rules
  if (typeof filter_rules === 'string') {
    filter_rules = recursiveParse(filter_rules)
  }
  // 如果解析出来是数组或对象，保留；否则(失败或空)保持原样或给空
  if (!filter_rules) filter_rules = []

  // 2. 处理特定区域规则 (region_rules)
  const regionRules = arr(src.region_rules)
  
  // 为特定规则添加 UI 辅助字段
  const processedRegionRules = regionRules.map(r => ({
    ...r,
    _selectedRegions: (r.regionIds || []).map(id => ({ id, type: r.regionType }))
  }))

  return {
    ...src,
    unit_price_rules,
    delivery_fee_rules,
    surcharge_fee_rules,
    filter_rules,
    region_rules: processedRegionRules
  };
}
function normalizeOut(src) {
  const out = { ...src };
  
  // 1. 保留根节点的通用规则
  out.unit_price_rules = arr(src.unit_price_rules)
  out.delivery_fee_rules = arr(src.delivery_fee_rules)
  out.surcharge_fee_rules = arr(src.surcharge_fee_rules)
  
  // filter_rules: 确保输出为 JSON 字符串 (后端可能需要字符串)
  if (src.filter_rules && typeof src.filter_rules === 'object') {
     out.filter_rules = JSON.stringify(src.filter_rules)
  } else {
     out.filter_rules = String(src.filter_rules || '')
  }

  // 2. 收集特定规则 (typeRules) -> region_rules
  const specificRules = []
  
  // Helper to check if rule has content
  const hasContent = (ruleObj) => {
    // 必须有选中区域 且 (有运费规则 或 有派送费规则)
    const hasRegions = ruleObj._selectedRegions && ruleObj._selectedRegions.length > 0
    const hasFees = (ruleObj.unit_price_rules && ruleObj.unit_price_rules.length > 0) || 
                    (ruleObj.delivery_fee_rules && ruleObj.delivery_fee_rules.length > 0)
    return hasRegions && hasFees
  }

  // Category
  if (hasContent(typeRules.category)) {
    specificRules.push({
      regionType: 'category',
      regionIds: typeRules.category._selectedRegions.map(r => r.id),
      unit_price_rules: typeRules.category.unit_price_rules,
      delivery_fee_rules: typeRules.category.delivery_fee_rules,
      surcharge_fee_rules: []
    })
  }

  // District
  if (hasContent(typeRules.district)) {
    specificRules.push({
      regionType: 'district',
      regionIds: typeRules.district._selectedRegions.map(r => r.id),
      unit_price_rules: typeRules.district.unit_price_rules,
      delivery_fee_rules: typeRules.district.delivery_fee_rules,
      surcharge_fee_rules: []
    })
  }

  // Sub-district
  if (hasContent(typeRules.sub_district)) {
    specificRules.push({
      regionType: 'sub_district',
      regionIds: typeRules.sub_district._selectedRegions.map(r => r.id),
      unit_price_rules: typeRules.sub_district.unit_price_rules,
      delivery_fee_rules: typeRules.sub_district.delivery_fee_rules,
      surcharge_fee_rules: []
    })
  }
  
  // 设置 region_rules
  if (STRINGIFY_JSON) {
    out.region_rules = JSON.stringify(specificRules);
  } else {
    out.region_rules = specificRules;
  }
  
  return out;
}

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

/* 区域规则弹窗内部样式 */
.region-selector-wrapper {
  margin-bottom: 30rpx;
}

.fee-editors {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.editor-section {
  border: 1px solid #eee;
  border-radius: 12rpx;
  padding: 20rpx;
}

.section-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}

.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 20rpx;
  margin-top: 30rpx;
  padding-top: 20rpx;
  border-top: 1px solid #eee;
}
/* 区域定价卡片样式 */
.subtitle {
  font-weight: 600;
  color: #555;
  margin-bottom: 12rpx;
  font-size: 28rpx;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 16rpx;
}

.rule-item {
  border: 1px solid #e0e0e0;
  border-radius: 10rpx;
  padding: 16rpx;
  background: #fafafa;
}

.rule-summary {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.region-type {
  font-weight: 600;
  color: #333;
  min-width: 120rpx;
}

.region-count {
  color: #666;
  flex: 1;
}

.rule-actions {
  display: flex;
  gap: 12rpx;
}

.add-rule {
  margin-top: 20rpx;
  text-align: center;
}

/* Tab 导航样式 */
.region-tabs {
  margin-bottom: 20rpx;
}
.tab-scroll {
  white-space: nowrap;
}
.tab-list {
  display: inline-flex;
  gap: 10rpx;
}
.tab-item {
  display: inline-flex;
  align-items: center;
  padding: 12rpx 24rpx;
  border: 1px solid #ddd;
  border-radius: 8rpx;
  background: #f9f9f9;
  color: #666;
  cursor: pointer;
  user-select: none;
}
.tab-item.active {
  background: #1f7ae0;
  color: #fff;
  border-color: #1f7ae0;
}
.tab-close {
  margin-left: 8rpx;
  display: flex;
  align-items: center;
  cursor: pointer;
}
.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

/* 规则卡片 */
.rule-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.05);
}

.rule-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16rpx;
  border-bottom: 1px solid #f0f0f0;
}

.rule-index {
  font-weight: 600;
  color: #333;
  font-size: 30rpx;
}

.rule-row {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.region-sel-box {
  background: #f8f9fa;
  padding: 16rpx;
  border-radius: 8rpx;
  border: 1px dashed #ccc;
}

</style>
