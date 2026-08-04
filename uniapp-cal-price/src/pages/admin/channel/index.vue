<template>
  <view class="container">
    <!-- █████ 搜索栏 █████ -->
    <uni-forms :modelValue="query" :rules="editRules" ref="searchFormRef" class="search-bar">
      <uni-forms-item name="keyword" label="关键词">
        <uni-easyinput v-model="query.keyword" placeholder="渠道编码/名称" @confirm="fetchData" clearable />
      </uni-forms-item>

      <view class="btn-group">
        <button class="mini-btn primary" @click="fetchData">查询</button>
        <button class="mini-btn" @click="resetQuery">重置</button>

        <label class="switch-wrap">
          <switch :checked="query.include_deleted" @change="onIncludeDeletedChange" />
          <text class="switch-label">显示已删除</text>
        </label>

        <button class="mini-btn success" @click="showEditDialog()">新建渠道</button>
      </view>
    </uni-forms>

    <!-- █████ 表头 █████ -->
    <view class="table-head">
      <text class="code">渠道编码</text>
      <text class="name">渠道名称</text>
      <text class="address">收货地址</text>
      <text class="surcharge">附加费</text> <!-- 新增 -->
      <text class="remark">备注</text>
      <text class="status">状态</text>
      <text class="action">操作</text>
    </view>

    <!-- █████ 列表正文（可滚动） █████ -->
    <scroll-view scroll-y style="max-height: 70vh">
      <view v-for="row in list" :key="row.id" class="table-row">
        <text class="code">{{ row.channel_code }}</text>
        <text class="name">{{ row.channel_name }}</text>
        <text class="address" :title="row.receiving_address">{{ row.receiving_address || '未配置' }}</text>

        <!-- 新增：附加费摘要 -->
        <view class="surcharge">
          <SurchargeSummary :rules="row.surcharge_rules" :nameMaps="nameMaps" :limit="2" />
        </view>

        <!-- 备注 2 行省略，title 提示完整文本 -->
        <text class="remark" :title="row.remark">{{ row.remark }}</text>

        <view class="status">
          <uni-tag :text="row.delete_flag ? '已删' : '正常'" :type="row.delete_flag ? 'error' : 'success'" size="mini" />
        </view>

        <view class="action">
          <button v-if="!row.delete_flag" size="mini" plain @click="showEditDialog(row)">编辑</button>
          <button v-if="!row.delete_flag" size="mini" plain type="primary" @click="openSurcharge(row)">附加费</button>
          <button v-if="!row.delete_flag" size="mini" plain @click="openQuoteHistory(row)">配置历史</button>
          <button v-if="!row.delete_flag" size="mini" type="warn" :plain="true" @click="handleDelete(row)">删</button>
          <button v-if="row.delete_flag" size="mini" type="primary" plain @click="handleRecover(row)">恢</button>
        </view>
      </view>
    </scroll-view>

    <!-- █████ 分页 █████ -->
    <view class="pagination">
      <uni-pagination :total="total" :current="query.page" :pageSize="query.page_size" show-icon
        @change="onPageChange" />
    </view>

    <!-- █████ 编辑弹窗 █████ -->
    <uni-popup ref="editPopup" type="dialog" class="wide-popup">
      <view class="edit-dialog">
        <uni-forms :modelValue="editDialog.form" :rules="editRules" ref="editFormRef" label-width="80px">
          <uni-forms-item name="channel_code" label="渠道编码">
            <uni-easyinput v-model="editDialog.form.channel_code" placeholder="请输入渠道编码" :disabled="editDialog.isEdit" />
          </uni-forms-item>
          <uni-forms-item name="channel_name" label="渠道名称">
            <uni-easyinput v-model="editDialog.form.channel_name" placeholder="请输入渠道名称" />
          </uni-forms-item>
          <uni-forms-item name="receiving_address" label="收货地址">
            <uni-easyinput
              v-model="editDialog.form.receiving_address"
              type="textarea"
              maxlength="500"
              placeholder="请输入该渠道发给客户的完整收货地址"
            />
          </uni-forms-item>
          <view class="section-title">
            <text>对客报价展示</text>
            <switch
              :checked="editDialog.form.customer_quote_config.enabled"
              @change="editDialog.form.customer_quote_config.enabled = !!$event.detail.value"
            />
          </view>
          <uni-forms-item label="入仓截单">
            <uni-easyinput
              v-model="editDialog.form.customer_quote_config.cutoff_text"
              placeholder="例如：当日12点前入仓"
            />
          </uni-forms-item>
          <uni-forms-item label="派送时效">
            <uni-easyinput
              v-model="editDialog.form.customer_quote_config.eta_text"
              placeholder="例如：预计次日香港派送"
            />
          </uni-forms-item>
          <uni-forms-item label="交收范围">
            <uni-easyinput
              v-model="editDialog.form.customer_quote_config.delivery_scope"
              placeholder="例如：香港地面交收"
            />
          </uni-forms-item>
          <uni-forms-item label="关键提醒">
            <uni-easyinput
              v-model="editDialog.form.customer_quote_config.primary_notice"
              type="textarea"
              placeholder="例如：上楼或特殊派送条件需要重新核价"
            />
          </uni-forms-item>
          <uni-forms-item label="查验提示">
            <uni-easyinput
              v-model="editDialog.form.customer_quote_config.customs_notice"
              placeholder="例如：海关查验可能导致时效延迟"
            />
          </uni-forms-item>
          <view class="switch-row">
            <text>对客展示中港运输费与香港派送费</text>
            <switch
              :checked="editDialog.form.customer_quote_config.show_fee_breakdown"
              @change="editDialog.form.customer_quote_config.show_fee_breakdown = !!$event.detail.value"
            />
          </view>
          <uni-forms-item name="remark" label="备注">
            <uni-easyinput v-model="editDialog.form.remark" type="textarea" placeholder="请输入备注" />
          </uni-forms-item>
        </uni-forms>

        <view class="dialog-actions">
          <button @click="closeEditDialog">取消</button>
          <button type="primary" @click="saveChannel">保存</button>
        </view>
      </view>
    </uni-popup>
  </view>


  <!-- 页面最底部挂载弹窗组件 -->
  <SurchargeEditor ref="surchargeRef" @saved="fetchData" />

  <uni-popup ref="historyPopup" type="center">
    <view class="history-dialog">
      <view class="history-head">
        <view>
          <text class="history-title">{{ historyDialog.channelName }} · 对客配置历史</text>
          <text class="history-subtitle">仅供备查，当前报价始终读取最新配置</text>
        </view>
        <button size="mini" plain @click="historyPopup.close()">关闭</button>
      </view>
      <scroll-view scroll-y class="history-list">
        <view v-if="!historyDialog.items.length" class="history-empty">暂无配置变更记录</view>
        <view v-for="item in historyDialog.items" :key="item.id" class="history-card">
          <view class="history-meta">
            <text>{{ item.changed_at || '-' }}</text>
            <text>{{ item.changed_by_name || '未知操作人' }}</text>
          </view>
          <text>截单：{{ item.config_snapshot?.cutoff_text || '未配置' }}</text>
          <text>时效：{{ item.config_snapshot?.eta_text || '未配置' }}</text>
          <text>交收：{{ item.config_snapshot?.delivery_scope || '未配置' }}</text>
        </view>
      </scroll-view>
    </view>
  </uni-popup>



</template>


<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import SurchargeEditor from '@/components/SurchargeEditor.vue'
import SurchargeSummary from '@/components/SurchargeSummary.vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request'   // ✅ 引入封装过的 request

const list = ref([])
const total = ref(0)
const query = reactive({
  page: 1,
  page_size: 50,
  keyword: '',
  include_deleted: false
})

const searchFormRef = ref(null)
const nameMaps = reactive({
  areaCatsById: {},
  distsById: {},
  subsById: {}
})

// 编辑弹窗
const editPopup = ref(null)
const editDialog = reactive({
  isEdit: false,
  form: emptyChannelForm()
})
const editFormRef = ref(null)
const editRules = {
  channel_code: [{ required: true, errorMessage: '渠道编码必填' }],
  channel_name: [{ required: true, errorMessage: '渠道名称必填' }],
  receiving_address: [],
  remark: []
}

onMounted(() => { fetchData(); preloadNameMaps() })

function defaultCustomerQuoteConfig() {
  return {
    enabled: true,
    cutoff_text: '',
    eta_text: '',
    delivery_scope: '香港地面交收',
    primary_notice: '上楼或特殊派送条件需要重新核价',
    customs_notice: '',
    show_fee_breakdown: true
  }
}

function emptyChannelForm() {
  return {
    id: null,
    channel_code: '',
    channel_name: '',
    receiving_address: '',
    remark: '',
    customer_quote_config: defaultCustomerQuoteConfig()
  }
}

// ===== 数据请求 =====
async function fetchData() {
  const res = await request({
    url: '/cal_price/channel_mgr/',
    method: 'POST',
    data: { ...query }
  })
  list.value = (res.data || []).map(row => {
    let rules = row.surcharge_rules
    if (typeof rules === 'string') {
      try { rules = JSON.parse(rules || '{}') } catch { rules = {} }
    }
    let quoteConfig = row.customer_quote_config
    if (typeof quoteConfig === 'string') {
      try { quoteConfig = JSON.parse(quoteConfig || '{}') } catch { quoteConfig = {} }
    }
    return {
      ...row,
      surcharge_rules: rules,
      customer_quote_config: { ...defaultCustomerQuoteConfig(), ...(quoteConfig || {}) }
    }
  })
  total.value = res.total || 0
}

function resetQuery() {
  query.keyword = ''
  query.page = 1
  query.include_deleted = false
  fetchData()
}
function onPageChange(e) {
  query.page = e.current
  query.page_size = e.pageSize
  fetchData()
}

// ===== 编辑弹窗 =====
function showEditDialog(row = null) {
  if (row) {
    editDialog.isEdit = true
    editDialog.form = {
      ...row,
      customer_quote_config: {
        ...defaultCustomerQuoteConfig(),
        ...(row.customer_quote_config || {})
      }
    }
  } else {
    editDialog.isEdit = false
    editDialog.form = emptyChannelForm()
  }
  editPopup.value.open()
}
function closeEditDialog() { editPopup.value.close() }

async function saveChannel() {
  try {
    await editFormRef.value.validate()
    if (editDialog.isEdit) {
      await request({
        url: `/cal_price/channel_mgr/${editDialog.form.id}`,
        method: 'PUT',
        data: editDialog.form
      })
    } else {
      await request({
        url: '/cal_price/channel_mgr/add',
        method: 'POST',
        data: editDialog.form
      })
    }
    uni.showToast({ title: '保存成功', icon: 'success' })
    closeEditDialog()
    fetchData()
  } catch (err) {
    console.error(err)
    uni.showToast({ title: '请检查表单填写', icon: 'none' })
  }
}

async function handleDelete(row) {
  const res = await uni.showModal({ title: '提示', content: '确定要删除该渠道吗？' })
  if (res.confirm) {
    await request({ url: `/cal_price/channel_mgr/${row.id}`, method: 'DELETE' })
    uni.showToast({ title: '删除成功', icon: 'success' })
    fetchData()
  }
}

async function handleRecover(row) {
  await request({ url: `/cal_price/channel_mgr/recover/${row.id}`, method: 'POST' })
  uni.showToast({ title: '恢复成功', icon: 'success' })
  fetchData()
}

// ===== 其它 =====
onPullDownRefresh(() => { fetchData(); uni.stopPullDownRefresh() })
function onIncludeDeletedChange(e) { query.include_deleted = !!e.detail.value; fetchData() }

const surchargeRef = ref(null)
async function openSurcharge(row) {
  if (!row?.id) {
    uni.showToast({ title: '请先保存渠道', icon: 'none' })
    return
  }
  const payload = row.surcharge_rules?.surcharges ? row.surcharge_rules : null
  await nextTick()                    // 等子组件和其内部 uni-popup 完成挂载
  surchargeRef.value?.open(row.id, payload)
}

const historyPopup = ref(null)
const historyDialog = reactive({ channelName: '', items: [] })

async function openQuoteHistory(row) {
  historyDialog.channelName = row.channel_name || row.channel_code
  const res = await request({
    url: `/cal_price/channel_mgr/${row.id}/customer-quote-history`,
    method: 'GET'
  })
  historyDialog.items = res.data || []
  historyPopup.value.open()
}

async function preloadNameMaps() {
  const areas = await request({ url: '/cal_price/area_categories/', method: 'GET' })
  ;(areas || []).forEach(c => { nameMaps.areaCatsById[c.id] = c.name })

  const dists = await request({ url: '/cal_price/districts/', method: 'GET' })
  ;(dists || []).forEach(d => {
    nameMaps.distsById[d.id] = d.name_cn
    ;(d.subs || []).forEach(s => {
      nameMaps.subsById[s.id] = `${d.name_cn}·${s.name_cn}`
    })
  })
}
</script>


<style>
/* ===== 公共容器 & 搜索 ===== */
.container {
  padding: 24rpx;
  background: #fafbfc;
}
.search-bar {
  background: #ffffff;
  padding: 20rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}
.btn-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20rpx;
  margin-top: 20rpx;
}
.switch-wrap {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.switch-label { font-size: 24rpx; }

/* ===== 表格结构 ===== */
.table-head,
.table-row {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 20rpx;
  font-size: 26rpx;
}
.table-head {
  font-weight: 600;
  background: #f2f3f5;
}
.table-row:not(:last-child) {
  border-bottom: 1px solid #eeeeee;
}

/* flex 列宽：20% | 20% | auto | 90px | 170px */
.code   { flex: 0 0 20%; }
.name   { flex: 0 0 14%; }
.address {
  flex: 0 0 22%;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: #4b5563;
}
.surcharge { flex: 0 0 24%; }   /* 新增 */
.remark {
  flex: 1 1 auto;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;          /* 最多两行 */
  -webkit-box-orient: vertical;
}
.status { flex: 0 0 90px; text-align: center; }
.action { flex: 0 0 170px; display: flex; flex-wrap: wrap; gap: 12rpx; }

/* ===== 分页 ===== */
.pagination { margin: 32rpx 0; text-align: center; }

/* ===== 弹窗 ===== */
.edit-dialog {
  background: #ffffff;
  padding: 24rpx;
  border-radius: 12rpx;
  width: 90%; /* Use 90% of the viewport width */
  max-width: 800rpx; /* Optional: limit maximum width */
}

.wide-popup .uni-popup__wrapper-box {
  width: 90% !important;
  max-width: 1000rpx !important;
  min-width: 600rpx !important; /* 添加最小宽度以防止过窄 */
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 24rpx;
  margin-top: 18rpx;
}

.section-title,
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 18rpx 0;
  color: #1f2937;
  font-weight: 600;
}
.section-title {
  margin: 8rpx 0 18rpx;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
}
.switch-row {
  margin-bottom: 20rpx;
  font-size: 26rpx;
  font-weight: 500;
}
.history-dialog {
  width: 720rpx;
  max-height: 78vh;
  padding: 28rpx;
  border-radius: 18rpx;
  background: #fffdf8;
  box-shadow: 0 24rpx 80rpx rgba(31, 41, 55, 0.2);
}
.history-head,
.history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}
.history-title,
.history-subtitle,
.history-card text {
  display: block;
}
.history-title { font-size: 30rpx; font-weight: 700; color: #17202a; }
.history-subtitle { margin-top: 6rpx; font-size: 22rpx; color: #7b8794; }
.history-list { max-height: 58vh; margin-top: 24rpx; }
.history-card {
  margin-bottom: 16rpx;
  padding: 20rpx;
  border-left: 6rpx solid #d69e2e;
  border-radius: 10rpx;
  background: #ffffff;
  color: #344050;
  line-height: 1.75;
}
.history-meta { margin-bottom: 8rpx; color: #8a6420; font-size: 22rpx; }
.history-empty { padding: 70rpx 0; text-align: center; color: #8b95a1; }
</style>
