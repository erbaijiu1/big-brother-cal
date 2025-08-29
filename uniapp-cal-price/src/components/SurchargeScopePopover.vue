<template>
  <view class="scope-chip" @click="open">
    <uni-tag :text="chipText" type="primary" size="small" />
    <uni-popup ref="pop" type="dialog">
      <view class="pop">
        <view class="pop-title">{{ title }}</view>

        <!-- 行政区模式：直接列行政区名 -->
        <view v-if="rule.scope?.mode === 'district'" class="list">
          <view v-for="n in resolvedNames" :key="n" class="item">· {{ n }}</view>
        </view>

        <!-- 子区模式：按行政区分组 -->
        <view v-else-if="rule.scope?.mode === 'sub_district'" class="list">
          <view v-for="g in groupedSubs" :key="g.district" class="group">
            <view class="group-name">{{ g.district }}</view>
            <view class="subs">
              <text v-for="s in g.subs" :key="s" class="sub"> {{ s }} </text>
            </view>
          </view>
        </view>

        <!-- 类别模式：展示类别名，并展开类别里的子区（同样按行政区分组） -->
        <view v-else-if="rule.scope?.mode === 'area_category'" class="list">
          <view v-for="cat in categoryBlocks" :key="cat.name" class="cat-block">
            <view class="cat-name">{{ cat.name }}（{{ cat.count }}）</view>
            <view v-for="g in cat.grouped" :key="g.district" class="group">
              <view class="group-name">{{ g.district }}</view>
              <view class="subs">
                <text v-for="s in g.subs" :key="s" class="sub"> {{ s }} </text>
              </view>
            </view>
          </view>
        </view>

        <view class="actions">
          <button size="mini" @click="close">关闭</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'

/**
 * props:
 * - rule: 单条附加费规则（新结构）
 * - dicts: {
 *     districts: [{ id,name_cn, subs:[{id,name_cn}] }, ...],
 *     categories: [{ id,name, sub_ids:[...] }, ...]
 *   }
 *   👉 这两个字典你在页面挂载时从 /districts 和 /area_categories 拿一次传进来即可
 */
const props = defineProps({
  rule: { type: Object, required: true },
  dicts: { type: Object, default: () => ({ districts: [], categories: [] }) }
})

const pop = ref(null)
const open = () => pop.value?.open()
const close = () => pop.value?.close()

const chipText = computed(() => {
  const m = props.rule?.scope?.mode
  if (m === 'district') return '行政区'
  if (m === 'sub_district') return '子区'
  if (m === 'area_category') return '类别'
  return '范围'
})
const title = computed(() => `${chipText.value}明细`)

/* ---- 字典查找工具 ---- */
function buildDistrictIndex() {
  // subId -> {districtName, subName}
  const idx = {}
  for (const d of props.dicts.districts || []) {
    for (const s of d.subs || []) {
      idx[s.id] = { district: d.name_cn, sub: s.name_cn }
    }
  }
  return idx
}
const subIndex = buildDistrictIndex()

/* ---- district 模式 ---- */
const resolvedNames = computed(() => {
  const names = props.rule?.scope?.names || []
  return names // 传的就是行政区中文名
})

/* ---- sub_district 模式：按行政区分组 ---- */
const groupedSubs = computed(() => {
  const names = props.rule?.scope?.names || [] // 这里传的是“子区中文名”
  // 用 dicts.districts 去反查，按行政区聚合
  const groups = {}
  for (const d of props.dicts.districts || []) {
    const hit = (d.subs || [])
      .filter(s => names.includes(s.name_cn))
      .map(s => s.name_cn)
    if (hit.length) groups[d.name_cn] = hit
  }
  return Object.keys(groups).map(k => ({ district: k, subs: groups[k] }))
})

/* ---- area_category 模式：展示每个类别，展开其子区并分组 ---- */
const categoryBlocks = computed(() => {
  const names = props.rule?.scope?.names || [] // 这里建议传“类别ID数组”或“类别名数组”，下方都兼容
  // 兼容 ID/名称：按 id 优先
  const cats = []
  for (const c of props.dicts.categories || []) {
    if (names.includes(c.id) || names.includes(c.name)) {
      // 将 sub_ids -> 分组
      const groups = {}
      for (const sid of c.sub_ids || []) {
        const hit = subIndex[sid]
        if (!hit) continue
        groups[hit.district] = groups[hit.district] || []
        groups[hit.district].push(hit.sub)
      }
      cats.push({
        name: c.name,
        count: (c.sub_ids || []).length,
        grouped: Object.keys(groups).map(k => ({ district: k, subs: groups[k] }))
      })
    }
  }
  return cats
})
</script>

<style scoped>
.scope-chip { display: inline-flex; margin-left: 8rpx; }
.pop { width: 640rpx; max-height: 70vh; overflow: auto; padding: 24rpx; background: #fff; border-radius: 12rpx; }
.pop-title { font-weight: 600; margin-bottom: 12rpx; }
.list .item { line-height: 1.8; }
.group { margin-bottom: 12rpx; }
.group-name { font-weight: 600; margin: 8rpx 0; }
.subs { display: flex; flex-wrap: wrap; gap: 8rpx; }
.sub { padding: 4rpx 10rpx; background: #f5f6fa; border-radius: 8rpx; }
.cat-block { border-top: 1px dashed #eee; padding-top: 10rpx; margin-top: 10rpx; }
.cat-name { color: #333; font-weight: 600; margin-bottom: 6rpx; }
.actions { display: flex; justify-content: flex-end; margin-top: 12rpx; }
</style>
