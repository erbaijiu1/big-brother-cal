<template>
  <view class="opportunity-page">
    <view class="hero">
      <view class="hero-copy">
        <text class="eyebrow">ACQUISITION LAB / 01</text>
        <text class="hero-title">钱该花在哪类货上？</text>
        <text class="hero-subtitle">从真实首单毛利润与复购证据中，挑出值得小额测试的 Facebook 获客方向。</text>
      </view>
      <view class="hero-seal"><text>TEST</text><text>FIRST</text></view>
    </view>

    <view class="disclaimer">
      <text class="disclaimer-mark">!</text>
      <text>历史新客活跃度不等于 Facebook 获客效率。当前尚未接入广告花费与归因，不展示虚构 CAC / ROI。</text>
    </view>

    <view class="filter-panel">
      <view class="quick-ranges">
        <view v-for="days in [90, 180, 365]" :key="days" class="range-chip" :class="{ active: activeDays === days }" @click="setRange(days)">近{{ days }}天</view>
      </view>
      <view class="date-row">
        <picker mode="date" :value="startDate" @change="startDate = $event.detail.value; activeDays = 0">
          <view class="date-box"><text>开始</text><strong>{{ startDate || '自动' }}</strong></view>
        </picker>
        <text class="date-arrow">→</text>
        <picker mode="date" :value="endDate" @change="endDate = $event.detail.value; activeDays = 0">
          <view class="date-box"><text>结束</text><strong>{{ endDate || '最新数据' }}</strong></view>
        </picker>
        <button class="query-button" :loading="loading" @click="loadData">重新计算</button>
      </view>
      <view class="threshold-row">
        <text>候选门槛</text>
        <view class="threshold-item"><text>订单≥</text><input v-model.number="minOrders" type="number" /></view>
        <view class="threshold-item"><text>历史首次客户≥</text><input v-model.number="minNewCustomers" type="number" /></view>
        <view class="threshold-item"><text>负毛利≤</text><input v-model.number="maxNegativeRate" type="number" /><text>%</text></view>
      </view>
    </view>

    <view v-if="loading && !data" class="state-card"><view class="pulse"></view><text>正在重建客户历史与成熟 cohort…</text></view>
    <view v-else-if="error" class="state-card error-card"><text>{{ error }}</text><button @click="loadData">重试</button></view>

    <template v-else-if="data">
      <view class="period-line">
        <text>统计期 {{ data.period.start_date }} — {{ data.period.end_date }}</text>
        <text>历史起点 {{ data.period.history_start_date }}</text>
      </view>

      <view class="metric-grid">
        <view class="metric-card primary" @click="openOrders('all', '业务订单明细')">
          <text class="metric-label">业务毛利润</text>
          <text class="metric-value">{{ money(data.summary.total_profit) }}</text>
          <text class="metric-foot">毛利率 {{ percent(data.summary.profit_rate_pct) }} · 覆盖 {{ percent(data.summary.profit_order_coverage_pct) }}</text>
        </view>
        <view class="metric-card" @click="openOrders('database_first', '数据库历史首次客户首单')">
          <text class="metric-label">数据库历史首次客户</text>
          <text class="metric-value">{{ integer(data.summary.database_first_customer_count) }}</text>
          <text class="metric-foot">首单毛利润 {{ money(data.summary.database_first_customer_profit) }}</text>
        </view>
        <view class="metric-card" @click="openOrders('all', '有效业务订单')">
          <text class="metric-label">有效业务规模</text>
          <text class="metric-value">{{ integer(data.summary.order_count) }}<small>票</small></text>
          <text class="metric-foot">收入 {{ money(data.summary.total_revenue) }}</text>
        </view>
        <view class="metric-card quality-card" @click="toggleQuality">
          <text class="metric-label">客户识别覆盖</text>
          <text class="metric-value">{{ percent(data.quality.customer_match_rate_pct) }}</text>
          <text class="metric-foot">查看 {{ integer(data.quality.pending_category_order_count + data.quality.unknown_category_order_count) }} 票品类问题 →</text>
        </view>
      </view>

      <view class="coverage-strip">
        <view @click="openOrders('profit_covered', '利润已覆盖订单')"><text class="coverage-number">{{ percent(data.summary.profit_revenue_coverage_pct) }}</text><text>利润收入覆盖率</text></view>
        <view @click="openOrders('missing_cost', '缺成本订单')"><text class="coverage-number">{{ integer(data.summary.missing_cost_order_count) }}</text><text>缺成本票</text></view>
        <view @click="openOrders('negative_profit', '负毛利订单')"><text class="coverage-number">{{ integer(data.summary.negative_profit_order_count) }}</text><text>负毛利票</text></view>
        <view @click="openOrders('unclassified_category', '未归一品类订单')"><text class="coverage-number">{{ percent(data.quality.unclassified_profit_share_pct) }}</text><text>未归一利润占比</text></view>
      </view>

      <view class="section quadrant-section">
        <view class="section-head">
          <view><text class="section-index">01 / SIGNAL</text><text class="section-title">首单机会四象限</text></view>
          <text class="section-note">中位数分界　横轴：历史首次客户数　纵轴：平均首单毛利润</text>
        </view>
        <view class="quadrant">
          <view class="axis axis-x"></view><view class="axis axis-y"></view>
          <text class="axis-cut axis-cut-x">新客中位 {{ numberLabel(newCustomerMedian) }}人</text>
          <text class="axis-cut axis-cut-y">首单毛利中位 {{ money(firstProfitMedian) }}</text>
          <text class="quad-label q1">高价值 / 多新客</text><text class="quad-label q2">高价值 / 少新客</text>
          <text class="quad-label q3">低价值 / 少新客</text><text class="quad-label q4">低价值 / 多新客</text>
          <view v-for="item in data.categories" :key="item.category" class="bubble" :class="statusClass(item.candidate_status)" :style="bubbleStyle(item)" @click="openDetail(item.category)">
            <text>{{ item.category }}</text><small>{{ item.database_first_customer_count }}人</small>
          </view>
        </view>
        <text class="chart-caption">分界采用当前筛选品类的中位数，极值只决定坐标边界；圆越大代表该品类毛利润越高。仅是历史表现，不代表广告平台上的获客难度。</text>
      </view>

      <view class="section candidate-section">
        <view class="section-head">
          <view><text class="section-index">02 / ACTION</text><text class="section-title">广告测试候选</text></view>
          <text class="section-note">规则透明，无综合黑盒分数</text>
        </view>
        <view class="status-tabs">
          <view v-for="name in statusOrder" :key="name" class="status-tab" :class="[statusClass(name), { active: activeStatus === name }]" @click="activeStatus = name">
            <text>{{ name }}</text><strong>{{ groupedCandidates[name]?.length || 0 }}</strong>
          </view>
        </view>
        <view class="candidate-list">
          <view v-for="item in groupedCandidates[activeStatus] || []" :key="item.category" class="candidate-card" @click="openDetail(item.category)">
            <view class="candidate-main">
              <view><text class="candidate-name">{{ item.category }}</text><text class="review-flag">合规待人工确认</text></view>
              <text class="candidate-profit">{{ money(item.avg_database_first_order_profit) }}<small>/历史首次客首单</small></text>
            </view>
            <view class="evidence-row">
              <text>{{ item.order_count }}票</text><text>{{ item.database_first_customer_count }}名历史首次客</text><text>90天复购 {{ percentOrDash(item.cohort_90.repurchase_rate_pct) }}</text><text>利润覆盖 {{ percent(item.profit_order_coverage_pct) }}</text>
            </view>
            <view class="reason-row"><text v-for="reason in item.candidate_reasons" :key="reason">· {{ reason }}</text></view>
          </view>
          <view v-if="!(groupedCandidates[activeStatus] || []).length" class="empty-state">当前筛选下没有该状态品类</view>
        </view>
      </view>

      <view class="section table-section">
        <view class="section-head">
          <view><text class="section-index">03 / EVIDENCE</text><text class="section-title">品类证据表</text></view>
          <text class="section-note">点击任一行查看订单与渠道明细</text>
        </view>
        <scroll-view scroll-x class="table-scroll">
          <view class="data-table">
            <view class="table-row table-header">
              <text class="col category-col">品类</text><text class="col">票数</text><text class="col">毛利润</text><text class="col">利润覆盖</text><text class="col">历史首次客</text><text class="col">品类首次客</text><text class="col">首单均利</text><text class="col">负毛利</text><text class="col">30天复购</text><text class="col">90天复购</text>
            </view>
            <view v-for="item in data.categories" :key="item.category" class="table-row" @click="openDetail(item.category)">
              <view class="col category-col"><text class="category-dot" :class="statusClass(item.candidate_status)"></text><strong>{{ item.category }}</strong></view>
              <text class="col">{{ item.order_count }}</text><text class="col">{{ compactMoney(item.total_profit) }}</text><text class="col">{{ percent(item.profit_order_coverage_pct) }}</text><text class="col">{{ item.database_first_customer_count }}</text><text class="col">{{ item.category_first_customer_count }}</text><text class="col">{{ money(item.avg_database_first_order_profit) }}</text><text class="col">{{ percentOrDash(item.negative_profit_rate_pct) }}</text><text class="col">{{ percentOrDash(item.cohort_30.repurchase_rate_pct) }}</text><text class="col">{{ percentOrDash(item.cohort_90.repurchase_rate_pct) }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </template>

    <view v-if="showQuality && data" class="drawer-mask" @click="showQuality = false">
      <view class="quality-drawer" @click.stop>
        <view class="drawer-head"><view><text class="section-index">DATA QUALITY</text><text class="drawer-title">这份判断有多可靠？</text></view><text class="close" @click="showQuality = false">×</text></view>
        <view class="quality-list">
          <view class="quality-row"><text>客户精确关联</text><strong>{{ percent(data.quality.customer_match_rate_pct) }}</strong><small>只用 company_tracking_no ↔ order_no</small></view>
          <view class="quality-row"><text>利润订单覆盖</text><strong>{{ percent(data.summary.profit_order_coverage_pct) }}</strong><small>{{ data.summary.missing_cost_order_count }}票缺成本不进入利润分母</small></view>
          <view class="quality-row warning"><text>待归一品类</text><strong>{{ integer(data.quality.pending_category_order_count) }}</strong><small>保留总账，暂不进入候选排名</small></view>
          <view class="quality-row warning"><text>未知品类</text><strong>{{ integer(data.quality.unknown_category_order_count) }}</strong><small>不会默认归入普货</small></view>
          <view class="quality-row"><text>取消/作废关键词</text><strong>{{ integer(data.quality.cancellation_or_void_keyword_count) }}</strong><small>只告警，不自动剔除</small></view>
          <view class="quality-row"><text>赔付/补单关键词</text><strong>{{ integer(data.quality.compensation_or_supplement_keyword_count) }}</strong><small>保留真实抵扣和负毛利</small></view>
          <view class="history-note">历史从 {{ data.quality.history_start_date }} 开始。这里的“首次客户”是数据库历史首次出现，存在左截断风险。</view>
        </view>
      </view>
    </view>

    <view v-if="showOrders" class="drawer-mask" @click="showOrders = false">
      <view class="order-drawer" @click.stop>
        <view class="drawer-head"><view><text class="section-index">SOURCE ORDERS</text><text class="drawer-title">{{ orderTitle }}</text></view><text class="close" @click="showOrders = false">×</text></view>
        <text class="drawer-sub">共 {{ integer(orderResult.total) }} 票 · 当前展示前 {{ orderResult.items.length }} 票</text>
        <view v-if="orderLoading" class="order-loading">正在读取原始记录…</view>
        <view v-else class="order-list">
          <view v-for="item in orderResult.items" :key="item.id" class="order-row">
            <view class="order-main"><strong>{{ item.company_tracking_no }}</strong><text>{{ item.shipping_date }}</text></view>
            <view class="order-tags"><text>{{ item.category }}</text><text>{{ item.product_name || '无货物描述' }}</text><text>{{ item.shipping_channel || '未知渠道' }}</text></view>
            <view class="order-money"><text>收入 {{ money(item.shipping_fee) }}</text><text>成本 {{ money(item.shipping_cost) }}</text><strong :class="{ negative: Number(item.gross_profit) < 0 }">毛利 {{ money(item.gross_profit) }}</strong></view>
            <text class="order-customer">{{ item.shipping_customer || '客户未识别' }}</text>
          </view>
          <view v-if="!orderResult.items.length" class="empty-state">当前范围没有对应记录</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request'

const data = ref<any>(null)
const loading = ref(false)
const error = ref('')
const startDate = ref('')
const endDate = ref('')
const activeDays = ref(180)
const minOrders = ref(20)
const minNewCustomers = ref(5)
const maxNegativeRate = ref(30)
const showQuality = ref(false)
const showOrders = ref(false)
const orderLoading = ref(false)
const orderTitle = ref('订单明细')
const orderResult = ref<any>({ total: 0, items: [] })
const activeStatus = ref('值得测试')
const statusOrder = ['值得测试', '需要观察', '暂不建议投放']

const groupedCandidates = computed(() => {
  const groups: Record<string, any[]> = { '值得测试': [], '需要观察': [], '暂不建议投放': [] }
  for (const item of data.value?.categories || []) (groups[item.candidate_status] ||= []).push(item)
  return groups
})

const newCustomerValues = computed(() => (data.value?.categories || []).map((item: any) => Number(item.database_first_customer_count) || 0))
const firstProfitValues = computed(() => (data.value?.categories || []).map((item: any) => Math.max(Number(item.avg_database_first_order_profit) || 0, 0)))
const newCustomerMedian = computed(() => median(newCustomerValues.value))
const firstProfitMedian = computed(() => median(firstProfitValues.value))
const newCustomerExtent = computed(() => extent(newCustomerValues.value))
const firstProfitExtent = computed(() => extent(firstProfitValues.value))
const maxProfit = computed(() => Math.max(...(data.value?.categories || []).map((item: any) => Math.max(Number(item.total_profit) || 0, 0)), 1))

function money(value: any) { return value === null || value === undefined ? '--' : `¥${Math.round(Number(value)).toLocaleString()}` }
function compactMoney(value: any) { const n = Number(value) || 0; return Math.abs(n) >= 10000 ? `¥${(n / 10000).toFixed(1)}万` : money(n) }
function integer(value: any) { return Math.round(Number(value) || 0).toLocaleString() }
function numberLabel(value: any) { const n = Number(value) || 0; return Number.isInteger(n) ? n.toLocaleString() : n.toFixed(1) }
function percent(value: any) { return value === null || value === undefined ? '--' : `${Number(value).toFixed(1)}%` }
function percentOrDash(value: any) { return percent(value) }
function statusClass(status: string) { return status === '值得测试' ? 'test' : status === '暂不建议投放' ? 'stop' : 'watch' }
function toggleQuality() { showQuality.value = !showQuality.value }

async function openOrders(scope: string, title: string) {
  showOrders.value = true
  orderLoading.value = true
  orderTitle.value = title
  try {
    const response: any = await request({
      url: '/cal_price/acquisition/orders', method: 'GET',
      data: { scope, start_date: startDate.value, end_date: endDate.value, page: 1, page_size: 100 }
    })
    orderResult.value = response?.data || { total: 0, items: [] }
  } catch (err: any) {
    orderResult.value = { total: 0, items: [] }
    uni.showToast({ title: err?.message || '订单明细加载失败', icon: 'none' })
  } finally { orderLoading.value = false }
}

function median(values: number[]) {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2
}

function extent(values: number[]) {
  return values.length ? { min: Math.min(...values), max: Math.max(...values) } : { min: 0, max: 0 }
}

function positionAroundMedian(value: number, midpoint: number, min: number, max: number) {
  if (value <= midpoint) return midpoint === min ? 50 : 10 + ((value - min) / (midpoint - min)) * 40
  return midpoint === max ? 50 : 50 + ((value - midpoint) / (max - midpoint)) * 40
}

function bubbleStyle(item: any) {
  const customers = Number(item.database_first_customer_count) || 0
  const firstProfit = Math.max(Number(item.avg_database_first_order_profit) || 0, 0)
  const x = positionAroundMedian(customers, newCustomerMedian.value, newCustomerExtent.value.min, newCustomerExtent.value.max)
  const y = 100 - positionAroundMedian(firstProfit, firstProfitMedian.value, firstProfitExtent.value.min, firstProfitExtent.value.max)
  const size = 72 + Math.sqrt(Math.max(Number(item.total_profit) || 0, 0) / maxProfit.value) * 48
  return { left: `${x}%`, top: `${y}%`, width: `${size}rpx`, height: `${size}rpx` }
}

function subtractDays(value: string, days: number) {
  const d = new Date(`${value}T00:00:00`)
  d.setDate(d.getDate() - days + 1)
  return d.toISOString().slice(0, 10)
}

function setRange(days: number) {
  activeDays.value = days
  const anchor = data.value?.period?.history_end_date || endDate.value
  if (anchor) {
    endDate.value = anchor
    startDate.value = subtractDays(anchor, days)
    loadData()
  }
}

function openDetail(category: string) {
  const query = [`category=${encodeURIComponent(category)}`, `start_date=${startDate.value || data.value.period.start_date}`, `end_date=${endDate.value || data.value.period.end_date}`]
  uni.navigateTo({ url: `/pages/admin/acquisition/detail?${query.join('&')}` })
}

async function loadData() {
  if (startDate.value && endDate.value && startDate.value > endDate.value) return uni.showToast({ title: '开始日期不能晚于结束日期', icon: 'none' })
  loading.value = true
  error.value = ''
  try {
    const response: any = await request({
      url: '/cal_price/acquisition/overview', method: 'GET',
      data: { start_date: startDate.value, end_date: endDate.value, min_orders: minOrders.value, min_new_customers: minNewCustomers.value, max_negative_rate_pct: maxNegativeRate.value }
    })
    if (response?.code !== 200 || !response?.data) throw new Error(response?.message || '接口未返回获客分析')
    data.value = response.data
    if (!startDate.value && !endDate.value) {
      startDate.value = response.data.period.start_date
      endDate.value = response.data.period.end_date
    }
  } catch (err: any) { error.value = err?.message || '获客分析加载失败' }
  finally { loading.value = false }
}

onShow(loadData)
</script>

<style scoped lang="scss">
.opportunity-page { --ink:#15231c; --paper:#f2ecdf; --cream:#fffaf0; --coral:#ed6547; --lime:#c9dd74; --amber:#e6ad54; min-height:100vh; padding:30rpx; color:var(--ink); background:radial-gradient(circle at 95% 2%,rgba(201,221,116,.24),transparent 25%),linear-gradient(180deg,#f8f3e9,var(--paper)); box-sizing:border-box; }
.hero { position:relative; display:flex; justify-content:space-between; overflow:hidden; padding:48rpx 42rpx; color:#fff; background:var(--ink); border-radius:6rpx 54rpx 6rpx 6rpx; }
.hero::after { content:''; position:absolute; width:320rpx; height:320rpx; right:-80rpx; bottom:-210rpx; border:2rpx solid rgba(255,255,255,.14); border-radius:50%; }
.hero-copy { position:relative; z-index:1; display:flex; flex-direction:column; max-width:78%; }
.eyebrow,.section-index { font-size:19rpx; letter-spacing:4rpx; color:var(--coral); }
.hero-title { margin-top:14rpx; font-family:'Songti SC','STSong',serif; font-size:59rpx; font-weight:700; letter-spacing:2rpx; }
.hero-subtitle { margin-top:16rpx; color:rgba(255,255,255,.68); font-size:24rpx; line-height:1.7; }
.hero-seal { position:relative; z-index:1; align-self:center; display:flex; flex-direction:column; align-items:center; justify-content:center; width:108rpx; height:108rpx; border:2rpx solid var(--lime); border-radius:50%; color:var(--lime); font-family:Georgia,serif; font-size:18rpx; letter-spacing:2rpx; transform:rotate(9deg); }
.disclaimer { display:flex; gap:18rpx; align-items:center; padding:18rpx 22rpx; color:#5f553a; background:#fff1ce; border-left:6rpx solid var(--amber); font-size:22rpx; line-height:1.5; }
.disclaimer-mark { flex:none; width:34rpx; height:34rpx; border:1rpx solid #8a6d31; border-radius:50%; text-align:center; line-height:34rpx; font-family:Georgia,serif; }
.filter-panel { margin:24rpx 0; padding:24rpx; background:rgba(255,250,240,.86); border:1rpx solid rgba(21,35,28,.1); }
.quick-ranges,.date-row,.threshold-row,.coverage-strip,.status-tabs,.evidence-row { display:flex; align-items:center; gap:14rpx; }
.range-chip { padding:10rpx 20rpx; border:1rpx solid #c9c0b0; font-size:22rpx; }.range-chip.active { color:#fff; background:var(--ink); border-color:var(--ink); }
.date-row { margin-top:18rpx; }.date-box { min-width:190rpx; padding:12rpx 16rpx; border-bottom:2rpx solid var(--ink); }.date-box text,.date-box strong { display:block; }.date-box text { color:#7b817d; font-size:18rpx; }.date-box strong { margin-top:5rpx; font-size:24rpx; }.date-arrow { color:#8b918d; }
.query-button { margin:0 0 0 auto; padding:0 26rpx; color:#fff; background:var(--coral); border-radius:3rpx; font-size:22rpx; line-height:66rpx; }.query-button::after { border:0; }
.threshold-row { flex-wrap:wrap; margin-top:20rpx; padding-top:18rpx; border-top:1rpx dashed #d1c9bb; color:#69716c; font-size:20rpx; }.threshold-item { display:flex; align-items:center; gap:4rpx; }.threshold-item input { width:74rpx; height:44rpx; color:var(--ink); text-align:center; background:#eee7da; }
.state-card { display:flex; justify-content:center; gap:16rpx; margin-top:40rpx; padding:60rpx; background:var(--cream); }.pulse { width:20rpx; height:20rpx; background:var(--coral); border-radius:50%; animation:pulse 1.2s infinite; }.error-card { color:#a33; }.error-card button { margin:0; font-size:22rpx; }
.period-line { display:flex; justify-content:space-between; margin:28rpx 4rpx 16rpx; color:#737b76; font-size:21rpx; }
.metric-grid { display:flex; flex-wrap:wrap; gap:16rpx; }.metric-card { width:calc(50% - 8rpx); min-height:174rpx; padding:26rpx; background:var(--cream); border-top:5rpx solid #a9b7aa; box-sizing:border-box; box-shadow:0 12rpx 28rpx rgba(30,40,34,.05); }.metric-card.primary { background:#f8ddd4; border-color:var(--coral); }.quality-card { cursor:pointer; }.metric-label,.metric-foot { display:block; color:#667068; font-size:21rpx; }.metric-value { display:block; margin:17rpx 0 12rpx; font-family:Georgia,'Times New Roman',serif; font-size:42rpx; font-weight:700; }.metric-value small { margin-left:5rpx; font-family:inherit; font-size:22rpx; }
.coverage-strip { justify-content:space-between; margin-top:18rpx; padding:22rpx; background:var(--ink); color:#fff; }.coverage-strip view { flex:1; text-align:center; border-right:1rpx solid rgba(255,255,255,.15); }.coverage-strip view:last-child { border:0; }.coverage-strip text { display:block; font-size:18rpx; color:rgba(255,255,255,.6); }.coverage-number { margin-bottom:6rpx; color:var(--lime)!important; font-family:Georgia,serif; font-size:27rpx!important; }
.section { margin-top:24rpx; padding:32rpx 28rpx; background:var(--cream); box-shadow:0 14rpx 32rpx rgba(30,40,34,.05); }.section-head { display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:25rpx; }.section-head view { display:flex; flex-direction:column; }.section-title { margin-top:7rpx; font-family:'Songti SC','STSong',serif; font-size:38rpx; font-weight:700; }.section-note { color:#8a918c; font-size:19rpx; }
.quadrant { position:relative; height:480rpx; overflow:hidden; background:linear-gradient(90deg,rgba(237,101,71,.035) 50%,rgba(201,221,116,.08) 50%),linear-gradient(180deg,rgba(201,221,116,.08) 50%,transparent 50%); border:1rpx solid #d8d0c2; }.axis { position:absolute; background:#918f82; opacity:.5; }.axis-x { left:4%; right:4%; top:50%; height:1rpx; }.axis-y { top:5%; bottom:5%; left:50%; width:1rpx; }.axis-cut { position:absolute; z-index:1; padding:3rpx 8rpx; color:#74796f; background:rgba(255,250,240,.9); font-size:15rpx; line-height:1.4; }.axis-cut-x { top:12rpx; left:50%; transform:translateX(-50%); }.axis-cut-y { top:50%; left:12rpx; transform:translateY(-50%); }.quad-label { position:absolute; z-index:1; color:#9b9a8e; font-size:17rpx; }.q1{top:12rpx;right:16rpx}.q2{top:12rpx;left:16rpx}.q3{bottom:12rpx;left:16rpx}.q4{right:16rpx;bottom:12rpx}
.bubble { position:absolute; z-index:2; display:flex; flex-direction:column; align-items:center; justify-content:center; transform:translate(-50%,-50%); border-radius:50%; color:#fff; font-size:19rpx; text-align:center; box-shadow:0 8rpx 20rpx rgba(21,35,28,.18); }.bubble small { margin-top:3rpx; font-size:15rpx; opacity:.75; }.bubble.test,.category-dot.test { background:#527b55; }.bubble.watch,.category-dot.watch { background:#c28a38; }.bubble.stop,.category-dot.stop { background:#a95648; }.chart-caption { display:block; margin-top:14rpx; color:#858b87; font-size:19rpx; }
.status-tabs { margin-bottom:20rpx; }.status-tab { display:flex; gap:10rpx; padding:12rpx 18rpx; color:#69706b; background:#ece6da; font-size:21rpx; }.status-tab strong { font-family:Georgia,serif; }.status-tab.active.test { color:#fff; background:#527b55; }.status-tab.active.watch { color:#fff; background:#c28a38; }.status-tab.active.stop { color:#fff; background:#a95648; }
.candidate-card { padding:22rpx 0; border-bottom:1rpx solid #ded8cc; }.candidate-main { display:flex; justify-content:space-between; align-items:flex-start; }.candidate-name { font-family:'Songti SC','STSong',serif; font-size:31rpx; font-weight:700; }.review-flag { margin-left:12rpx; padding:4rpx 8rpx; color:#8b6030; background:#f5e4c6; font-size:16rpx; }.candidate-profit { color:var(--coral); font-family:Georgia,serif; font-size:28rpx; font-weight:700; }.candidate-profit small { margin-left:4rpx; color:#7d847f; font-family:inherit; font-size:16rpx; }.evidence-row { flex-wrap:wrap; margin-top:14rpx; color:#5f6963; font-size:19rpx; }.evidence-row text { padding-right:12rpx; border-right:1rpx solid #ccc5b9; }.reason-row { display:flex; flex-wrap:wrap; gap:8rpx 15rpx; margin-top:12rpx; color:#8a8173; font-size:18rpx; }.empty-state { padding:45rpx 0; color:#999; text-align:center; }
.table-scroll { width:100%; }.data-table { min-width:1720rpx; }.table-row { display:flex; min-height:76rpx; align-items:center; border-bottom:1rpx solid #ddd6c9; font-size:20rpx; }.table-header { min-height:64rpx; color:#727a75; background:#ece7dc; font-weight:700; }.col { flex:none; width:155rpx; padding:0 12rpx; box-sizing:border-box; }.category-col { display:flex; align-items:center; width:190rpx; }.category-dot { display:inline-block; width:13rpx; height:13rpx; margin-right:10rpx; border-radius:50%; }
.drawer-mask { position:fixed; z-index:20; inset:0; background:rgba(10,18,14,.48); }.quality-drawer,.order-drawer { position:absolute; top:0; right:0; bottom:0; width:82%; max-width:680rpx; padding:36rpx; overflow-y:auto; background:#f9f3e7; box-sizing:border-box; box-shadow:-20rpx 0 50rpx rgba(0,0,0,.18); }.order-drawer{max-width:900rpx}.drawer-head { display:flex; justify-content:space-between; align-items:flex-start; }.drawer-head view { display:flex; flex-direction:column; }.drawer-title { margin-top:10rpx; font-family:'Songti SC','STSong',serif; font-size:38rpx; font-weight:700; }.drawer-sub{display:block;margin-top:12rpx;color:#7c847f;font-size:19rpx}.close { font-size:48rpx; line-height:1; }.quality-list { margin-top:25rpx; }.quality-row { display:grid; grid-template-columns:1fr auto; gap:8rpx; padding:20rpx 0; border-bottom:1rpx solid #d9d1c3; }.quality-row strong { color:#416846; font-family:Georgia,serif; font-size:28rpx; }.quality-row small { grid-column:1 / 3; color:#7b827d; font-size:18rpx; }.quality-row.warning strong { color:#b26f35; }.history-note { margin-top:24rpx; padding:20rpx; color:#5c5549; background:#eee2cb; font-size:20rpx; line-height:1.6; }.order-loading{padding:70rpx 0;color:#777;text-align:center}.order-list{margin-top:22rpx}.order-row{padding:20rpx 0;border-bottom:1rpx solid #d9d1c3}.order-main,.order-money{display:flex;justify-content:space-between;gap:12rpx}.order-main strong{font-family:Georgia,serif}.order-main text,.order-customer{color:#737c76;font-size:18rpx}.order-tags{display:flex;flex-wrap:wrap;gap:8rpx;margin:12rpx 0}.order-tags text{padding:5rpx 9rpx;background:#e9e1d4;font-size:17rpx}.order-money{font-size:18rpx}.order-money strong{color:#47724c}.order-money strong.negative{color:#b24f42}.order-customer{display:block;margin-top:9rpx}
@keyframes pulse { 50% { opacity:.3; transform:scale(.7); } }
@media (min-width:900px) { .opportunity-page{padding:42px 6vw}.hero{padding:50px 54px}.metric-card{width:calc(25% - 12rpx)}.quadrant{height:560px}.quality-drawer{width:520px}.section{padding:38px}.hero-title{font-size:58px} }
</style>
