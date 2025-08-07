<template>
  <view class="container">
    <!-- █████ 搜索栏 █████ -->
    <uni-forms :modelValue="query" ref="searchFormRef" class="search-bar">
      <uni-forms-item name="keyword" label="关键词">
        <uni-easyinput v-model="query.keyword" placeholder="主分类名称" @confirm="fetchData" clearable />
      </uni-forms-item>

      <view class="btn-group">
        <button class="mini-btn primary" @click="fetchData">查询</button>
        <button class="mini-btn" @click="resetQuery">重置</button>
        <label class="switch-wrap">
          <switch :checked="query.include_deleted" @change="onIncludeDeletedChange" />
          <text class="switch-label">显示已删除</text>
        </label>
        <button class="mini-btn success" @click="showEditDialog()">新建分类</button>
      </view>
    </uni-forms>

    <!-- █████ 表头 █████ -->
    <view class="table-head">
      <text class="code">ID</text>
      <text class="name">主分类</text>
      <text class="remark">分类示例</text>
      <text class="temp">温控</text>
      <text class="hazard">危险</text>
      <text class="status">状态</text>
      <text class="action">操作</text>
    </view>

    <!-- █████ 列表正文（可滚动） █████ -->
    <scroll-view scroll-y style="max-height: 70vh">
      <view v-for="row in list" :key="row.category_id" class="table-row">
        <text class="code">{{ row.category_id }}</text>
        <text class="name">{{ row.main_category }}</text>
        <text class="remark" :title="row.sub_examples">{{ row.sub_examples }}</text>
        <text class="temp">{{ row.temperature_req }}</text>
        <text class="hazard">{{ row.hazard_level }}</text>
        <view class="status">
          <uni-tag
            :text="row.status == 2 ? '已删' : '正常'"
            :type="row.status == 2 ? 'error' : 'success'"
            size="mini"
          />
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
      <uni-pagination
        :total="total"
        :current="query.page"
        :pageSize="query.page_size"
        show-icon
        @change="onPageChange"
      />
    </view>

    <!-- █████ 编辑弹窗 █████ -->
    <uni-popup ref="editPopup" type="dialog">
      <view class="edit-dialog">
        <uni-forms :modelValue="editDialog.form" :rules="editRules" ref="editFormRef" label-width="80px">
          <uni-forms-item name="main_category" label="主分类">
            <uni-easyinput v-model="editDialog.form.main_category" placeholder="主分类名称" />
          </uni-forms-item>
          <uni-forms-item name="sub_examples" label="子类示例">
            <uni-easyinput v-model="editDialog.form.sub_examples" placeholder="逗号分隔" />
          </uni-forms-item>
          <uni-forms-item name="description" label="说明">
            <uni-easyinput v-model="editDialog.form.description" type="textarea" placeholder="说明" />
          </uni-forms-item>
          <uni-forms-item name="temperature_req" label="温控">
            <uni-easyinput v-model="editDialog.form.temperature_req" placeholder="冷链/常温" />
          </uni-forms-item>
          <uni-forms-item name="hazard_level" label="危险等级">
            <uni-easyinput v-model="editDialog.form.hazard_level" placeholder="非险/险" />
          </uni-forms-item>
          <uni-forms-item name="storage_level" label="库位等级">
            <uni-easyinput v-model="editDialog.form.storage_level" placeholder="A/B/C" />
          </uni-forms-item>
          <uni-forms-item name="priority" label="优先级">
            <uni-easyinput v-model="editDialog.form.priority" type="number" placeholder="数字越小优先级越高" />
          </uni-forms-item>
        </uni-forms>
        <view class="dialog-actions">
          <button @click="closeEditDialog">取消</button>
          <button type="primary" @click="saveCategory">保存</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { BASE_URL } from '@/common/config'

const list = ref([])
const total = ref(0)
const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  include_deleted: false
})

const searchFormRef = ref(null)

// 编辑弹窗
const editPopup = ref(null)
const editDialog = reactive({
  visible: false,
  isEdit: false,
  form: {
    category_id: null,
    main_category: '',
    sub_examples: '',
    description: '',
    temperature_req: '',
    hazard_level: '',
    storage_level: '',
    priority: 99
  }
})
const editFormRef = ref(null)
const editRules = {
  main_category: [{ required: true, errorMessage: '主分类必填', trigger: 'blur' }],
  sub_examples: [{ required: true, errorMessage: '分类示例必填', trigger: 'blur' }],
  description: [{ required: false, trigger: 'blur' }],       // 写个空规则
  temperature_req: [{ required: false, trigger: 'blur' }],
  hazard_level: [{ required: false, trigger: 'blur' }],
  storage_level: [{ required: false, trigger: 'blur' }],
  priority: [{ required: false, trigger: 'blur' }]
  ,category_id: []
}

onMounted(() => {
  fetchData()
})

function fetchData() {
  uni.request({
    url: `${BASE_URL}/cal_price/classify_mgr/`,
    method: 'GET',
    data: { ...query, include_deleted: query.include_deleted ? 1 : 0 },
    success(res) {
      list.value = res.data.data
      total.value = res.data.total
    }
  })
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

function onIncludeDeletedChange(e) {
  query.include_deleted = !!e.detail.value
  fetchData()
}

function showEditDialog(row = null) {
  if (row) {
    editDialog.isEdit = true
    // 注意类型兼容
    editDialog.form = {
      category_id: row.category_id ?? null,
      main_category: row.main_category ?? '',
      sub_examples: row.sub_examples ?? '',
      description: row.description ?? '',
      temperature_req: row.temperature_req ?? '',
      hazard_level: row.hazard_level ?? '',
      storage_level: row.storage_level ?? '',
      priority: typeof row.priority === 'number' ? row.priority : Number(row.priority) || 99
    }
  } else {
    // 新建
    editDialog.isEdit = false
    editDialog.form = {
      category_id: null,
      main_category: '',
      sub_examples: '',
      description: '',
      temperature_req: '',
      hazard_level: '',
      storage_level: '',
      priority: 99
    }
  }
  editPopup.value.open()
}

function closeEditDialog() {
  editPopup.value.close()
}

function saveCategory() {
  if (!editFormRef.value) {
    uni.showToast({ title: '表单未初始化', icon: 'none' })
    return
  }

  console.log('form:', editDialog.form)

  editFormRef.value.validate()
    .then(() => {
      const isEdit = editDialog.isEdit
      const apiUrl = isEdit
        ? `${BASE_URL}/cal_price/classify_mgr/${editDialog.form.category_id}`
        : `${BASE_URL}/cal_price/classify_mgr/`
      const method = isEdit ? 'PUT' : 'POST'
      uni.request({
        url: apiUrl,
        method,
        data: editDialog.form,
        success(res) {
          uni.showToast({ title: isEdit ? '保存成功' : '新增成功', icon: 'success' })
          closeEditDialog()
          fetchData()
        },
        fail() {
          uni.showToast({ title: isEdit ? '保存失败' : '新增失败', icon: 'error' })
        }
      })
    })
    .catch(err => {
      console.log('校验失败', err)
      uni.showToast({ title: '请检查表单填写', icon: 'none' })
    })
}


function handleDelete(row) {
  uni.showModal({
    title: '提示',
    content: '确定要删除该分类吗？'
  }).then(res => {
    if (res.confirm) {
      uni.request({
        url: `${BASE_URL}/cal_price/classify_mgr/${row.category_id}`,
        method: 'DELETE',
        success() {
          uni.showToast({ title: '已删除', icon: 'success' })
          fetchData()
        }
      })
    }
  })
}

function handleRecover(row) {
  uni.request({
    url: `${BASE_URL}/cal_price/classify_mgr/recover/${row.category_id}`,
    method: 'POST',
    success() {
      uni.showToast({ title: '已恢复', icon: 'success' })
      fetchData()
    }
  })
}

// 下拉刷新
onPullDownRefresh(() => {
  fetchData()
  uni.stopPullDownRefresh()
})

function onShow() {
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.redirectTo({ url: '/pages/login/index' })
  }
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
/* ===== 表格结构 ===== */
.table-head,
.table-row {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 20rpx;
  font-size: 26rpx;
  gap: 8rpx;  /* 推荐加一点间隔，视觉更清晰 */
}
.table-head {
  font-weight: 600;
  background: #f2f3f5;
}
.table-row:not(:last-child) {
  border-bottom: 1px solid #eeeeee;
}

/* 列宽自定义，灵活扩展 */
.code    { flex: 0 0 80px; min-width: 60px; text-align: center; }
.name    { flex: 0 0 120px; min-width: 100px; word-break: break-all; }
.remark  { 
  flex: 1 1 auto;
  min-width: 150px;
  /* 支持多行显示，如果想要2行省略用下两行，但小程序端不总兼容 */
  /* overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; */
  word-break: break-all;
  white-space: normal;
}
.temp    { flex: 0 0 80px; min-width: 60px; text-align: center; }
.hazard  { flex: 0 0 80px; min-width: 60px; text-align: center; }
.status  { flex: 0 0 70px; min-width: 60px; text-align: center; }
.action  { flex: 0 0 170px; display: flex; flex-wrap: wrap; gap: 12rpx; }

/* 可以额外优化操作按钮样式 */
.action button {
  margin: 0 4rpx 4rpx 0;
}

/* ===== 分页 ===== */
.pagination { margin: 32rpx 0; text-align: center; }

/* ===== 弹窗 ===== */
.edit-dialog {
  background: #ffffff;
  padding: 24rpx;
  border-radius: 12rpx;
  width: 700rpx;
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 24rpx;
  margin-top: 18rpx;
}
</style>
