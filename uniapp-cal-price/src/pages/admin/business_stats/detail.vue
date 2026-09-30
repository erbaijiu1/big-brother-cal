<template>
  <view class="detail-page">
    <view class="detail-hero">
      <view>
        <text class="eyebrow">CONTRIBUTION LEDGER</text>
        <text class="hero-title">增长贡献明细</text>
        <text class="hero-copy">{{ month }} 对比 {{ compareMonth }} · {{ dimensionLabel }}</text>
      </view>
      <view class="hero-period">
        <text class="period-current">{{ month }}</text>
        <text class="period-vs">VS</text>
        <text>{{ compareMonth }}</text>
      </view>
    </view>

    <scroll-view class="dimension-scroll" scroll-x>
      <view class="dimension-tabs">
        <view
          v-for="item in dimensionOptions"
          :key="item.key"
          class="dimension-tab"
          :class="{ active: dimension === item.key }"
          @click="changeDimension(item.key)"
        >{{ item.label }}</view>
      </view>
    </scroll-view>

    <view class="control-panel">
      <view class="search-box">
        <input
          v-model="keywordInput"
          class="search-input"
          :placeholder="`搜索${dimensionLabel}`"
          confirm-type="search"
          @confirm="applySearch"
        />
        <view v-if="keywordInput" class="clear-search" @click="clearSearch">×</view>
        <button class="search-button" @click="applySearch">搜索</button>
      </view>

      <scroll-view class="sort-scroll" scroll-x>
        <view class="sort-list">
          <view
            v-for="item in sortOptions"
            :key="item.key"
            class="sort-chip"
            :class="{ active: sortBy === item.key }"
            @click="setSort(item.key)"
          >
            {{ item.label }}
            <text v-if="sortBy === item.key" class="sort-arrow">{{ sortOrder === 'desc' ? '↓' : '↑' }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <view v-if="keyword" class="active-filter">
      <view>
        <text class="filter-prefix">当前定位</text>
        <text class="filter-value">{{ dimensionLabel }} · {{ keyword }}</text>
      </view>
      <view class="show-all" @click="clearSearch">查看全部 {{ dimensionLabel }} →</view>
    </view>

    <view class="result-meta">
      <text>{{ keyword ? `找到 ${total} 个匹配结果` : `共 ${total} 个${dimensionLabel}` }}</text>
      <text>第 {{ page }} / {{ totalPages }} 页</text>
    </view>

    <view v-if="loading" class="state-card">
      <view class="pulse-dot"></view>
      <text>正在整理贡献明细…</text>
    </view>

    <view v-else-if="error" class="state-card error-state">
      <text>{{ error }}</text>
      <button class="retry-button" @click="loadDetail">重新加载</button>
    </view>

    <view v-else-if="items.length === 0" class="state-card">
      <text>当前条件下没有数据</text>
    </view>

    <scroll-view v-else class="table-scroll" scroll-x>
      <view class="detail-table">
        <view class="table-row table-head">
          <text class="cell rank-cell">排名</text>
          <text class="cell name-cell">{{ dimensionLabel }}</text>
          <text class="cell delta-cell">利润变化</text>
          <text class="cell">{{ month }}利润</text>
          <text class="cell">{{ compareMonth }}利润</text>
          <text class="cell delta-cell">订单变化</text>
          <text class="cell">{{ month }}订单</text>
          <text class="cell">{{ compareMonth }}订单</text>
          <text class="cell">{{ month }}收入</text>
        </view>

        <view v-for="(item, index) in items" :key="item.name" class="table-row data-row">
          <text class="cell rank-cell">{{ padRank((page - 1) * pageSize + index + 1) }}</text>
          <view class="cell name-cell name-wrap">
            <text class="item-name">{{ item.name }}</text>
            <view class="mini-track">
              <view
                class="mini-fill"
                :class="Number(item.delta_profit) >= 0 ? 'positive-fill' : 'negative-fill'"
                :style="{ width: deltaWidth(item.delta_profit) }"
              ></view>
            </view>
          </view>
          <text class="cell delta-cell strong-value" :class="signClass(item.delta_profit)">{{ signedMoney(item.delta_profit) }}</text>
          <text class="cell">{{ money(item.current_profit) }}</text>
          <text class="cell muted-value">{{ money(item.previous_profit) }}</text>
          <text class="cell delta-cell strong-value" :class="signClass(item.order_delta)">{{ signedInteger(item.order_delta) }}</text>
          <text class="cell">{{ formatInteger(item.current_orders) }}</text>
          <text class="cell muted-value">{{ formatInteger(item.previous_orders) }}</text>
          <text class="cell">{{ money(item.current_revenue) }}</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="!loading && totalPages > 1" class="pagination">
      <button class="page-button" :disabled="page <= 1" @click="changePage(page - 1)">← 上一页</button>
      <view class="page-numbers">
        <view
          v-for="number in visiblePages"
          :key="number"
          class="page-number"
          :class="{ active: page === number }"
          @click="changePage(number)"
        >{{ number }}</view>
      </view>
      <button class="page-button" :disabled="page >= totalPages" @click="changePage(page + 1)">下一页 →</button>
    </view>

    <text class="page-note">利润变化 = 本月实际业绩 − 对比月实际业绩。正数表示推动增长，负数表示形成拖累。</text>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request'

const dimensionOptions = [
  { key: 'products', label: '产品' },
  { key: 'channels', label: '渠道' },
  { key: 'weights', label: '重量段' },
  { key: 'salesmen', label: '业务员' }
]
const sortOptions = [
  { key: 'impact', label: '影响大小' },
  { key: 'delta_profit', label: '利润变化' },
  { key: 'current_profit', label: '本月利润' },
  { key: 'order_delta', label: '订单变化' },
  { key: 'current_orders', label: '本月订单' },
  { key: 'name', label: '名称' }
]

const month = ref('')
const compareMonth = ref('')
const dimension = ref('products')
const keywordInput = ref('')
const keyword = ref('')
const sortBy = ref('impact')
const sortOrder = ref('desc')
const page = ref(1)
const pageSize = 30
const total = ref(0)
const items = ref<any[]>([])
const loading = ref(false)
const error = ref('')

const dimensionLabel = computed(() => dimensionOptions.find(item => item.key === dimension.value)?.label || '明细')
const totalPages = computed(() => Math.max(Math.ceil(total.value / pageSize), 1))
const maxDelta = computed(() => Math.max(...items.value.map(item => Math.abs(Number(item.delta_profit) || 0)), 1))
const visiblePages = computed(() => {
  const start = Math.max(1, Math.min(page.value - 2, totalPages.value - 4))
  const end = Math.min(totalPages.value, start + 4)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

function formatInteger(value: any) {
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(Number(value) || 0)
}

function money(value: any) {
  return `¥${new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(Number(value) || 0)}`
}

function signedMoney(value: any) {
  const amount = Number(value) || 0
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${money(Math.abs(amount))}`
}

function signedInteger(value: any) {
  const amount = Number(value) || 0
  return `${amount > 0 ? '+' : ''}${formatInteger(amount)}`
}

function signClass(value: any) {
  const amount = Number(value) || 0
  if (amount > 0) return 'positive-value'
  if (amount < 0) return 'negative-value'
  return 'neutral-value'
}

function padRank(value: number) {
  return String(value).padStart(2, '0')
}

function deltaWidth(value: any) {
  return `${Math.max(Math.abs(Number(value) || 0) / maxDelta.value * 100, 2)}%`
}

function changeDimension(value: string) {
  if (dimension.value === value) return
  dimension.value = value
  keywordInput.value = ''
  keyword.value = ''
  page.value = 1
  loadDetail()
}

function setSort(value: string) {
  if (sortBy.value === value) {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortBy.value = value
    sortOrder.value = value === 'name' ? 'asc' : 'desc'
  }
  page.value = 1
  loadDetail()
}

function applySearch() {
  keyword.value = keywordInput.value.trim()
  page.value = 1
  loadDetail()
}

function clearSearch() {
  keywordInput.value = ''
  keyword.value = ''
  page.value = 1
  loadDetail()
}

function changePage(value: number) {
  if (value < 1 || value > totalPages.value || value === page.value) return
  page.value = value
  loadDetail()
  uni.pageScrollTo({ scrollTop: 0, duration: 180 })
}

async function loadDetail() {
  if (!month.value || loading.value) return
  loading.value = true
  error.value = ''

  try {
    const response: any = await request({
      url: '/cal_price/business_stats/growth/detail',
      method: 'GET',
      data: {
        month: month.value,
        compare_month: compareMonth.value,
        dimension: dimension.value,
        keyword: keyword.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value,
        page: page.value,
        page_size: pageSize
      }
    })
    if (response?.code !== 200 || !response?.data) throw new Error(response?.message || '接口未返回贡献明细')
    items.value = response.data.items || []
    total.value = Number(response.data.total) || 0
  } catch (err: any) {
    items.value = []
    total.value = 0
    error.value = err?.message || '贡献明细加载失败'
  } finally {
    loading.value = false
  }
}

onLoad((options: any) => {
  month.value = options?.month || ''
  compareMonth.value = options?.compare_month || ''
  if (dimensionOptions.some(item => item.key === options?.dimension)) dimension.value = options.dimension
  keywordInput.value = options?.keyword || ''
  keyword.value = keywordInput.value.trim()
  loadDetail()
})
</script>

<style scoped lang="scss">
.detail-page {
  --ink: #17211d;
  --paper: #f1ece1;
  --cream: #fffaf0;
  --coral: #f26b4f;
  min-height: 100vh;
  padding: 30rpx;
  color: var(--ink);
  background: linear-gradient(180deg, #f6f1e7, var(--paper));
  box-sizing: border-box;
}
.detail-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 30rpx; padding: 42rpx; color: #fff; background: var(--ink); }
.detail-hero > view:first-child { display: flex; flex-direction: column; }
.eyebrow { font-size: 19rpx; letter-spacing: 4rpx; color: var(--coral); }
.hero-title { margin: 12rpx 0; font-family: 'STSong', 'Songti SC', serif; font-size: 50rpx; font-weight: 700; }
.hero-copy { font-size: 22rpx; color: rgba(255,255,255,.62); }
.hero-period { display: flex; align-items: center; gap: 12rpx; font-family: Georgia, serif; font-size: 22rpx; color: rgba(255,255,255,.6); }
.period-current { color: var(--coral); }
.period-vs { padding: 8rpx; border: 1rpx solid rgba(255,255,255,.2); font-size: 15rpx; }
.dimension-scroll { width: 100%; margin-top: 22rpx; }
.dimension-tabs { display: flex; gap: 10rpx; min-width: max-content; }
.dimension-tab { padding: 17rpx 34rpx; border: 1rpx solid #cfc6b7; font-size: 23rpx; background: #f6f1e8; cursor: pointer; }
.dimension-tab.active { border-color: var(--ink); color: #fff; background: var(--ink); }
.control-panel { margin-top: 18rpx; padding: 24rpx; background: var(--cream); }
.search-box { display: flex; align-items: center; }
.search-input { flex: 1; height: 70rpx; padding: 0 22rpx; border: 1rpx solid #cfc7ba; font-size: 23rpx; box-sizing: border-box; }
.clear-search { width: 58rpx; margin-left: -59rpx; font-size: 32rpx; line-height: 68rpx; text-align: center; color: #8a918c; cursor: pointer; }
.search-button { margin: 0 0 0 12rpx; padding: 0 32rpx; border-radius: 0; font-size: 22rpx; line-height: 70rpx; color: #fff; background: var(--coral); }
.search-button::after, .retry-button::after, .page-button::after { border: 0; }
.sort-scroll { width: 100%; margin-top: 18rpx; }
.sort-list { display: flex; gap: 10rpx; min-width: max-content; }
.sort-chip { padding: 11rpx 20rpx; border-bottom: 2rpx solid transparent; font-size: 20rpx; color: #747c77; background: #eee8dc; cursor: pointer; }
.sort-chip.active { border-color: var(--coral); font-weight: 700; color: var(--ink); }
.sort-arrow { margin-left: 5rpx; color: var(--coral); }
.active-filter { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; margin-top: 18rpx; padding: 22rpx 26rpx; border-left: 6rpx solid var(--coral); background: #f7ded3; }
.active-filter > view:first-child { display: flex; flex-direction: column; }
.filter-prefix { font-size: 17rpx; letter-spacing: 2rpx; color: #9b756a; }
.filter-value { margin-top: 5rpx; font-size: 26rpx; font-weight: 700; color: var(--ink); }
.show-all { padding: 9rpx 0; border-bottom: 2rpx solid var(--coral); font-size: 20rpx; font-weight: 700; color: #c94d37; cursor: pointer; }
.result-meta { display: flex; justify-content: space-between; padding: 24rpx 4rpx 14rpx; font-size: 20rpx; color: #737b76; }
.table-scroll { width: 100%; background: var(--cream); }
.detail-table { min-width: 1900rpx; }
.table-row { display: flex; align-items: stretch; min-height: 92rpx; border-top: 1rpx solid #dfd8cc; }
.table-head { min-height: 68rpx; color: #727a75; background: #e9e2d6; }
.cell { display: flex; align-items: center; width: 200rpx; padding: 16rpx; font-size: 21rpx; box-sizing: border-box; }
.rank-cell { width: 90rpx; font-family: Georgia, serif; color: #9a9489; }
.name-cell { width: 310rpx; font-weight: 700; }
.delta-cell { width: 190rpx; }
.data-row:hover { background: #fff7e9; }
.name-wrap { align-items: stretch; flex-direction: column; justify-content: center; }
.item-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mini-track { overflow: hidden; width: 100%; height: 6rpx; margin-top: 12rpx; background: #e5ded2; }
.mini-fill { height: 100%; }
.positive-fill { background: var(--coral); }
.negative-fill { background: #56867b; }
.strong-value { font-family: Georgia, serif; font-size: 23rpx; font-weight: 700; }
.positive-value { color: #d9563e; }
.negative-value { color: #39776b; }
.neutral-value, .muted-value { color: #858c87; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 20rpx; margin-top: 24rpx; }
.page-button { margin: 0; padding: 0 25rpx; border-radius: 0; font-size: 20rpx; line-height: 62rpx; color: #fff; background: var(--ink); }
.page-button[disabled] { color: #999; background: #ddd6ca; }
.page-numbers { display: flex; gap: 7rpx; }
.page-number { width: 52rpx; height: 52rpx; font-family: Georgia, serif; font-size: 20rpx; line-height: 52rpx; text-align: center; background: #e4ddd1; cursor: pointer; }
.page-number.active { color: #fff; background: var(--coral); }
.state-card { display: flex; align-items: center; justify-content: center; gap: 16rpx; min-height: 260rpx; background: var(--cream); color: #737b76; }
.error-state { flex-direction: column; color: #b44635; }
.retry-button { margin: 15rpx 0 0; padding: 0 24rpx; border-radius: 0; font-size: 20rpx; line-height: 58rpx; color: #fff; background: var(--ink); }
.pulse-dot { width: 18rpx; height: 18rpx; border-radius: 50%; background: var(--coral); animation: pulse 1s infinite alternate; }
.page-note { display: block; margin-top: 22rpx; padding: 18rpx 0; border-top: 1rpx dashed #c9c1b4; font-size: 18rpx; line-height: 1.6; color: #777f79; }
@keyframes pulse { to { opacity: .3; transform: scale(.72); } }
@media (min-width: 960px) {
  .detail-page { padding: 42px max(42px, calc((100vw - 1380px) / 2)); }
}
</style>
