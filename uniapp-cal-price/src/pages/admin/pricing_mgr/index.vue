<template>
  <view class="container">
    <!-- █████ 筛选栏 █████ -->
    <uni-forms :modelValue="query" class="search-bar">
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
      <text class="method">费用规则</text>
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
        <view class="rules">
          <RuleViewer :rules="row.unit_price_rules" />
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

    <!-- █████ 编辑弹窗 █████ -->
    <uni-popup ref="editPopup" type="dialog">
      <view class="edit-dialog">
        <uni-forms :modelValue="editDialog.form" :rules="editRules" ref="editFormRef" label-width="90px">
          <uni-forms-item name="channel" label="渠道">
            <picker :range="channelList" range-key="channel_name" @change="onEditChannelChange">
              <view class="picker">
                {{ getChannelName(editDialog.form.channel) || '请选择' }}
              </view>
            </picker>
          </uni-forms-item>
          <uni-forms-item name="category_id" label="分类">
            <picker :range="categoryList" range-key="main_category" @change="onEditCategoryChange">
              <view class="picker">
                {{ getCategoryName(editDialog.form.category_id) || '请选择' }}
              </view>
            </picker>
          </uni-forms-item>
          <uni-forms-item name="transport_method" label="运输方式">
            <uni-easyinput v-model="editDialog.form.transport_method" />
          </uni-forms-item>

          <uni-forms-item name="unit_price_rules" label="运费规则">
            <RuleEditor v-model="editDialog.form.unit_price_rules" />
          </uni-forms-item>

          <uni-forms-item name="remark" label="备注">
            <uni-easyinput v-model="editDialog.form.remark" type="textarea" />
          </uni-forms-item>
        </uni-forms>
        <view class="dialog-actions">
          <button @click="closeEditDialog">取消</button>
          <button type="primary" @click="saveRule">保存</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>


<script setup>
import { ref, reactive, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { BASE_URL } from '@/common/config'
import RuleViewer from '@/components/RuleViewer.vue'


const list = ref([])
const total = ref(0)
const channelList = ref([])
const categoryList = ref([])

// category_id: int，默认0
const query = reactive({
  page: 1,
  page_size: 50,
  channel: '',
  category_id: 0,   // int，默认0
  keyword: '',
  include_deleted: false
})

const searchFormRef = ref(null)
const editPopup = ref(null)
const editDialog = reactive({
  isEdit: false,
  form: {
    id: null,
    channel: '',
    category_id: 0,
    transport_method: '',
    remark: ''
  }
})
const editFormRef = ref(null)
const editRules = {
  channel: [{ required: true, errorMessage: '请选择渠道' }],
  category_id: [{ required: true, errorMessage: '请选择分类' }],
}

// 拉取渠道和分类（可改成你实际API）
function fetchChannelList() {
  uni.request({
    url: `${BASE_URL}/cal_price/channel_mgr/`, method: 'POST', data: {},
    success(res) {
      channelList.value = res.data.data || []
    }
  })
}
function fetchCategoryList() {
  uni.request({
    url: `${BASE_URL}/cal_price/classify_mgr/`, method: 'GET',
    success(res) {
      categoryList.value = res.data.data || []
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

onMounted(() => {
  fetchChannelList()
  fetchCategoryList()
  fetchData()
})

function fetchData() {
  uni.request({
    url: `${BASE_URL}/cal_price/pricing_mgr/`,
    method: 'GET',
    data: {
      ...query,
      include_deleted: query.include_deleted ? 1 : 0
    },
    success(res) {
      // 假设接口返回 unit_price_rules 是字符串，要处理为数组
      list.value = (res.data.data || []).map(item => ({
        ...item,
        unit_price_rules: typeof item.unit_price_rules === 'string'
          ? JSON.parse(item.unit_price_rules || '[]')
          : (item.unit_price_rules || [])
      }))
      total.value = res.data.total
    }
  })
}
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
function showEditDialog(row = null) {
  if (row) {
    editDialog.isEdit = true
    editDialog.form = { ...row }
  } else {
    editDialog.isEdit = false
    editDialog.form = {
      id: null,
      channel: '',
      category_id: 0,
      transport_method: '',
      remark: '',
      unit_price_rules: []
    }
  }
  editPopup.value.open()
}
function closeEditDialog() {
  editPopup.value.close()
}
function onEditChannelChange(e) {
  const index = e.detail.value
  editDialog.form.channel = channelList.value[index]?.channel_code || ''
}
function onEditCategoryChange(e) {
  const index = e.detail.value
  editDialog.form.category_id = categoryList.value[index]?.category_id || 0
}
function saveRule() {
  if (!editFormRef.value) {
    uni.showToast({ title: '表单未初始化', icon: 'none' })
    return
  }
  editFormRef.value.validate().then(() => {
    if (editDialog.isEdit) {
      uni.request({
        url: `${BASE_URL}/cal_price/pricing_mgr/${editDialog.form.id}`,
        method: 'PUT',
        data: editDialog.form,
        success(res) {
          uni.showToast({ title: '保存成功', icon: 'success' })
          closeEditDialog()
          fetchData()
        }
      })
    } else {
      uni.request({
        url: `${BASE_URL}/cal_price/pricing_mgr/`,
        method: 'POST',
        data: editDialog.form,
        success(res) {
          uni.showToast({ title: '保存成功', icon: 'success' })
          closeEditDialog()
          fetchData()
        }
      })
    }
  }).catch(err => {
    uni.showToast({ title: '请检查表单填写', icon: 'none' })
  })
}
function handleDelete(row) {
  uni.showModal({
    title: '提示',
    content: '确定要删除该规则吗？'
  }).then(res => {
    if (res.confirm) {
      uni.request({
        url: `${BASE_URL}/pricing_mgr/${row.id}`,
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

.search-bar {
  background: #fff;
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

.switch-label {
  font-size: 24rpx;
}

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

.id {
  flex: 0 0 70px;
}

.channel {
  flex: 0 0 110px;
}

.category {
  flex: 0 0 110px;
}

.method {
  flex: 0 0 110px;
}

.remark {
  flex: 1 1 auto;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.status {
  flex: 0 0 90px;
  text-align: center;
}

.action {
  flex: 0 0 170px;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.pagination {
  margin: 32rpx 0;
  text-align: center;
}

.edit-dialog {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  width: 680rpx;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 24rpx;
  margin-top: 18rpx;
}

.picker {
  min-width: 110rpx;
  padding: 0 8rpx;
  color: #666;
}
</style>
