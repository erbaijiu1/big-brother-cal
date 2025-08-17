<template>
  <view class="container">
    <!-- █████ 筛选栏 █████ -->
    <uni-forms :modelValue="query" class="search-bar" label-position="left" :label-width="120">
      <uni-forms-item name="channel" label="渠道">
        <picker :range="channelList" range-key="channel_name" @change="onChannelChange">
          <view class="picker">
            {{ getChannelName(query.channel) || '全部' }}
          </view>
        </picker>
      </uni-forms-item>

      <uni-forms-item name="category_id" label="分类">
        <picker :range="categoryList" range-key="main_category" @change="onCategoryChange">
          <view class="picker">
            {{ getCategoryName(query.category_id) || '全部' }}
          </view>
        </picker>
      </uni-forms-item>

      <uni-forms-item name="keyword" label="关键词">
        <uni-easyinput v-model="query.keyword" placeholder="支持模糊查询" @confirm="fetchData" clearable />
      </uni-forms-item>

      <view class="btn-group">
        <button class="mini-btn primary" @click="fetchData">查询</button>
        <button class="mini-btn" @click="resetQuery">重置</button>
        <label class="switch-wrap">
          <switch :checked="query.include_deleted" @change="onIncludeDeletedChange" />
          <text class="switch-label">显示已删除</text>
        </label>
        <button class="mini-btn success" @click="showEditDialog()">新建规则</button>
      </view>
    </uni-forms>

    <!-- █████ 表头 █████ -->
    <view class="table-head">
      <text class="id">ID</text>
      <text class="channel">渠道</text>
      <text class="category">分类</text>
      <text class="method">运输方式</text>
      <text class="trans_fee_rules">运输费用</text>
      <text class="delivery_fee_rules">派送费用</text>
      <text class="remark">备注</text>
      <text class="status">状态</text>
      <text class="action">操作</text>
    </view>

    <!-- █████ 列表正文（可滚动） █████ -->
    <scroll-view scroll-y style="max-height: 70vh">
      <view v-for="row in list" :key="row.id" class="table-row">
        <text class="id">{{ row.id }}</text>
        <text class="channel">{{ getChannelName(row.channel) }}</text>
        <text class="category">{{ getCategoryName(row.category_id) }}</text>
        <text class="method">{{ row.transport_method || '-' }}</text>

        <view class="trans_fee_rules">
          <RuleViewer :rules="row.unit_price_rules" />
        </view>

        <view class="delivery_fee_rules">
          <RuleViewer :rules="row.delivery_fee_rules" />
        </view>

        <text class="remark" :title="row.remark">{{ row.remark }}</text>

        <view class="status">
          <uni-tag :text="row.status == 2 ? '已删' : '正常'" :type="row.status == 2 ? 'error' : 'success'" size="mini" />
        </view>

        <view class="action">
          <button v-if="row.status != 2" size="mini" plain @click="showEditDialog(row)">编辑</button>
          <button v-if="row.status != 2" size="mini" type="warn" :plain="true" @click="handleDelete(row)">删</button>
          <button v-if="row.status == 2" size="mini" type="primary" plain @click="handleRecover(row)">恢</button>
        </view>
      </view>
    </scroll-view>

    <!-- █████ 分页 █████ -->
    <view class="pagination">
      <uni-pagination :total="total" :current="query.page" :pageSize="query.page_size" show-icon
        @change="onPageChange" />
    </view>

    <!-- 编辑弹窗（大号居中窗 + 内部滚动） -->
    <uni-popup ref="editPopup" type="center">
      <view class="editor-sheet">
        <RuleEditor v-model="editDialog.form" :channelList="channelList" :categoryList="categoryList"
          @save="onSaveFromChild" @cancel="closeEditDialog" />
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { BASE_URL } from '@/common/config'
import RuleViewer from '@/components/RuleViewer.vue'
import RuleEditor from '@/components/RuleEditor.vue'

const list = ref([])
const total = ref(0)
const channelList = ref([])
const categoryList = ref([])

// 查询参数
const query = reactive({
  page: 1,
  page_size: 50,
  channel: '',
  category_id: 0,  // int，默认0
  keyword: '',
  include_deleted: false
})

const editPopup = ref(null)
const editDialog = reactive({
  form: {
    id: null,
    channel: '',
    category_id: 0,
    transport_method: '',
    warehouse: '',
    min_consumption: 0,
    unit_price_rules: [],
    surcharge_fee_rules: [],
    delivery_fee_rules: [],
    discount_price: '',
    delivery_time: '',
    packaging_requirement: '',
    remark: '',
    compensation_policy: '',
    status: 1,
    filter_rules: ''
  }
})

/** 工具：把可能为字符串的 JSON 字段转为数组 */
function toArr(val) {
  if (Array.isArray(val)) return val
  if (typeof val === 'string') {
    try {
      const a = JSON.parse(val)
      return Array.isArray(a) ? a : []
    } catch { return [] }
  }
  return []
}

/** 渠道/分类 */
function fetchChannelList() {
  uni.request({
    url: `${BASE_URL}/cal_price/channel_mgr/`,
    method: 'POST',
    data: {},
    success(res) {
      channelList.value = res.data?.data || []
    }
  })
}
function fetchCategoryList() {
  uni.request({
    url: `${BASE_URL}/cal_price/classify_mgr/`,
    method: 'GET',
    success(res) {
      categoryList.value = res.data?.data || []
    }
  })
}
function getChannelName(code) {
  const c = channelList.value.find(item => item.channel_code === code)
  return c ? c.channel_name : code
}
function getCategoryName(id) {
  if (!id || id === 0) return ''
  const c = categoryList.value.find(item => Number(item.category_id) === Number(id))
  return c ? c.main_category : id
}

/** 生命周期 */
onMounted(() => {
  fetchChannelList()
  fetchCategoryList()
  fetchData()
})

/** 列表请求 */
function fetchData() {
  uni.request({
    url: `${BASE_URL}/cal_price/pricing_mgr/`,
    method: 'GET',
    data: {
      ...query,
      include_deleted: query.include_deleted ? 1 : 0
    },
    success(res) {
      const arr = res.data?.data || []
      list.value = arr.map(item => ({
        ...item,
        unit_price_rules: toArr(item.unit_price_rules),
        surcharge_fee_rules: toArr(item.surcharge_fee_rules),
        delivery_fee_rules: toArr(item.delivery_fee_rules),
      }))
      total.value = res.data?.total || 0
    }
  })
}

/** 查询区交互 */
function resetQuery() {
  query.channel = ''
  query.category_id = 0
  query.keyword = ''
  query.include_deleted = false
  fetchData()
}
function onPageChange(e) {
  query.page = e.current
  query.page_size = e.pageSize
  fetchData()
}
function onChannelChange(e) {
  const index = e.detail.value
  query.channel = channelList.value[index]?.channel_code || ''
}
function onCategoryChange(e) {
  const index = e.detail.value
  query.category_id = categoryList.value[index]?.category_id || 0
}
function onIncludeDeletedChange(e) {
  query.include_deleted = !!e.detail.value
  fetchData()
}

/** 编辑弹窗 */
function showEditDialog(row = null) {
  if (row) {
    // 编辑：把已有记录灌入（并兼容字符串数组）
    editDialog.form = {
      id: row.id ?? null,
      channel: row.channel ?? '',
      category_id: Number(row.category_id ?? 0),
      transport_method: row.transport_method ?? '',
      warehouse: row.warehouse ?? '',
      min_consumption: Number(row.min_consumption ?? 0),
      unit_price_rules: toArr(row.unit_price_rules),
      surcharge_fee_rules: toArr(row.surcharge_fee_rules),
      delivery_fee_rules: toArr(row.delivery_fee_rules),
      discount_price: row.discount_price ?? '',
      delivery_time: row.delivery_time ?? '',
      packaging_requirement: row.packaging_requirement ?? '',
      remark: row.remark ?? '',
      compensation_policy: row.compensation_policy ?? '',
      status: Number(row.status ?? 1),
      filter_rules: row.filter_rules ?? ''
    }
  } else {
    // 新建：给一套默认
    editDialog.form = {
      id: null,
      channel: '',
      category_id: 0,
      transport_method: '',
      warehouse: '',
      min_consumption: 0,
      unit_price_rules: [],
      surcharge_fee_rules: [],
      delivery_fee_rules: [],
      discount_price: '',
      delivery_time: '',
      packaging_requirement: '',
      remark: '',
      compensation_policy: '',
      status: 1,
      filter_rules: ''
    }
  }
  editPopup.value.open()
}
function closeEditDialog() {
  editPopup.value.close()
}

/** 保存（由子组件 RuleEditor 触发） */
function onSaveFromChild(payload) {
  // payload 已由 RuleEditor 规范化（数组或字符串按其内部配置）
  const url = payload.id
    ? `${BASE_URL}/cal_price/pricing_mgr/${payload.id}`
    : `${BASE_URL}/cal_price/pricing_mgr/`
  const method = payload.id ? 'PUT' : 'POST'

  uni.request({
    url, method, data: payload,
    success() {
      uni.showToast({ title: '保存成功', icon: 'success' })
      closeEditDialog()
      fetchData()
    }
  })
}

/** 删除/恢复 */
function handleDelete(row) {
  uni.showModal({
    title: '提示',
    content: '确定要删除该规则吗？'
  }).then(res => {
    if (res.confirm) {
      uni.request({
        url: `${BASE_URL}/cal_price/pricing_mgr/${row.id}`,
        method: 'DELETE',
        success() {
          uni.showToast({ title: '删除成功', icon: 'success' })
          fetchData()
        }
      })
    }
  })
}
function handleRecover(row) {
  uni.request({
    url: `${BASE_URL}/cal_price/pricing_mgr/recover/${row.id}`,
    method: 'POST',
    success() {
      uni.showToast({ title: '恢复成功', icon: 'success' })
      fetchData()
    }
  })
}

/** 下拉刷新 */
onPullDownRefresh(() => {
  fetchData()
  uni.stopPullDownRefresh()
})
</script>

<style>
.container {
  padding: 24rpx;
  background: #fafbfc;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx 24rpx;
}
.search-bar .uni-forms-item {
  width: calc(50% - 12rpx);
  margin-bottom: 2rpx !important;
  display: flex;
  align-items: center;
}
.search-bar .uni-forms-item__label {
  width: 120rpx !important;
  min-width: 120rpx;
  justify-content: flex-start;
}
.search-bar .uni-forms-item__content { flex: 1; min-width: 0; }
.search-bar .picker, .search-bar .uni-easyinput { width: 100%; }

/* 按钮组 */
.btn-group {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20rpx;
  margin-top: 12rpx;
}
.switch-wrap { display: flex; align-items: center; gap: 8rpx; }
.switch-label { font-size: 24rpx; }

/* 表格 */
.table-head, .table-row {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 20rpx;
  font-size: 26rpx;
  text-align: left;
  gap: 10rpx;
}
.table-head text, .table-row text { padding: 0 10rpx; }
.table-head { font-weight: 600; background: #f2f3f5; }
.table-row:not(:last-child) { border-bottom: 1px solid #eeeeee; }

.id { flex: 0 0 50px; }
.channel { flex: 0 0 80px; }
.category { flex: 0 0 140px; }
.method { flex: 0 0 70px; min-width: 70px; }
.trans_fee_rules, .delivery_fee_rules { flex: 1 1 300px; }
.remark {
  flex: 1 1 100px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.status { flex: 0 0 90px; text-align: center; }
.action { flex: 0 0 170px; display: flex; flex-wrap: wrap; gap: 12rpx; }

/* 分页 */
.pagination { margin: 32rpx 0; text-align: center; }

/* 选择展示 */
.picker {
  min-width: 110rpx;
  padding: 0 8rpx;
  color: #666;
  display: flex;
  align-items: center;
  margin-bottom: 0rpx !important;
}

/* 窄屏降级为单列 */
@media (max-width: 750px) {
  .search-bar .uni-forms-item { width: 100%; }
}

/* 大号编辑窗：外层控制宽高，内部滚动 */
.editor-sheet{
  width: 92vw;
  max-width: 1080px;
  max-height: 88vh;
  background:#fff;
  border-radius: 14rpx;
  overflow: auto;  /* 关键：内部滚动 */
  padding: 16rpx;
}

</style>
