<template>
  <view class="container">
    <!-- █████ 筛选栏 █████ -->
    <uni-forms :modelValue="query" class="search-bar" label-position="left" :label-width="120">
      <uni-forms-item name="username" label="账号">
        <uni-easyinput v-model="query.username" placeholder="账号模糊查询" @confirm="fetchData" clearable />
      </uni-forms-item>

      <view class="btn-group">
        <button class="mini-btn primary" @click="fetchData">查询</button>
        <button class="mini-btn" @click="resetQuery">重置</button>
        <label class="switch-wrap">
          <switch :checked="query.include_deleted" @change="onIncludeDeletedChange" />
          <text class="switch-label">显示已删除</text>
        </label>
        <button class="mini-btn success" @click="showEditDialog()">新建用户</button>
      </view>
    </uni-forms>

    <!-- █████ 表头 █████ -->
    <view class="table-head">
      <text class="id">ID</text>
      <text class="username">账号</text>
      <text class="nickname">昵称</text>
      <text class="status">状态</text>
      <text class="action">操作</text>
    </view>

    <!-- █████ 列表正文 █████ -->
    <scroll-view scroll-y style="max-height: 70vh">
      <view v-for="row in list" :key="row.id" class="table-row">
        <text class="id">{{ row.id }}</text>
        <text class="username">{{ row.username }}</text>
        <text class="nickname">{{ row.nickname }}</text>
        <view class="status">
          <uni-tag
            :text="row.status == 2 ? '已删' : (row.status == 1 ? '正常' : '禁用')"
            :type="row.status == 2 ? 'error' : (row.status == 1 ? 'success' : 'warning')"
            size="mini"
          />
        </view>
        <view class="action">
          <button v-if="row.status != 2" size="mini" plain @click="showEditDialog(row)">编辑</button>
          <button v-if="row.status != 2" size="mini" type="warn" plain @click="handleDelete(row)">删</button>
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
        <!-- 注意：:rules 绑定的是 ref(editRules)，并且通过 setRules 动态更新 -->
        <uni-forms :modelValue="editDialog.form" :rules="editRules" ref="editFormRef" label-width="80px">
          <uni-forms-item name="username" label="账号">
            <uni-easyinput v-model="editDialog.form.username" placeholder="请输入账号" :disabled="editDialog.isEdit" />
          </uni-forms-item>

          <!-- 始终展示密码框：
               新增：必填（≥8位）
               编辑：可留空（留空不修改；若填也必须 ≥8位）
          -->
          <uni-forms-item name="password" label="密码">
            <uni-easyinput
              v-model="editDialog.form.password"
              type="password"
              placeholder="新增必填≥8位；编辑留空表示不修改"
              @blur="onPasswordBlur"
            />
          </uni-forms-item>

          <uni-forms-item name="nickname" label="昵称">
            <uni-easyinput v-model="editDialog.form.nickname" placeholder="请输入昵称" />
          </uni-forms-item>

          <uni-forms-item name="status" label="状态">
            <picker :range="statusOptions" range-key="label" :value="statusIndex" @change="onStatusChange">
              <view class="picker">{{ statusLabel }}</view>
            </picker>
          </uni-forms-item>
        </uni-forms>

        <view class="dialog-actions">
          <button @click="closeEditDialog">取消</button>
          <button type="primary" @click="saveUser">保存</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request'

/* ========= 列表 & 筛选 ========= */
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, username: '', include_deleted: false })

/* ========= 编辑弹窗 ========= */
const editPopup = ref(null)
const editFormRef = ref(null)
const editDialog = reactive({
  isEdit: false,
  form: { id: null, username: '', password: '', nickname: '', status: 1 }
})

/* ========= 状态选项 ========= */
const statusOptions = [
  { value: 0, label: '初始化' },
  { value: 1, label: '正常' },
  { value: 2, label: '已删' }
]
const statusIndex = computed(() =>
  Math.max(0, statusOptions.findIndex(opt => opt.value === editDialog.form.status))
)
const statusLabel = computed(() => statusOptions[statusIndex.value]?.label || '初始化')
function onStatusChange(e) { editDialog.form.status = statusOptions[e.detail.value]?.value ?? 1 }

/* ========= 动态校验规则（关键修复） =========
 * 使用 uni-forms 官方格式：{ fieldName: { rules: [ ... ] } }
 * 并在新增/编辑时调用 setRules 应用最新规则。
 */
const editRules = ref(makeRules(false)) // 默认按“新增”规则初始化；会在打开弹窗时重置

function makeRules(isEdit) {
  return {
    username: {
      rules: [{ required: true, errorMessage: '账号必填' }]
    },
    password: {
      rules: [
        // 编辑时允许留空；新增必须填写
        {
          validateFunction: (_rule, value) => {
            if (isEdit) {
              // 编辑：允许空；若填了则需 ≥8 位
              if (!value) return true
              return String(value).length >= 8
            } else {
              // 新增：必填且 ≥8 位
              return typeof value === 'string' && value.length >= 8
            }
          },
          errorMessage: isEdit ? '如需修改密码，请输入至少 8 位' : '密码至少 8 位'
        }
      ]
    },
    nickname: {
      rules: [{ required: true, errorMessage: '昵称必填' }]
    }
  }
}

function applyRules() {
  // 变更 isEdit 后，重设 rules 并通知 uni-forms 生效
  editRules.value = makeRules(editDialog.isEdit)
  nextTick(() => {
    editFormRef.value?.setRules?.(editRules.value)
  })
}

function onPasswordBlur() {
  // 失焦时快速校验单字段（体验更直观）
  editFormRef.value?.validateField?.('password')
}

/* ========= 数据加载 ========= */
function fetchData() {
  const params = {
    page: query.page,
    page_size: query.page_size,
    username: query.username
  }
  // 仅当不显示已删除时才过滤 status=1；显示已删除则完全不传 status
  if (!query.include_deleted) params.status = 1

  request({
    url: '/cal_price/admin_user/',
    method: 'GET',
    data: params
  }).then(res => {
    list.value = res.items || []
    total.value = res.total || 0
  })
}


function resetQuery() {
  query.username = ''
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

/* ========= 弹窗开关 ========= */
function showEditDialog(row = null) {
  if (row) {
    editDialog.isEdit = true
    editDialog.form = { id: row.id, username: row.username, password: '', nickname: row.nickname, status: row.status }
  } else {
    editDialog.isEdit = false
    editDialog.form = { id: null, username: '', password: '', nickname: '', status: 1 }
  }
  applyRules()               // ★ 关键：打开前应用对应规则
  nextTick(() => editPopup.value.open())
}
function closeEditDialog() { editPopup.value.close() }

/* ========= 保存 ========= */
function saveUser() {
  editFormRef.value.validate().then(() => {
    const isEdit = editDialog.isEdit
    const apiUrl = isEdit ? `/cal_price/admin_user/${editDialog.form.id}` : '/cal_price/admin_user/'
    const method = isEdit ? 'PUT' : 'POST'
    const payload = { ...editDialog.form }

    // 编辑且密码空：不传 password，避免被后端当成“设为空”
    if (isEdit && !payload.password) delete payload.password

    request({ url: apiUrl, method, data: payload }).then(() => {
      uni.showToast({ title: isEdit ? '保存成功' : '新增成功', icon: 'success' })
      closeEditDialog()
      fetchData()
    })
  }).catch(() => {
    uni.showToast({ title: '请检查表单填写', icon: 'none' })
  })
}

/* ========= 删除 / 恢复 ========= */
function handleDelete(row) {
  uni.showModal({ title: '提示', content: '确定要删除该用户吗？' }).then(res => {
    if (res.confirm) {
      request({ url: `/cal_price/admin_user/${row.id}`, method: 'DELETE' }).then(() => {
        uni.showToast({ title: '已删除', icon: 'success' })
        fetchData()
      })
    }
  })
}
function handleRecover(row) {
  request({ url: `/cal_price/admin_user/${row.id}`, method: 'PUT', data: { status: 1 } }).then(() => {
    uni.showToast({ title: '已恢复', icon: 'success' })
    fetchData()
  })
}

onMounted(() => fetchData())
onPullDownRefresh(() => { fetchData(); uni.stopPullDownRefresh() })
</script>

<style>
.container { padding: 24rpx; background: #fafbfc; }
.search-bar { display: flex; flex-wrap: wrap; gap: 16rpx 24rpx; }
.search-bar .uni-forms-item { width: calc(50% - 12rpx); }
.btn-group { display: flex; flex-wrap: wrap; align-items: center; gap: 20rpx; margin-top: 12rpx; }
.switch-wrap { display: flex; align-items: center; gap: 8rpx; }
.switch-label { font-size: 24rpx; }

.table-head, .table-row {
  display: flex; align-items: flex-start;
  padding: 16rpx 20rpx; font-size: 26rpx; gap: 10rpx;
}
.table-head { font-weight: 600; background: #f2f3f5; }
.table-row:not(:last-child) { border-bottom: 1px solid #eee; }

.id { flex: 0 0 60px; }
.username { flex: 0 0 160px; }
.nickname { flex: 0 0 160px; }
.status { flex: 0 0 90px; text-align: center; }
.action { flex: 0 0 200px; display: flex; flex-wrap: wrap; gap: 12rpx; }

.pagination { margin: 32rpx 0; text-align: center; }
.edit-dialog { background: #fff; padding: 24rpx; border-radius: 12rpx; width: 700rpx; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 24rpx; margin-top: 18rpx; }
.picker { min-width: 110rpx; padding: 0 8rpx; color: #666; }
</style>
