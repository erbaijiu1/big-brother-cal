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
  form: { id: null, channel_code: '', channel_name: '', remark: '' }
})
const editFormRef = ref(null)
const editRules = {
  channel_code: [{ required: true, errorMessage: '渠道编码必填' }],
  channel_name: [{ required: true, errorMessage: '渠道名称必填' }],
  remark: []
}

onMounted(() => { fetchData(); preloadNameMaps() })

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
    return { ...row, surcharge_rules: rules }
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
    editDialog.form = { ...row }
  } else {
    editDialog.isEdit = false
    editDialog.form = { id: null, channel_code: '', channel_name: '', remark: '' }
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
.name   { flex: 0 0 20%; }
.surcharge { flex: 0 0 30%; }   /* 新增 */
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
</style>
