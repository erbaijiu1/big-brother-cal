<template>
  <view class="detail-page">
    <view v-if="loading && !data" class="state">正在拆解品类证据…</view>
    <view v-else-if="error && !data" class="state error">{{ error }}<button @click="loadData">重试</button></view>
    <template v-else-if="data">
      <view class="masthead">
        <text class="eyebrow">CATEGORY EVIDENCE / 02</text>
        <view class="title-row"><text class="title">{{ data.category }}</text><text class="status" :class="statusClass(data.metric.candidate_status)">{{ data.metric.candidate_status }}</text></view>
        <text class="lead">{{ data.metric.candidate_reasons.join('；') }}</text>
      </view>

      <view class="metric-grid">
        <view class="metric hero-metric"><text>首单平均毛利润</text><strong>{{ money(data.metric.avg_database_first_order_profit) }}</strong><small>历史首次客户 · 利润覆盖 {{ percent(data.metric.database_first_profit_coverage_pct) }}</small></view>
        <view class="metric"><text>历史首次客户</text><strong>{{ integer(data.metric.database_first_customer_count) }}</strong><small>完整数据库第一次出现</small></view>
        <view class="metric"><text>品类首次客户</text><strong>{{ integer(data.metric.category_first_customer_count) }}</strong><small>第一次发该品类，可曾发过别类</small></view>
        <view class="metric"><text>品类毛利润</text><strong>{{ money(data.metric.total_profit) }}</strong><small>毛利率 {{ percent(data.metric.profit_rate_pct) }} · 覆盖 {{ percent(data.metric.profit_order_coverage_pct) }}</small></view>
      </view>

      <view class="section cohort-section">
        <view class="section-head"><view><text class="eyebrow">01 / RETENTION</text><text class="section-title">成熟观察期复购</text></view><text class="note">按去重客户，不按订单数</text></view>
        <view class="cohort-grid">
          <view v-for="cohort in [data.metric.cohort_30, data.metric.cohort_90]" :key="cohort.days" class="cohort-card">
            <view class="cohort-top"><strong>{{ cohort.days }}天</strong><text>{{ cohort.sample_sufficient ? '样本可读' : '小样本' }}</text></view>
            <view class="funnel"><view><strong>{{ cohort.mature_customers }}</strong><text>观察期完整客户</text></view><text class="arrow">→</text><view><strong>{{ cohort.repurchased_customers }}</strong><text>发生任意复购</text></view></view>
            <view class="rate-bar"><view :style="{ width: `${Math.min(cohort.repurchase_rate_pct || 0, 100)}%` }"></view></view>
            <view class="cohort-foot"><text>任意品类 {{ percent(cohort.repurchase_rate_pct) }}</text><text>同品类 {{ percent(cohort.same_category_repurchase_rate_pct) }}</text></view>
            <text class="coverage">窗口利润覆盖 {{ percent(cohort.profit_order_coverage_pct) }}</text>
          </view>
        </view>
        <text class="footnote">同日多票按“发货日期 → 公司单号 → 记录 ID”稳定排序；首票之后的同日订单可计作复购。</text>
      </view>

      <view class="section contribution-section">
        <view class="section-head"><view><text class="eyebrow">02 / SALESMAN</text><text class="section-title">业务员贡献分析</text></view><text class="note">订单归属业务员，不代表实际获客人</text></view>
        <view class="concentration-strip three">
          <view><text>业务员总数</text><strong>{{ integer(data.salesman_contribution.summary.salesman_count) }}</strong><small>未识别 {{ integer(data.salesman_contribution.summary.unknown_order_count) }} 票</small></view>
          <view><text>TOP1 毛利集中度</text><strong>{{ percent(data.salesman_contribution.summary.top1_profit_concentration_pct) }}</strong><small>可识别净毛利分母</small></view>
          <view><text>TOP3 毛利集中度</text><strong>{{ percent(data.salesman_contribution.summary.top3_profit_concentration_pct) }}</strong><small>{{ money(data.salesman_contribution.summary.profit_denominator) }}</small></view>
        </view>
        <view class="table-toolbar"><text>排序</text><text v-for="option in salesmanSortOptions" :key="`salesman-${option.key}`" class="sort-chip" :class="{ active: salesmanSort.key === option.key }" @click="setSort('salesman', option.key)">{{ option.label }} {{ sortMark(salesmanSort, option.key) }}</text></view>
        <scroll-view scroll-x class="contribution-scroll">
          <view class="contribution-table salesman-table">
            <view class="contribution-row table-header"><text>业务员</text><text>订单数</text><text>去重客户</text><text>历史首客</text><text>销售额</text><text>毛利润</text><text>贡献占比</text><text>核对</text></view>
            <view v-for="item in visibleSalespeople" :key="item.key" class="contribution-row" :class="{ selected: selectedSalesman === item.key, unknown: item.key === unknownKey }" @click="filterBySalesman(item)">
              <view class="entity-cell"><strong>{{ item.name }}</strong><small>点击筛选关联客户</small></view>
              <text>{{ integer(item.order_count) }}</text><text>{{ integer(item.customer_count) }}</text><text>{{ integer(item.database_first_customer_count) }}</text><text class="revenue-value">{{ money(item.total_revenue) }}</text><text :class="profitClass(item.total_profit)">{{ money(item.total_profit) }}</text><text>{{ percent(item.profit_contribution_pct) }}</text>
              <text class="detail-link" @click.stop="openOrders('业务员订单明细', item.key, '')">订单</text>
            </view>
          </view>
        </scroll-view>
        <view v-if="data.salesman_contribution.items.length > 10" class="expand-line" @click="salesmanExpanded = !salesmanExpanded">{{ salesmanExpanded ? '收起到 TOP10' : `展开全部 ${data.salesman_contribution.items.length} 位` }}</view>
      </view>

      <view class="section contribution-section customer-section">
        <view class="section-head">
          <view><text class="eyebrow">03 / CUSTOMER</text><text class="section-title">客户贡献分析</text></view>
          <view class="customer-scope"><text v-if="data.customer_contribution.summary.salesman_filter_name">当前业务员：{{ data.customer_contribution.summary.salesman_filter_name }}</text><text v-if="selectedSalesman" class="clear-filter" @click="clearSalesmanFilter">查看全部客户 ×</text></view>
        </view>
        <view class="concentration-strip four">
          <view><text>客户总数</text><strong>{{ integer(data.customer_contribution.summary.customer_count) }}</strong><small>未识别 {{ integer(data.customer_contribution.summary.unknown_order_count) }} 票</small></view>
          <view><text>TOP1 集中度</text><strong>{{ percent(data.customer_contribution.summary.top1_profit_concentration_pct) }}</strong><small>可识别净毛利分母</small></view>
          <view><text>TOP5 集中度</text><strong>{{ percent(data.customer_contribution.summary.top5_profit_concentration_pct) }}</strong><small>{{ money(data.customer_contribution.summary.profit_denominator) }}</small></view>
          <view class="remainder"><text>剔除最大客户</text><strong>{{ money(data.customer_contribution.summary.profit_excluding_largest_customer) }}</strong><small>剩余可识别毛利润</small></view>
        </view>
        <view class="table-toolbar"><text>排序</text><text v-for="option in sortOptions" :key="`customer-${option.key}`" class="sort-chip" :class="{ active: customerSort.key === option.key }" @click="setSort('customer', option.key)">{{ option.label }} {{ sortMark(customerSort, option.key) }}</text></view>
        <scroll-view scroll-x class="contribution-scroll">
          <view class="contribution-table customer-table">
            <view class="contribution-row table-header"><text>客户</text><text>订单数</text><text>毛利润</text><text>贡献占比</text><text>历史首次发货</text><text>最后发货</text><text>历史首客</text><text>核对</text></view>
            <view v-for="item in visibleCustomers" :key="item.key" class="contribution-row" :class="{ unknown: item.key === unknownKey }">
              <view class="entity-cell"><strong>{{ item.name }}</strong><small>{{ item.profit_covered_order_count }}/{{ item.order_count }} 票有成本</small></view>
              <text>{{ integer(item.order_count) }}</text><text :class="profitClass(item.total_profit)">{{ money(item.total_profit) }}</text><text>{{ percent(item.profit_contribution_pct) }}</text><text>{{ item.first_shipping_date || '--' }}</text><text>{{ item.last_shipping_date || '--' }}</text>
              <text><text class="first-badge" :class="{ yes: item.is_database_first_customer }">{{ item.is_database_first_customer ? '是' : '否' }}</text></text>
              <text class="detail-link" @click="openOrders('客户订单明细', selectedSalesman, item.key)">订单</text>
            </view>
          </view>
        </scroll-view>
        <view v-if="data.customer_contribution.items.length > 10" class="expand-line" @click="customerExpanded = !customerExpanded">{{ customerExpanded ? '收起到 TOP10' : `展开全部 ${data.customer_contribution.items.length} 位` }}</view>
      </view>

      <view class="judgement-panel">
        <view class="judgement-title"><text class="eyebrow">STRUCTURE NOTE</text><strong>经营判断</strong></view>
        <view class="judgement-copy"><text v-for="(insight, index) in data.business_insights" :key="insight"><i>{{ String(index + 1).padStart(2, '0') }}</i>{{ insight }}</text></view>
        <text class="denominator-note">{{ data.contribution_note }}</text>
      </view>

      <view class="section">
        <view class="section-head"><view><text class="eyebrow">04 / TREND</text><text class="section-title">月度获客与利润</text></view><view class="salesman-dimension"><text>业务员维度</text><picker :range="salesmanOptions" range-key="name" :value="selectedSalesmanIndex" @change="changeSalesman"><view class="salesman-picker"><strong>{{ selectedSalesmanLabel }}</strong><text>⌄</text></view></picker><small>同时筛选月度与渠道</small></view></view>
        <view v-if="data.monthly.length" class="trend-list"><view v-for="month in data.monthly" :key="month.month" class="trend-row"><text class="month">{{ month.month }}</text><view class="bar-track"><view class="bar" :style="{ width: trendWidth(month.total_profit) }"></view></view><text>{{ money(month.total_profit) }}</text><text>历史首客 {{ month.database_first_customer_count }}</text><text>品类首客 {{ month.category_first_customer_count }}</text></view></view>
        <view v-else class="empty">{{ selectedSalesman ? `${selectedSalesmanLabel}在当前区间没有月度数据` : '当前区间没有月度数据' }}</view>
      </view>

      <view class="split-grid">
        <view class="section split-section"><view class="section-head"><view><text class="eyebrow">05 / CHANNEL</text><text class="section-title">渠道贡献</text></view><text class="note">{{ selectedSalesman ? `${selectedSalesmanLabel} · 渠道销售占比` : '按销售额排序 · 占当前品类总销售额' }}</text></view><view v-for="channel in data.channels" :key="channel.name" class="rank-row channel-row"><view class="channel-main"><strong>{{ channel.name }}</strong><small>{{ channel.order_count }}票 · 销售占比 {{ percent(channel.revenue_contribution_pct) }} · 毛利率 {{ percent(channel.profit_rate_pct) }}</small><view class="channel-share-track"><view class="channel-share-fill" :style="{ width: shareWidth(channel.revenue_contribution_pct) }"></view></view></view><view class="channel-values"><strong>{{ money(channel.revenue) }}</strong><small>销售额</small><text :class="profitClass(channel.total_profit)">毛利 {{ money(channel.total_profit) }}</text></view></view><view v-if="!data.channels.length" class="empty">{{ selectedSalesmanLabel }}没有渠道数据</view></view>
        <view class="section split-section"><view class="section-head"><view><text class="eyebrow">06 / SOURCE</text><text class="section-title">原始品名</text></view></view><view v-for="(item, index) in data.raw_product_names" :key="item.name" class="rank-row raw-row"><text class="rank">{{ String(index + 1).padStart(2, '0') }}</text><strong>{{ item.name }}</strong><text>{{ item.order_count }}票</text></view></view>
      </view>

      <view class="audit-note"><strong>口径提醒</strong><text>利润 = shipping_fee - shipping_cost；缺成本票不按零计算。客户只通过 company_tracking_no ↔ order_no 精确关联。历史从 2025 年初开始，首次客户存在左截断风险。</text></view>
    </template>

    <view v-if="showOrders" class="drawer-mask" @click="showOrders = false">
      <view class="order-drawer" @click.stop>
        <view class="drawer-head"><view><text class="eyebrow">ORDER EVIDENCE</text><text class="drawer-title">{{ orderTitle }}</text><text class="drawer-sub">共 {{ integer(orderResult.total) }} 票 · 当前最多展示 200 票</text></view><text class="close" @click="showOrders = false">×</text></view>
        <view v-if="orderLoading" class="order-loading">正在读取订单证据…</view>
        <view v-else class="order-list"><view v-for="item in orderResult.items" :key="item.id" class="order-row"><view class="order-main"><strong>{{ item.company_tracking_no || `记录 ${item.id}` }}</strong><text>{{ item.shipping_date }}</text></view><view class="order-tags"><text>{{ item.salesman || '未识别业务员' }}</text><text>{{ item.shipping_channel || '未知渠道' }}</text><text>{{ item.category }}</text></view><view class="order-money"><text>收入 {{ money(item.shipping_fee) }}</text><text>成本 {{ money(item.shipping_cost) }}</text><strong :class="profitClass(item.gross_profit)">毛利 {{ money(item.gross_profit) }}</strong></view><text class="order-customer">{{ item.shipping_customer || '未识别客户' }}</text></view><view v-if="!orderResult.items.length" class="empty">没有对应订单</view></view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request'

const unknownKey = '__UNKNOWN__'
const sortOptions = [{ key: 'order_count', label: '订单数' }, { key: 'total_profit', label: '毛利润' }, { key: 'profit_contribution_pct', label: '贡献占比' }]
const salesmanSortOptions = [{ key: 'order_count', label: '订单数' }, { key: 'total_revenue', label: '销售额' }, { key: 'total_profit', label: '毛利润' }, { key: 'profit_contribution_pct', label: '贡献占比' }]
const data = ref<any>(null)
const loading = ref(false)
const error = ref('')
const params = ref({ category: '', start_date: '', end_date: '' })
const salesmanExpanded = ref(false)
const customerExpanded = ref(false)
const selectedSalesman = ref('')
const salesmanSort = ref({ key: 'total_profit', direction: 'desc' })
const customerSort = ref({ key: 'total_profit', direction: 'desc' })
const showOrders = ref(false)
const orderLoading = ref(false)
const orderTitle = ref('订单明细')
const orderResult = ref<any>({ total: 0, items: [] })

const maxTrendProfit = computed(() => Math.max(...(data.value?.monthly || []).map((item: any) => Math.max(Number(item.total_profit) || 0, 0)), 1))
const sortedSalespeople = computed(() => sortItems(data.value?.salesman_contribution?.items || [], salesmanSort.value))
const sortedCustomers = computed(() => sortItems(data.value?.customer_contribution?.items || [], customerSort.value))
const visibleSalespeople = computed(() => salesmanExpanded.value ? sortedSalespeople.value : sortedSalespeople.value.slice(0, 10))
const visibleCustomers = computed(() => customerExpanded.value ? sortedCustomers.value : sortedCustomers.value.slice(0, 10))
const salesmanOptions = computed(() => [{ key: '', name: '全部业务员' }, ...(data.value?.salesman_contribution?.items || []).map((item: any) => ({ key: item.key, name: item.name }))])
const selectedSalesmanIndex = computed(() => Math.max(0, salesmanOptions.value.findIndex((item: any) => item.key === selectedSalesman.value)))
const selectedSalesmanLabel = computed(() => salesmanOptions.value[selectedSalesmanIndex.value]?.name || '全部业务员')

function money(value: any) { return value === null || value === undefined ? '--' : `¥${Math.round(Number(value)).toLocaleString()}` }
function integer(value: any) { return Math.round(Number(value) || 0).toLocaleString() }
function percent(value: any) { return value === null || value === undefined ? '--' : `${Number(value).toFixed(1)}%` }
function statusClass(status: string) { return status === '值得测试' ? 'test' : status === '暂不建议投放' ? 'stop' : 'watch' }
function trendWidth(value: any) { return `${Math.max(3, Math.max(Number(value) || 0, 0) / maxTrendProfit.value * 100)}%` }
function shareWidth(value: any) { return `${Math.min(Math.max(Number(value) || 0, 0), 100)}%` }
function profitClass(value: any) { return Number(value) < 0 ? 'negative' : 'positive' }
function sortItems(items: any[], state: any) { const direction = state.direction === 'asc' ? 1 : -1; return [...items].sort((left, right) => { const l = left[state.key] ?? Number.NEGATIVE_INFINITY; const r = right[state.key] ?? Number.NEGATIVE_INFINITY; return (Number(l) - Number(r)) * direction }) }
function setSort(target: 'salesman' | 'customer', key: string) { const state = target === 'salesman' ? salesmanSort : customerSort; state.value = { key, direction: state.value.key === key && state.value.direction === 'desc' ? 'asc' : 'desc' } }
function sortMark(state: any, key: string) { return state.key !== key ? '' : state.direction === 'desc' ? '↓' : '↑' }

async function filterBySalesman(item: any) { selectedSalesman.value = selectedSalesman.value === item.key ? '' : item.key; customerExpanded.value = false; await loadData() }
async function clearSalesmanFilter() { selectedSalesman.value = ''; customerExpanded.value = false; await loadData() }
async function changeSalesman(event: any) { selectedSalesman.value = salesmanOptions.value[Number(event.detail.value)]?.key || ''; customerExpanded.value = false; await loadData() }

async function openOrders(title: string, salesman = '', customer = '') {
  showOrders.value = true
  orderLoading.value = true
  orderTitle.value = title
  try {
    const response: any = await request({ url: '/cal_price/acquisition/orders', method: 'GET', data: { scope: 'all', category: params.value.category, start_date: params.value.start_date, end_date: params.value.end_date, salesman, customer, page: 1, page_size: 200 } })
    orderResult.value = response?.data || { total: 0, items: [] }
  } catch (err: any) {
    orderResult.value = { total: 0, items: [] }
    uni.showToast({ title: err?.message || '订单明细加载失败', icon: 'none' })
  } finally { orderLoading.value = false }
}

async function loadData() {
  if (!params.value.category) return
  loading.value = true
  error.value = ''
  try {
    const response: any = await request({ url: `/cal_price/acquisition/categories/${encodeURIComponent(params.value.category)}`, method: 'GET', data: { ...params.value, salesman: selectedSalesman.value } })
    if (response?.code !== 200 || !response?.data) throw new Error(response?.message || '品类详情加载失败')
    data.value = response.data
  } catch (err: any) {
    error.value = err?.message || '品类详情加载失败'
    uni.showToast({ title: error.value, icon: 'none' })
  } finally { loading.value = false }
}

onLoad((options: any) => { params.value = { category: decodeURIComponent(options?.category || ''), start_date: options?.start_date || '', end_date: options?.end_date || '' }; loadData() })
</script>

<style scoped lang="scss">
.detail-page{--ink:#15231c;--paper:#f2ecdf;--cream:#fffaf0;--coral:#ed6547;--lime:#c9dd74;min-height:100vh;padding:30rpx;color:var(--ink);background:radial-gradient(circle at 90% 5%,rgba(201,221,116,.22),transparent 24%),var(--paper);box-sizing:border-box}.state{display:flex;justify-content:center;gap:20rpx;margin-top:80rpx;padding:60rpx;background:var(--cream)}.state button{margin:0}.error{color:#a44}.masthead{padding:46rpx 40rpx;color:#fff;background:var(--ink);border-radius:4rpx 50rpx 4rpx 4rpx}.eyebrow{display:block;color:var(--coral);font-size:18rpx;letter-spacing:4rpx}.title-row{display:flex;align-items:center;gap:22rpx;margin-top:10rpx}.title{font-family:'Songti SC','STSong',serif;font-size:62rpx;font-weight:700}.status{padding:8rpx 15rpx;font-size:19rpx}.status.test{color:#e8f5b6;background:#426248}.status.watch{color:#fff0cd;background:#986b2c}.status.stop{color:#ffe0da;background:#914f43}.lead{display:block;margin-top:15rpx;color:rgba(255,255,255,.65);font-size:22rpx;line-height:1.6}.metric-grid{display:flex;flex-wrap:wrap;gap:16rpx;margin-top:20rpx}.metric{width:calc(50% - 8rpx);padding:25rpx;background:var(--cream);border-top:5rpx solid #a5b0a7;box-sizing:border-box}.hero-metric{background:#f7ddd5;border-color:var(--coral)}.metric text,.metric small{display:block;color:#68716b;font-size:19rpx}.metric strong{display:block;margin:16rpx 0 12rpx;font-family:Georgia,serif;font-size:38rpx}.section{margin-top:22rpx;padding:30rpx 27rpx;background:var(--cream);box-shadow:0 12rpx 30rpx rgba(30,40,34,.05)}.section-head{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:22rpx}.section-title{display:block;margin-top:7rpx;font-family:'Songti SC','STSong',serif;font-size:34rpx;font-weight:700}.note{max-width:48%;color:#858c87;font-size:18rpx;text-align:right}.cohort-grid{display:grid;grid-template-columns:1fr 1fr;gap:18rpx}.cohort-card{padding:23rpx;background:#eee8dc}.cohort-top,.cohort-foot,.funnel{display:flex;justify-content:space-between;align-items:center}.cohort-top strong{font-family:Georgia,serif;font-size:29rpx}.cohort-top text{color:#856b37;font-size:18rpx}.funnel{margin:25rpx 0}.funnel view{display:flex;flex-direction:column}.funnel strong{font-family:Georgia,serif;font-size:35rpx}.funnel text{color:#747b76;font-size:17rpx}.arrow{color:#a7aaa1}.rate-bar{height:8rpx;background:#d5cec1}.rate-bar view{height:100%;background:var(--coral)}.cohort-foot{margin-top:13rpx;font-size:18rpx}.coverage{display:block;margin-top:12rpx;color:#788078;font-size:17rpx}.footnote{display:block;margin-top:18rpx;color:#7b827d;font-size:18rpx}.concentration-strip{display:grid;gap:1rpx;margin-bottom:22rpx;background:#d7d0c3;border:1rpx solid #d7d0c3}.concentration-strip.three{grid-template-columns:repeat(3,1fr)}.concentration-strip.four{grid-template-columns:repeat(4,1fr)}.concentration-strip>view{min-height:125rpx;padding:20rpx;background:#eee8dc;box-sizing:border-box}.concentration-strip text,.concentration-strip small{display:block;color:#747b76;font-size:17rpx}.concentration-strip strong{display:block;margin:10rpx 0 7rpx;font-family:Georgia,serif;font-size:30rpx}.concentration-strip .remainder{background:#f6ddd4}.table-toolbar{display:flex;align-items:center;gap:10rpx;margin-bottom:13rpx;color:#7a817c;font-size:18rpx}.sort-chip{padding:8rpx 14rpx;background:#ece5d8}.sort-chip.active{color:#fff;background:var(--ink)}.contribution-scroll{width:100%}.contribution-table{border-top:2rpx solid var(--ink)}.salesman-table{min-width:1350rpx}.customer-table{min-width:1510rpx}.contribution-row{display:grid;align-items:center;min-height:76rpx;border-bottom:1rpx solid #ddd6c9;font-size:19rpx}.salesman-table .contribution-row{grid-template-columns:240rpx 115rpx 125rpx 130rpx 170rpx 170rpx 140rpx 100rpx}.customer-table .contribution-row{grid-template-columns:260rpx 110rpx 160rpx 135rpx 170rpx 170rpx 120rpx 95rpx}.contribution-row>*{padding:0 12rpx;box-sizing:border-box}.table-header{min-height:62rpx;color:#727a75;background:#ece7dc;font-weight:700}.contribution-row:not(.table-header){cursor:pointer}.contribution-row:not(.table-header):hover,.contribution-row.selected{background:#f4ead1}.contribution-row.unknown{background:rgba(230,173,84,.11)}.entity-cell{display:flex;flex-direction:column}.entity-cell strong{font-size:21rpx}.entity-cell small{margin-top:5rpx;color:#92958c;font-size:15rpx}.revenue-value{font-family:Georgia,serif;color:#24352c}.detail-link{color:var(--coral);font-weight:700}.positive{color:#416c48}.negative{color:#b34d40!important}.first-badge{display:inline-block;padding:5rpx 10rpx;color:#777;background:#e5dfd4}.first-badge.yes{color:#355d3c;background:#dce8c2}.expand-line{margin-top:16rpx;padding:13rpx;color:#5a685f;background:#eee8dc;text-align:center;font-size:19rpx}.customer-scope{display:flex;align-items:flex-end;gap:14rpx;color:#7d847f;font-size:18rpx}.clear-filter{color:var(--coral);font-weight:700}.judgement-panel{display:grid;grid-template-columns:220rpx 1fr;gap:24rpx;margin-top:22rpx;padding:31rpx;color:#fff;background:var(--ink)}.judgement-title strong{display:block;margin-top:10rpx;font-family:'Songti SC','STSong',serif;font-size:35rpx}.judgement-copy{display:grid;gap:12rpx}.judgement-copy text{display:flex;color:rgba(255,255,255,.78);font-size:20rpx;line-height:1.55}.judgement-copy i{margin-right:14rpx;color:var(--lime);font-family:Georgia,serif;font-style:normal}.denominator-note{grid-column:2;color:rgba(255,255,255,.48);font-size:17rpx;line-height:1.55}.trend-row{display:grid;grid-template-columns:120rpx minmax(120rpx,1fr) 150rpx 140rpx 140rpx;gap:12rpx;align-items:center;min-width:760rpx;padding:14rpx 0;border-bottom:1rpx solid #dfd8cc;font-size:18rpx}.month{font-family:Georgia,serif;font-weight:700}.bar-track{height:12rpx;background:#e3ddd1}.bar{height:100%;background:var(--coral)}.split-grid{display:grid;grid-template-columns:1fr 1fr;gap:22rpx}.split-section{min-width:0}.rank-row{display:flex;justify-content:space-between;gap:12rpx;align-items:center;padding:17rpx 0;border-bottom:1rpx solid #ddd6ca}.rank-row view{display:flex;flex-direction:column}.rank-row small{margin-top:5rpx;color:#7c837e;font-size:17rpx}.rank-row>text{font-family:Georgia,serif;font-size:20rpx}.raw-row{justify-content:flex-start}.raw-row strong{flex:1}.rank{color:var(--coral)!important}.audit-note{display:flex;gap:18rpx;margin-top:22rpx;padding:23rpx;color:#585c55;background:#e8deca;font-size:19rpx;line-height:1.6}.audit-note strong{flex:none;color:var(--ink)}.empty{padding:40rpx;color:#888;text-align:center}.drawer-mask{position:fixed;z-index:30;inset:0;background:rgba(10,18,14,.48)}.order-drawer{position:absolute;top:0;right:0;bottom:0;width:86%;max-width:900rpx;padding:36rpx;overflow-y:auto;background:#f9f3e7;box-sizing:border-box;box-shadow:-20rpx 0 50rpx rgba(0,0,0,.18)}.drawer-head{display:flex;justify-content:space-between;align-items:flex-start}.drawer-head>view{display:flex;flex-direction:column}.drawer-title{margin-top:10rpx;font-family:'Songti SC','STSong',serif;font-size:38rpx;font-weight:700}.drawer-sub{display:block;margin-top:12rpx;color:#7c847f;font-size:19rpx}.close{font-size:48rpx;line-height:1}.order-loading{padding:70rpx 0;color:#777;text-align:center}.order-list{margin-top:22rpx}.order-row{padding:20rpx 0;border-bottom:1rpx solid #d9d1c3}.order-main,.order-money{display:flex;justify-content:space-between;gap:12rpx}.order-main strong{font-family:Georgia,serif}.order-main text,.order-customer{color:#737c76;font-size:18rpx}.order-tags{display:flex;flex-wrap:wrap;gap:8rpx;margin:12rpx 0}.order-tags text{padding:5rpx 9rpx;background:#e9e1d4;font-size:17rpx}.order-money{font-size:18rpx}.order-money strong{color:#47724c}.order-customer{display:block;margin-top:9rpx}@media(min-width:900px){.detail-page{padding:42px 6vw}.metric{width:calc(25% - 12rpx)}.masthead{padding:52px}.section{padding:34px}.cohort-grid{gap:24px}.order-drawer{width:680px}}@media(max-width:620px){.cohort-grid,.split-grid{grid-template-columns:1fr}.section-head{align-items:flex-start;gap:12rpx;flex-direction:column}.note{max-width:none;text-align:left}.trend-list{overflow-x:auto}.concentration-strip.three,.concentration-strip.four{grid-template-columns:1fr 1fr}.judgement-panel{grid-template-columns:1fr}.denominator-note{grid-column:1}.customer-scope{align-items:flex-start;flex-direction:column}.order-drawer{width:94%;padding:28rpx}}
.channel-row{align-items:center}.channel-main{flex:1;min-width:0}.channel-share-track{overflow:hidden;width:100%;height:5rpx;margin-top:12rpx;background:#e7e0d4}.channel-share-fill{height:100%;background:var(--coral);transition:width .35s ease}.channel-values{align-items:flex-end;min-width:190rpx;text-align:right}.channel-values>strong{font-family:Georgia,serif;font-size:22rpx}.channel-values>small{margin-top:2rpx;color:#8a8f89;font-size:15rpx}.channel-values>text{margin-top:8rpx;font-size:17rpx}
.salesman-dimension{display:flex;align-items:flex-end;gap:10rpx;flex-wrap:wrap;justify-content:flex-end}.salesman-dimension>text,.salesman-dimension>small{color:#858c87;font-size:17rpx}.salesman-dimension>small{width:100%;text-align:right}.salesman-picker{display:flex;align-items:center;justify-content:space-between;min-width:230rpx;padding:10rpx 14rpx;border-bottom:2rpx solid var(--ink);background:#eee8dc;box-sizing:border-box}.salesman-picker strong{font-size:19rpx}.salesman-picker text{margin-left:20rpx;color:var(--coral);font-size:20rpx}
</style>
