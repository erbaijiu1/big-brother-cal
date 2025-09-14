<template>
    <view class="sum-wrap" v-if="items.length">
        <!-- 顶部统计 -->
        <view class="stats">
            <uni-tag size="mini" :text="`共 ${items.length} 项`" type="primary" />
            <uni-tag size="mini" :text="`全局 ${globals.length}`" type="success" v-if="globals.length" />
            <uni-tag size="mini" :text="`区域 ${areas.length}`" type="warning" v-if="areas.length" />
            <button v-if="items.length > limit" size="mini" class="link" @click="expanded = !expanded">
                {{ expanded ? '收起' : '展开' }}
            </button>
        </view>

        <!-- 列表 -->
        <view class="list">
            <view v-for="(r, i) in visibleItems" :key="i" class="row">
                <uni-tag size="mini" :type="r.type === 'global' ? 'success' : 'warning'"
                    :text="r.type === 'global' ? '全局' : '区域'" />
                <text class="title">{{ r.title || r.key }}</text>
                <text class="price">¥{{ r.price }}</text>

                <!-- 条件 -->
                <text class="cond" v-if="r.conditionsText">（{{ r.conditionsText }}）</text>

                <!-- 区域信息 -->
                <view v-if="r.type === 'area'" class="area">
                    <uni-tag size="mini" type="primary" :text="scopeModeLabel(r.scope?.mode)" />

                    <!-- hover 展示全部 -->
                    <uni-tooltip>
                        <text class="scope">{{ renderScopeNames(r) }}</text>
                        <template #content>
                            <view class="scope-full">
                                {{ renderFullScopeNames(r) }}
                            </view>
                        </template>
                    </uni-tooltip>

                    <uni-tag v-if="r.resolve === 'snapshot' && (r.sub_ids_snapshot?.length)" size="mini" type="default"
                        :text="`快照: ${r.sub_ids_snapshot.length} 子区`" />
                </view>

                <!-- 合并策略 -->
                <text class="combine">/{{ combineLabel(r.combine) }}</text>
            </view>
        </view>
    </view>

    <view v-else class="empty">— 未配置 —</view>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  /** 支持传入对象或字符串 */
  rules: { type: [Object, String], default: () => ({}) },
  /** 折叠时最多显示几条 */
  limit: { type: Number, default: 3 },
  /** 供渲染名称的映射（可不传），避免长列表时重复查询
   *  { areaCatsById, distsById, subsById }
   */
  nameMaps: { type: Object, default: () => ({}) }
})

const expanded = ref(false)

const normalized = computed(() => {
  // 兼容 string / object
  let obj = {}
  try {
    obj = typeof props.rules === 'string' ? JSON.parse(props.rules || '{}') : (props.rules || {})
  } catch (e) { obj = {} }

  // 标准化为数组 surcharges
  const list = Array.isArray(obj.surcharges) ? obj.surcharges : []

  // 预处理文本
  return list.map(r => {
    const c = r.conditions || {}
    const condParts = []
    if (c.volume_range) condParts.push(`体积 ${c.volume_range}`)
    if (c.weight_range) condParts.push(`重量 ${c.weight_range}`)
    if (c.vehicle)      condParts.push(`车型 ${c.vehicle}`)
    return { ...r, conditionsText: condParts.join('，') }
  })
})

const items   = computed(() => normalized.value)
const globals = computed(() => items.value.filter(r => r.type === 'global'))
const areas   = computed(() => items.value.filter(r => r.type === 'area'))
const visibleItems = computed(() => expanded.value ? items.value : items.value.slice(0, props.limit))

function scopeModeLabel(mode) {
  if (mode === 'area_category') return '自定义区'
  if (mode === 'district')      return '行政区'
  if (mode === 'sub_district')  return '子区'
  return '范围'
}
function combineLabel(v) {
  if (v === 'max')   return '取最大'
  if (v === 'first') return '取第一条'
  return '叠加'
}

// 渲染范围名称（尽量用外部 map，找不到再用 id）
function renderScopeNames(r) {
  if (r.type !== 'area') return ''
  const ids = r.scope?.ids || []
  const mode = r.scope?.mode
  const { areaCatsById = {}, distsById = {}, subsById = {} } = props.nameMaps

  const names = ids.map(id => {
    if (mode === 'area_category') return areaCatsById[id] || `#${id}`
    if (mode === 'district')      return distsById[id] || `#${id}`
    if (mode === 'sub_district')  return subsById[id] || `#${id}`
    return `#${id}`
  })

  // 太长时截断
  const text = names.join('、')
  return text.length > 60 ? text.slice(0, 60) + '…' : text
}

function renderFullScopeNames(r) {
  if (r.type !== 'area') return ''
  const ids = r.scope?.ids || []
  const mode = r.scope?.mode
  const { areaCatsById = {}, distsById = {}, subsById = {} } = props.nameMaps

  return ids.map(id => {
    if (mode === 'area_category') return areaCatsById[id] || `#${id}`
    if (mode === 'district')      return distsById[id] || `#${id}`
    if (mode === 'sub_district')  return subsById[id] || `#${id}`
    return `#${id}`
  }).join('、')
}

</script>

<style scoped>
.sum-wrap { display:flex; flex-direction:column; gap:8rpx; }
.stats { display:flex; align-items:center; gap:10rpx; }
.link { background:#f6f7fb; }

.list { display:flex; flex-direction:column; gap:8rpx; }
.row { display:flex; flex-wrap:wrap; align-items:center; gap:8rpx; }
.title { font-weight:600; }
.price { color:#e67e22; }
.combine { color:#999; }
.cond { color:#666; }
.area { display:flex; align-items:center; gap:8rpx; }
.scope { color:#666; }
.empty { color:#bbb; }
</style>
