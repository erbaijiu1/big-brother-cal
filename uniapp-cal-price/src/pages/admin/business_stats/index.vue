<template>
  <view class="dashboard">
    <view class="hero">
      <view class="hero-copy">
        <text class="eyebrow">BUSINESS PULSE</text>
        <text class="hero-title">经营雷达</text>
        <text class="hero-subtitle">从真实订单里，找到值得复制的生意。</text>
      </view>
      <view class="hero-mark">¥</view>
    </view>

    <view class="filter-panel">
      <view class="date-field">
        <text class="field-label">开始日期</text>
        <picker mode="date" :value="startDate" @change="startDate = $event.detail.value">
          <view class="date-value">{{ startDate || '最早记录' }}</view>
        </picker>
      </view>
      <view class="date-divider">—</view>
      <view class="date-field">
        <text class="field-label">结束日期</text>
        <picker mode="date" :value="endDate" @change="endDate = $event.detail.value">
          <view class="date-value">{{ endDate || '最新记录' }}</view>
        </picker>
      </view>
      <button class="query-button" :loading="loading" @click="loadStats">查询</button>
      <button v-if="startDate || endDate" class="reset-button" @click="resetDates">全部</button>
    </view>

    <view v-if="loading && !stats" class="state-card">
      <view class="pulse-dot"></view>
      <text>正在汇总经营数据…</text>
    </view>

    <view v-else-if="error" class="state-card error-card">
      <text class="state-title">数据加载失败</text>
      <text class="state-copy">{{ error }}</text>
      <button class="retry-button" @click="loadStats">重新加载</button>
    </view>

    <template v-else-if="stats">
      <view class="period-line">
        <text>业绩范围 {{ stats.summary.min_shipping_date || '--' }} 至 {{ stats.summary.max_shipping_date || '--' }}</text>
        <text class="record-count">{{ formatInteger(stats.summary.order_count) }} 票</text>
      </view>

      <view class="metric-grid">
        <view class="metric-card metric-primary">
          <text class="metric-label">总利润</text>
          <text class="metric-value">{{ money(stats.summary.total_profit) }}</text>
          <text class="metric-foot">利润率 {{ percent(stats.summary.profit_rate_pct) }}</text>
        </view>
        <view class="metric-card">
          <text class="metric-label">总运费收入</text>
          <text class="metric-value">{{ money(stats.summary.total_shipping_fee) }}</text>
          <text class="metric-foot">成本 {{ money(stats.summary.total_shipping_cost) }}</text>
        </view>
        <view class="metric-card">
          <text class="metric-label">平均单票利润</text>
          <text class="metric-value">{{ money(stats.summary.avg_order_profit) }}</text>
          <text class="metric-foot">{{ formatInteger(stats.summary.trade_count) }} 条托运记录</text>
        </view>
        <view class="metric-card">
          <text class="metric-label">客户数</text>
          <text class="metric-value">{{ formatInteger(stats.summary.customer_count) }}</text>
          <text class="metric-foot">去重托运客户</text>
        </view>
      </view>

      <view class="section dark-section">
        <view class="section-heading light-heading">
          <view>
            <text class="section-kicker">01 / TREND</text>
            <text class="section-title">月度经营走势</text>
          </view>
          <text class="section-note">柱长代表月利润</text>
        </view>
        <scroll-view class="month-scroll" scroll-x>
          <view class="month-chart">
            <view
              v-for="item in stats.monthly"
              :key="item.month"
              class="month-column"
              :class="{ 'month-selected': selectedMonth === item.month }"
              @click="openGrowth(item.month)"
            >
              <text class="month-profit">{{ compactMoney(item.total_profit) }}</text>
              <view class="month-track">
                <view class="month-bar" :style="{ height: barHeight(item.total_profit, maxMonthlyProfit) }"></view>
              </view>
              <text class="month-label">{{ item.month }}</text>
              <text class="month-orders">{{ item.order_count }}票</text>
            </view>
          </view>
        </scroll-view>
        <text class="month-hint">点击月份，查看增长来自哪里 ↑</text>
      </view>

      <view v-if="growthLoading" class="growth-loading">
        <view class="pulse-dot"></view>
        <text>正在拆解 {{ selectedMonth }} 的增长来源…</text>
      </view>

      <view v-else-if="growthError" class="growth-loading growth-error">
        <text>{{ growthError }}</text>
        <button class="growth-retry" @click="openGrowth(selectedMonth)">重试</button>
      </view>

      <view v-else-if="growth" class="growth-panel">
        <view class="growth-header">
          <view>
            <text class="growth-kicker">GROWTH DIAGNOSIS</text>
            <text class="growth-title">{{ growth.month }} 增长诊断</text>
          </view>
          <view class="compare-badge">对比 {{ growth.compare_month }}</view>
        </view>

        <view class="insight-strip">
          <text class="insight-mark">↗</text>
          <text class="insight-copy">{{ growthInsight }}</text>
        </view>

        <view class="growth-metrics">
          <view class="growth-metric">
            <text class="growth-metric-label">利润变化</text>
            <text class="growth-metric-value" :class="signClass(growth.summary.profit_delta)">{{ signedMoney(growth.summary.profit_delta) }}</text>
            <text class="growth-metric-rate">{{ signedPercent(growth.summary.profit_change_pct) }}</text>
          </view>
          <view class="growth-metric">
            <text class="growth-metric-label">订单变化</text>
            <text class="growth-metric-value" :class="signClass(growth.summary.order_delta)">{{ signedInteger(growth.summary.order_delta) }}票</text>
            <text class="growth-metric-rate">{{ signedPercent(growth.summary.order_change_pct) }}</text>
          </view>
          <view class="growth-metric">
            <text class="growth-metric-label">单票利润变化</text>
            <text class="growth-metric-value" :class="signClass(growth.summary.avg_profit_delta)">{{ signedMoney(growth.summary.avg_profit_delta) }}</text>
            <text class="growth-metric-rate">{{ signedPercent(growth.summary.avg_profit_change_pct) }}</text>
          </view>
        </view>

        <view class="bridge-card">
          <view class="bridge-title-row">
            <text class="bridge-title">利润增长桥</text>
            <text class="bridge-caption">数量贡献 + 单票利润贡献 = 总变化</text>
          </view>
          <view class="bridge-flow">
            <view class="bridge-node base-node">
              <text class="bridge-node-label">{{ growth.compare_month }}</text>
              <text class="bridge-node-value">{{ compactMoney(growth.summary.previous_profit) }}</text>
            </view>
            <view class="bridge-arrow">→</view>
            <view class="bridge-node effect-node">
              <text class="bridge-node-label">订单数量</text>
              <text class="bridge-node-value" :class="signClass(growth.summary.volume_effect)">{{ signedCompactMoney(growth.summary.volume_effect) }}</text>
              <text class="bridge-node-foot">贡献 {{ percent(growth.summary.volume_effect_pct) }}</text>
            </view>
            <view class="bridge-plus">+</view>
            <view class="bridge-node effect-node">
              <text class="bridge-node-label">单票利润</text>
              <text class="bridge-node-value" :class="signClass(growth.summary.unit_effect)">{{ signedCompactMoney(growth.summary.unit_effect) }}</text>
              <text class="bridge-node-foot">贡献 {{ percent(growth.summary.unit_effect_pct) }}</text>
            </view>
            <view class="bridge-arrow">→</view>
            <view class="bridge-node current-node">
              <text class="bridge-node-label">{{ growth.month }}</text>
              <text class="bridge-node-value">{{ compactMoney(growth.summary.current_profit) }}</text>
            </view>
          </view>
        </view>

        <view class="diagnosis-grid">
          <view class="contribution-card">
            <view class="card-title-row">
              <view>
                <text class="card-eyebrow">CONTRIBUTION</text>
                <text class="card-title">谁推动了变化</text>
              </view>
              <view class="detail-link" @click="goContributionDetail()">查看全部与排序 →</view>
            </view>
            <scroll-view class="dimension-tabs" scroll-x>
              <view class="dimension-tabs-inner">
                <view
                  v-for="item in dimensionOptions"
                  :key="item.key"
                  class="dimension-tab"
                  :class="{ active: activeDimension === item.key }"
                  @click="activeDimension = item.key"
                >{{ item.label }}</view>
              </view>
            </scroll-view>
            <view class="contribution-list">
              <view
                v-for="(item, index) in activeContributions"
                :key="item.name"
                class="contribution-row"
                hover-class="contribution-row-active"
                @click="goContributionDetail(item.name)"
              >
                <view class="contribution-topline">
                  <text class="contribution-rank">{{ padRank(index + 1) }}</text>
                  <text class="contribution-name">{{ item.name }}</text>
                  <text class="contribution-delta" :class="signClass(item.delta_profit)">{{ signedMoney(item.delta_profit) }}</text>
                  <text class="contribution-open">›</text>
                </view>
                <view class="delta-track">
                  <view
                    class="delta-fill"
                    :class="Number(item.delta_profit) >= 0 ? 'positive-fill' : 'negative-fill'"
                    :style="{ width: contributionWidth(item.delta_profit) }"
                  ></view>
                </view>
                <text class="contribution-foot">订单 {{ signedInteger(item.order_delta) }}票 · 本月 {{ item.current_orders }}票</text>
              </view>
            </view>
          </view>

          <view class="customer-change-card">
            <view class="card-title-row">
              <view>
                <text class="card-eyebrow">CUSTOMER FLOW</text>
                <text class="card-title">客户从哪里来</text>
              </view>
              <text class="card-caption">仅统计可关联订单</text>
            </view>
            <view class="segment-list">
              <view v-for="item in customerSegments" :key="item.name" class="segment-row">
                <view class="segment-symbol" :class="`segment-${item.name}`">{{ segmentSymbol(item.name) }}</view>
                <view class="segment-main">
                  <view class="segment-title-line">
                    <text class="segment-title">{{ segmentLabel(item.name) }}</text>
                    <text class="segment-count">{{ item.customer_count }} 位</text>
                  </view>
                  <text class="segment-description">{{ segmentDescription(item) }}</text>
                </view>
                <text class="segment-profit" :class="signClass(item.delta_profit)">{{ signedCompactMoney(item.delta_profit) }}</text>
              </view>
            </view>
          </view>
        </view>

        <text class="diagnosis-boundary">这里展示的是经营结构贡献；若要判断是否由 Facebook 广告造成，还需要客户来源和广告活动数据。</text>
      </view>

      <view class="section">
        <view class="section-heading">
          <view>
            <text class="section-kicker">02 / PRODUCT</text>
            <text class="section-title">最赚钱的货</text>
          </view>
          <text class="section-note">按总利润排序</text>
        </view>
        <view class="rank-list">
          <view v-for="(item, index) in stats.products" :key="item.name" class="rank-row">
            <text class="rank-number">{{ padRank(index + 1) }}</text>
            <view class="rank-main">
              <view class="rank-line">
                <text class="rank-name">{{ item.name }}</text>
                <text class="rank-value">{{ money(item.total_profit) }}</text>
              </view>
              <view class="bar-track">
                <view class="bar-fill coral" :style="{ width: barWidth(item.total_profit, maxProductProfit) }"></view>
              </view>
              <view class="rank-meta">
                <text>{{ item.order_count }} 票</text>
                <text>单票 {{ money(item.avg_order_profit) }}</text>
                <text>利润率 {{ percent(item.profit_rate_pct) }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <view class="split-layout">
        <view class="section split-section">
          <view class="section-heading">
            <view>
              <text class="section-kicker">03 / WEIGHT</text>
              <text class="section-title">重量段结构</text>
            </view>
          </view>
          <view class="distribution-list">
            <view v-for="item in stats.weights" :key="item.name" class="distribution-row">
              <view class="distribution-labels">
                <text>{{ item.name }}</text>
                <text>{{ percent(item.order_pct) }}</text>
              </view>
              <view class="bar-track soft-track">
                <view class="bar-fill ink" :style="{ width: `${Math.max(Number(item.order_pct) || 0, 1)}%` }"></view>
              </view>
              <text class="distribution-detail">{{ item.order_count }} 票 · 利润 {{ money(item.total_profit) }}</text>
            </view>
          </view>
        </view>

        <view class="section split-section">
          <view class="section-heading">
            <view>
              <text class="section-kicker">04 / LOYALTY</text>
              <text class="section-title">客户复购结构</text>
            </view>
          </view>
          <view class="loyalty-grid">
            <view v-for="item in stats.repurchase" :key="item.name" class="loyalty-card">
              <text class="loyalty-frequency">{{ item.name }}</text>
              <text class="loyalty-count">{{ item.customer_count }}</text>
              <text class="loyalty-percent">占 {{ percent(item.customer_pct) }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <view class="section-heading">
          <view>
            <text class="section-kicker">05 / CHANNEL</text>
            <text class="section-title">渠道经营排名</text>
          </view>
          <text class="section-note">横向滑动查看完整数据</text>
        </view>
        <scroll-view class="table-scroll" scroll-x>
          <view class="data-table">
            <view class="table-row table-head">
              <text class="cell cell-name">渠道</text>
              <text class="cell">票数</text>
              <text class="cell">收入</text>
              <text class="cell">利润</text>
              <text class="cell">单票利润</text>
              <text class="cell">利润率</text>
            </view>
            <view v-for="item in stats.channels" :key="item.name" class="table-row">
              <text class="cell cell-name">{{ item.name }}</text>
              <text class="cell">{{ item.order_count }}</text>
              <text class="cell">{{ money(item.total_shipping_fee) }}</text>
              <text class="cell profit-cell">{{ money(item.total_profit) }}</text>
              <text class="cell">{{ money(item.avg_order_profit) }}</text>
              <text class="cell">{{ percent(item.profit_rate_pct) }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="section">
        <view class="section-heading">
          <view>
            <text class="section-kicker">06 / CUSTOMER</text>
            <text class="section-title">高价值客户</text>
          </view>
          <text class="section-note">按可关联订单利润排序</text>
        </view>
        <scroll-view class="table-scroll" scroll-x>
          <view class="data-table customer-table">
            <view class="table-row table-head">
              <text class="cell cell-customer">客户</text>
              <text class="cell">票数</text>
              <text class="cell">活跃月</text>
              <text class="cell">收入</text>
              <text class="cell">利润</text>
              <text class="cell">利润率</text>
            </view>
            <view v-for="item in stats.top_customers" :key="item.name" class="table-row">
              <text class="cell cell-customer">{{ item.name }}</text>
              <text class="cell">{{ item.order_count }}</text>
              <text class="cell">{{ item.active_months }}</text>
              <text class="cell">{{ money(item.total_shipping_fee) }}</text>
              <text class="cell profit-cell">{{ money(item.total_profit) }}</text>
              <text class="cell">{{ percent(item.profit_rate_pct) }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="quality-card">
        <view>
          <text class="quality-kicker">DATA CONFIDENCE</text>
          <text class="quality-title">两表关联覆盖率 {{ percent(stats.join_quality.matched_pct) }}</text>
          <text class="quality-copy">
            托运编码 → 托运号码：{{ formatInteger(stats.join_quality.matched_count) }} / {{ formatInteger(stats.join_quality.trade_total) }} 条命中。高价值客户榜仅统计可可靠关联的数据。
          </text>
        </view>
        <view class="quality-ring" :style="qualityRingStyle">
          <view class="quality-ring-inner">{{ Math.round(Number(stats.join_quality.matched_pct) || 0) }}%</view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request'

const loading = ref(false)
const error = ref('')
const stats = ref<any>(null)
const startDate = ref('')
const endDate = ref('')
const growthLoading = ref(false)
const growthError = ref('')
const growth = ref<any>(null)
const selectedMonth = ref('')
const activeDimension = ref('products')

const dimensionOptions = [
  { key: 'products', label: '产品' },
  { key: 'channels', label: '渠道' },
  { key: 'weights', label: '重量段' },
  { key: 'salesmen', label: '业务员' }
]

const maxMonthlyProfit = computed(() => Math.max(...(stats.value?.monthly || []).map((item: any) => Math.max(Number(item.total_profit) || 0, 0)), 1))
const maxProductProfit = computed(() => Math.max(...(stats.value?.products || []).map((item: any) => Math.max(Number(item.total_profit) || 0, 0)), 1))
const qualityRingStyle = computed(() => {
  const value = Math.min(Math.max(Number(stats.value?.join_quality?.matched_pct) || 0, 0), 100)
  return { background: `conic-gradient(#f26b4f ${value}%, rgba(255,255,255,.14) ${value}% 100%)` }
})
const activeContributions = computed(() => growth.value?.contributions?.[activeDimension.value] || [])
const maxContribution = computed(() => Math.max(...activeContributions.value.map((item: any) => Math.abs(Number(item.delta_profit) || 0)), 1))
const customerSegments = computed(() => {
  const order = ['new', 'retained', 'reactivated', 'lost']
  const segments = growth.value?.customer_segments || []
  return [...segments].sort((a: any, b: any) => order.indexOf(a.name) - order.indexOf(b.name))
})
const growthInsight = computed(() => {
  if (!growth.value) return ''

  const summary = growth.value.summary
  const positive = (growth.value.contributions?.products || [])
    .filter((item: any) => Number(item.delta_profit) > 0)
    .sort((a: any, b: any) => Number(b.delta_profit) - Number(a.delta_profit))[0]
  const direction = Number(summary.profit_delta) >= 0 ? '增长' : '下降'
  const mainDriver = Math.abs(Number(summary.volume_effect_pct)) >= Math.abs(Number(summary.unit_effect_pct)) ? '订单数量变化' : '单票利润变化'
  const productText = positive ? `，其中“${positive.name}”贡献最突出` : ''
  return `${growth.value.month} 利润环比${direction} ${percent(Math.abs(Number(summary.profit_change_pct) || 0))}，主要由${mainDriver}推动${productText}。`
})

function formatInteger(value: any) {
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(Number(value) || 0)
}

function money(value: any) {
  return `¥${new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(Number(value) || 0)}`
}

function compactMoney(value: any) {
  const amount = Number(value) || 0
  if (Math.abs(amount) >= 10000) return `¥${(amount / 10000).toFixed(1)}万`
  return `¥${Math.round(amount)}`
}

function percent(value: any) {
  return `${(Number(value) || 0).toFixed(1)}%`
}

function signedPercent(value: any) {
  if (value === null || value === undefined) return '--'
  const amount = Number(value) || 0
  return `${amount > 0 ? '+' : ''}${amount.toFixed(1)}%`
}

function signedMoney(value: any) {
  const amount = Number(value) || 0
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${money(Math.abs(amount))}`
}

function signedCompactMoney(value: any) {
  const amount = Number(value) || 0
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${compactMoney(Math.abs(amount))}`
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

function barWidth(value: any, max: number) {
  const width = Math.max((Math.max(Number(value) || 0, 0) / max) * 100, 2)
  return `${Math.min(width, 100)}%`
}

function barHeight(value: any, max: number) {
  const height = Math.max((Math.max(Number(value) || 0, 0) / max) * 100, 4)
  return `${Math.min(height, 100)}%`
}

function contributionWidth(value: any) {
  const width = Math.max(Math.abs(Number(value) || 0) / maxContribution.value * 100, 2)
  return `${Math.min(width, 100)}%`
}

function segmentLabel(name: string) {
  return ({ new: '新客户', retained: '持续客户', reactivated: '回流客户', lost: '流失客户' } as Record<string, string>)[name] || name
}

function segmentSymbol(name: string) {
  return ({ new: '+', retained: '↔', reactivated: '↻', lost: '−' } as Record<string, string>)[name] || '·'
}

function segmentDescription(item: any) {
  if (item.name === 'new') return `${item.current_orders} 票首次成交`
  if (item.name === 'retained') return `${item.growing_customers} 位客户利润继续增长`
  if (item.name === 'reactivated') return `${item.current_orders} 票重新激活`
  if (item.name === 'lost') return `上月 ${item.previous_orders} 票本月未延续`
  return ''
}

function goContributionDetail(keyword: string = '') {
  if (!growth.value) return

  const query = [
    `month=${encodeURIComponent(growth.value.month)}`,
    `compare_month=${encodeURIComponent(growth.value.compare_month)}`,
    `dimension=${encodeURIComponent(activeDimension.value)}`
  ]
  if (keyword) query.push(`keyword=${encodeURIComponent(keyword)}`)

  const url = `/pages/admin/business_stats/detail?${query.join('&')}`
  uni.navigateTo({ url })
}

async function openGrowth(month: string) {
  if (!month || growthLoading.value) return

  selectedMonth.value = month
  growthLoading.value = true
  growthError.value = ''

  try {
    const response: any = await request({
      url: '/cal_price/business_stats/growth',
      method: 'GET',
      data: { month }
    })
    if (response?.code !== 200 || !response?.data) throw new Error(response?.message || '接口未返回增长诊断')
    growth.value = response.data
  } catch (err: any) {
    growth.value = null
    growthError.value = err?.message || '增长诊断加载失败'
  } finally {
    growthLoading.value = false
  }
}

async function loadStats() {
  if (startDate.value && endDate.value && startDate.value > endDate.value) {
    uni.showToast({ title: '开始日期不能晚于结束日期', icon: 'none' })
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response: any = await request({
      url: '/cal_price/business_stats/overview',
      method: 'GET',
      data: { start_date: startDate.value, end_date: endDate.value }
    })
    if (response?.code !== 200 || !response?.data) throw new Error(response?.message || '接口未返回统计数据')
    stats.value = response.data

    const latestMonth = stats.value.monthly?.[stats.value.monthly.length - 1]?.month
    if (latestMonth && !selectedMonth.value) openGrowth(latestMonth)
  } catch (err: any) {
    error.value = err?.message || '请检查服务状态后重试'
  } finally {
    loading.value = false
  }
}

function resetDates() {
  startDate.value = ''
  endDate.value = ''
  loadStats()
}

onShow(loadStats)
</script>

<style scoped lang="scss">
.dashboard {
  --ink: #17211d;
  --paper: #f3efe5;
  --cream: #fffaf0;
  --coral: #f26b4f;
  --sage: #a8b7a4;
  min-height: 100vh;
  padding: 30rpx;
  color: var(--ink);
  background:
    radial-gradient(circle at 86% 2%, rgba(242, 107, 79, .14), transparent 28%),
    linear-gradient(180deg, #f7f3e9 0%, var(--paper) 100%);
  box-sizing: border-box;
}

.hero { position: relative; display: flex; justify-content: space-between; overflow: hidden; padding: 48rpx 42rpx; border-radius: 8rpx 44rpx 8rpx 8rpx; color: #fffaf0; background: var(--ink); }
.hero::after { content: ''; position: absolute; right: 116rpx; bottom: -110rpx; width: 260rpx; height: 260rpx; border: 2rpx solid rgba(255,255,255,.1); border-radius: 50%; }
.hero-copy { position: relative; z-index: 1; display: flex; flex-direction: column; }
.eyebrow, .section-kicker, .quality-kicker { font-size: 20rpx; letter-spacing: 4rpx; color: var(--coral); }
.hero-title { margin-top: 12rpx; font-family: 'STSong', 'Songti SC', serif; font-size: 64rpx; font-weight: 700; letter-spacing: 4rpx; }
.hero-subtitle { margin-top: 14rpx; font-size: 25rpx; color: rgba(255,255,255,.7); }
.hero-mark { position: relative; z-index: 1; align-self: center; width: 88rpx; height: 88rpx; border: 2rpx solid rgba(255,255,255,.28); border-radius: 50%; font-family: Georgia, serif; font-size: 48rpx; line-height: 88rpx; text-align: center; color: var(--coral); }

.filter-panel { display: flex; align-items: flex-end; gap: 18rpx; margin: 24rpx 0; padding: 24rpx; border: 1rpx solid rgba(23,33,29,.1); background: rgba(255,250,240,.78); }
.date-field { flex: 1; min-width: 0; }
.field-label { display: block; margin-bottom: 8rpx; font-size: 20rpx; color: #748078; }
.date-value { padding: 14rpx 0; border-bottom: 2rpx solid var(--ink); font-size: 25rpx; white-space: nowrap; }
.date-divider { padding-bottom: 14rpx; color: #8b938e; }
.query-button, .reset-button, .retry-button { margin: 0; border-radius: 4rpx; font-size: 24rpx; line-height: 68rpx; }
.query-button { padding: 0 30rpx; color: #fff; background: var(--coral); }
.reset-button { padding: 0 22rpx; color: var(--ink); background: #e7e1d4; }
.query-button::after, .reset-button::after, .retry-button::after { border: 0; }

.period-line { display: flex; justify-content: space-between; margin: 34rpx 4rpx 18rpx; font-size: 22rpx; color: #6e7771; }
.record-count { font-weight: 700; color: var(--ink); }
.metric-grid { display: flex; flex-wrap: wrap; gap: 18rpx; }
.metric-card { width: calc(50% - 9rpx); min-height: 180rpx; padding: 28rpx; border-top: 5rpx solid var(--sage); background: var(--cream); box-sizing: border-box; box-shadow: 0 14rpx 30rpx rgba(37,42,35,.06); }
.metric-primary { border-color: var(--coral); background: #f9dfd5; }
.metric-label, .metric-foot { display: block; font-size: 22rpx; color: #667069; }
.metric-value { display: block; margin: 18rpx 0 14rpx; font-family: Georgia, 'Times New Roman', serif; font-size: 44rpx; font-weight: 700; }

.section { margin-top: 24rpx; padding: 34rpx 28rpx; background: var(--cream); box-shadow: 0 14rpx 34rpx rgba(37,42,35,.05); }
.dark-section { color: #fff; background: var(--ink); }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20rpx; margin-bottom: 30rpx; }
.section-heading > view:first-child { display: flex; flex-direction: column; }
.section-title { margin-top: 8rpx; font-family: 'STSong', 'Songti SC', serif; font-size: 38rpx; font-weight: 700; }
.section-note { font-size: 20rpx; color: #89918c; text-align: right; }
.light-heading .section-note { color: rgba(255,255,255,.5); }

.month-scroll { width: 100%; }
.month-chart { display: flex; align-items: flex-end; min-width: 1150rpx; height: 390rpx; gap: 18rpx; }
.month-column { display: flex; flex: 1; flex-direction: column; align-items: center; min-width: 72rpx; height: 100%; opacity: .76; transition: opacity .2s ease, transform .2s ease; cursor: pointer; }
.month-column:hover, .month-selected { opacity: 1; transform: translateY(-6rpx); }
.month-selected .month-track { outline: 2rpx solid rgba(242,107,79,.7); outline-offset: 6rpx; }
.month-profit { height: 34rpx; font-size: 18rpx; color: rgba(255,255,255,.66); }
.month-track { display: flex; align-items: flex-end; width: 42rpx; height: 240rpx; margin: 8rpx 0 12rpx; background: rgba(255,255,255,.07); }
.month-bar { width: 100%; min-height: 8rpx; background: linear-gradient(180deg, #ff9f7e, var(--coral)); transition: height .45s ease; }
.month-label { font-size: 18rpx; color: #fff; transform: rotate(-28deg); transform-origin: center; white-space: nowrap; }
.month-orders { margin-top: 18rpx; font-size: 17rpx; color: rgba(255,255,255,.45); }
.month-hint { display: block; margin-top: 20rpx; font-size: 19rpx; text-align: right; color: rgba(255,255,255,.48); }

.growth-loading { display: flex; align-items: center; justify-content: center; gap: 16rpx; min-height: 150rpx; margin-top: 24rpx; padding: 30rpx; font-size: 23rpx; color: #68716b; background: var(--cream); }
.growth-error { color: #b44534; }
.growth-retry { margin: 0; padding: 0 24rpx; border: 0; border-radius: 4rpx; font-size: 21rpx; line-height: 56rpx; color: #fff; background: var(--ink); }
.growth-retry::after { border: 0; }
.growth-panel { position: relative; overflow: hidden; margin-top: 24rpx; padding: 38rpx 30rpx; border: 2rpx solid var(--ink); background: #ede7da; box-shadow: 12rpx 12rpx 0 rgba(23,33,29,.12); }
.growth-panel::before { content: ''; position: absolute; top: -110rpx; right: -80rpx; width: 260rpx; height: 260rpx; border: 38rpx solid rgba(242,107,79,.09); border-radius: 50%; }
.growth-header { position: relative; display: flex; align-items: flex-end; justify-content: space-between; gap: 22rpx; }
.growth-header > view:first-child { display: flex; flex-direction: column; }
.growth-kicker, .card-eyebrow { font-size: 19rpx; letter-spacing: 3rpx; color: var(--coral); }
.growth-title { margin-top: 9rpx; font-family: 'STSong', 'Songti SC', serif; font-size: 44rpx; font-weight: 700; }
.compare-badge { padding: 10rpx 18rpx; border: 1rpx solid rgba(23,33,29,.25); font-size: 20rpx; white-space: nowrap; }
.insight-strip { position: relative; display: flex; align-items: center; gap: 20rpx; margin: 28rpx 0; padding: 24rpx 28rpx; color: #fff; background: var(--ink); }
.insight-mark { flex: 0 0 54rpx; width: 54rpx; height: 54rpx; border-radius: 50%; font-family: Georgia, serif; font-size: 34rpx; line-height: 54rpx; text-align: center; color: var(--coral); background: rgba(255,255,255,.08); }
.insight-copy { font-size: 24rpx; line-height: 1.65; }
.growth-metrics { display: flex; flex-wrap: wrap; gap: 14rpx; }
.growth-metric { display: flex; flex: 1 0 28%; flex-direction: column; min-width: 180rpx; padding: 24rpx; border-top: 4rpx solid var(--ink); background: var(--cream); box-sizing: border-box; }
.growth-metric-label { font-size: 20rpx; color: #747d77; }
.growth-metric-value { margin: 13rpx 0 8rpx; font-family: Georgia, serif; font-size: 36rpx; font-weight: 700; }
.growth-metric-rate { font-size: 21rpx; color: #747d77; }
.positive-value { color: #d8583f !important; }
.negative-value { color: #437b70 !important; }
.neutral-value { color: #666f69 !important; }

.bridge-card { margin-top: 22rpx; padding: 28rpx; background: var(--cream); }
.bridge-title-row, .card-title-row { display: flex; align-items: flex-end; justify-content: space-between; gap: 20rpx; }
.bridge-title { font-family: 'STSong', 'Songti SC', serif; font-size: 30rpx; font-weight: 700; }
.bridge-caption, .card-caption { font-size: 18rpx; color: #858c87; text-align: right; }
.bridge-flow { display: flex; align-items: stretch; gap: 10rpx; margin-top: 24rpx; }
.bridge-node { display: flex; flex: 1; flex-direction: column; justify-content: center; min-width: 0; padding: 20rpx 14rpx; text-align: center; background: #e9e2d5; }
.effect-node { border-bottom: 5rpx solid var(--coral); }
.current-node { color: #fff; background: var(--ink); }
.bridge-node-label, .bridge-node-foot { font-size: 17rpx; color: #777f79; }
.current-node .bridge-node-label { color: rgba(255,255,255,.6); }
.bridge-node-value { margin: 9rpx 0 5rpx; font-family: Georgia, serif; font-size: 27rpx; font-weight: 700; white-space: nowrap; }
.bridge-arrow, .bridge-plus { align-self: center; font-size: 24rpx; color: #87908a; }

.diagnosis-grid { display: flex; flex-direction: column; gap: 20rpx; margin-top: 22rpx; }
.contribution-card, .customer-change-card { padding: 28rpx; background: var(--cream); }
.card-title-row > view:first-child { display: flex; flex-direction: column; }
.card-title { margin-top: 7rpx; font-family: 'STSong', 'Songti SC', serif; font-size: 30rpx; font-weight: 700; }
.detail-link { padding: 10rpx 14rpx; border-bottom: 2rpx solid var(--coral); font-size: 20rpx; font-weight: 700; color: #cf5039; cursor: pointer; }
.dimension-tabs { width: 100%; margin: 24rpx 0 10rpx; white-space: nowrap; }
.dimension-tabs-inner { display: flex; gap: 10rpx; }
.dimension-tab { padding: 12rpx 24rpx; border: 1rpx solid #cfc7b8; font-size: 21rpx; color: #6d756f; background: #f2ede4; cursor: pointer; }
.dimension-tab.active { border-color: var(--ink); color: #fff; background: var(--ink); }
.contribution-row { padding: 19rpx 10rpx; border-top: 1rpx solid #ded7ca; transition: background .18s ease, transform .18s ease; cursor: pointer; }
.contribution-row:hover, .contribution-row-active { background: #f5ecdf; transform: translateX(5rpx); }
.contribution-topline { display: flex; align-items: center; gap: 13rpx; }
.contribution-rank { width: 42rpx; font-family: Georgia, serif; font-size: 19rpx; color: #a29b90; }
.contribution-name { overflow: hidden; flex: 1; font-size: 23rpx; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.contribution-delta { font-family: Georgia, serif; font-size: 23rpx; font-weight: 700; }
.contribution-open { width: 28rpx; font-family: Georgia, serif; font-size: 32rpx; line-height: 1; text-align: right; color: #a29a8e; }
.delta-track { overflow: hidden; height: 8rpx; margin: 12rpx 0 9rpx 55rpx; background: #e6dfd2; }
.delta-fill { height: 100%; }
.positive-fill { background: var(--coral); }
.negative-fill { background: #5f8d82; }
.contribution-foot { margin-left: 55rpx; font-size: 18rpx; color: #858c87; }
.segment-row { display: flex; align-items: center; gap: 18rpx; padding: 23rpx 0; border-top: 1rpx solid #ded7ca; }
.segment-list { margin-top: 22rpx; }
.segment-symbol { flex: 0 0 58rpx; width: 58rpx; height: 58rpx; border-radius: 50%; font-family: Georgia, serif; font-size: 30rpx; line-height: 58rpx; text-align: center; background: #e7e0d3; }
.segment-new { color: #fff; background: var(--coral); }
.segment-retained { color: #fff; background: var(--ink); }
.segment-reactivated { color: var(--ink); background: #bdc9b9; }
.segment-lost { color: #fff; background: #6f8881; }
.segment-main { flex: 1; min-width: 0; }
.segment-title-line { display: flex; justify-content: space-between; gap: 12rpx; }
.segment-title { font-size: 24rpx; font-weight: 700; }
.segment-count { font-size: 20rpx; color: #767e78; }
.segment-description { display: block; margin-top: 6rpx; font-size: 18rpx; color: #858c87; }
.segment-profit { font-family: Georgia, serif; font-size: 23rpx; font-weight: 700; }
.diagnosis-boundary { display: block; margin-top: 22rpx; padding-top: 18rpx; border-top: 1rpx dashed rgba(23,33,29,.25); font-size: 18rpx; line-height: 1.6; color: #737b75; }

.rank-row { display: flex; gap: 20rpx; padding: 22rpx 0; border-top: 1rpx solid rgba(23,33,29,.1); }
.rank-number { width: 50rpx; font-family: Georgia, serif; font-size: 24rpx; color: var(--coral); }
.rank-main { flex: 1; min-width: 0; }
.rank-line, .rank-meta, .distribution-labels { display: flex; justify-content: space-between; gap: 12rpx; }
.rank-name { overflow: hidden; flex: 1; font-size: 27rpx; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.rank-value { font-family: Georgia, serif; font-size: 26rpx; font-weight: 700; }
.bar-track { overflow: hidden; height: 7rpx; margin: 15rpx 0 12rpx; background: #e8e1d4; }
.bar-fill { height: 100%; transition: width .45s ease; }
.coral { background: var(--coral); }
.ink { background: var(--ink); }
.rank-meta { justify-content: flex-start; gap: 28rpx; font-size: 20rpx; color: #7c847f; }

.distribution-row { margin-bottom: 26rpx; }
.distribution-labels { font-size: 24rpx; font-weight: 700; }
.soft-track { height: 12rpx; margin: 10rpx 0; background: #e7e1d4; }
.distribution-detail { font-size: 20rpx; color: #7c847f; }
.loyalty-grid { display: flex; flex-wrap: wrap; gap: 14rpx; }
.loyalty-card { display: flex; flex: 1 0 28%; flex-direction: column; min-width: 150rpx; padding: 22rpx; border-left: 4rpx solid var(--coral); background: #eee8dc; box-sizing: border-box; }
.loyalty-frequency { font-size: 22rpx; color: #6d756f; }
.loyalty-count { margin: 10rpx 0; font-family: Georgia, serif; font-size: 42rpx; font-weight: 700; }
.loyalty-percent { font-size: 19rpx; color: #838a85; }

.table-scroll { width: 100%; }
.data-table { min-width: 1150rpx; }
.table-row { display: flex; align-items: center; min-height: 76rpx; border-top: 1rpx solid #ded8cc; }
.table-head { min-height: 60rpx; color: #79817c; background: #eee8dc; }
.cell { width: 170rpx; padding: 0 14rpx; font-size: 22rpx; box-sizing: border-box; }
.cell-name { width: 240rpx; font-weight: 700; }
.cell-customer { width: 300rpx; font-weight: 700; }
.customer-table { min-width: 1210rpx; }
.profit-cell { font-weight: 700; color: #cf4d37; }

.quality-card { display: flex; align-items: center; justify-content: space-between; gap: 30rpx; margin: 24rpx 0 20rpx; padding: 36rpx; color: #fff; background: var(--ink); }
.quality-card > view:first-child { flex: 1; }
.quality-title { display: block; margin: 12rpx 0; font-family: 'STSong', 'Songti SC', serif; font-size: 34rpx; font-weight: 700; }
.quality-copy { display: block; font-size: 21rpx; line-height: 1.7; color: rgba(255,255,255,.62); }
.quality-ring { display: flex; flex: 0 0 128rpx; align-items: center; justify-content: center; width: 128rpx; height: 128rpx; border-radius: 50%; }
.quality-ring-inner { width: 94rpx; height: 94rpx; border-radius: 50%; font-family: Georgia, serif; font-size: 27rpx; font-weight: 700; line-height: 94rpx; text-align: center; background: var(--ink); }

.state-card { display: flex; align-items: center; justify-content: center; gap: 18rpx; min-height: 280rpx; margin-top: 24rpx; padding: 40rpx; background: var(--cream); color: #68716b; }
.pulse-dot { width: 20rpx; height: 20rpx; border-radius: 50%; background: var(--coral); animation: pulse 1s infinite alternate; }
.error-card { flex-direction: column; }
.state-title { font-size: 32rpx; font-weight: 700; color: var(--ink); }
.state-copy { font-size: 22rpx; }
.retry-button { margin-top: 16rpx; padding: 0 30rpx; color: #fff; background: var(--ink); }

@keyframes pulse { to { opacity: .3; transform: scale(.72); } }

@media (min-width: 960px) {
  .dashboard { padding: 42px max(42px, calc((100vw - 1240px) / 2)); }
  .metric-card { width: calc(25% - 14px); }
  .split-layout { display: flex; gap: 24rpx; }
  .split-section { width: calc(50% - 12rpx); box-sizing: border-box; }
  .diagnosis-grid { flex-direction: row; }
  .contribution-card { width: calc(58% - 10rpx); box-sizing: border-box; }
  .customer-change-card { width: calc(42% - 10rpx); box-sizing: border-box; }
}
</style>
