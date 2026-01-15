<template>
  <view class="container">
    <!-- 区域规则列表 -->
    <view class="table-head">
      <text class="id">ID</text>
      <text class="channel">渠道</text>
      <text class="category">分类</text>
      <text class="region-type">区域类型</text>
      <text class="region-count">区域数</text>
      <text class="unit-rules">运费规则</text>
      <text class="delivery-rules">派送费规则</text>
      <text class="action">操作</text>
    </view>

    <scroll-view scroll-y style="max-height: 70vh">
      <view v-for="rule in regionRules" :key="rule.id" class="table-row">
        <text class="id">{{ rule.id }}</text>
        <text class="channel">{{ getChannelName(rule.channel) }}</text>
        <text class="category">{{ getCategoryName(rule.category_id) }}</text>
        <text class="region-type">{{ rule.regionType }}</text>
        <text class="region-count">{{ rule.regionIds.length }}</text>
        <view class="unit-rules">
          <RuleViewer :rules="rule.unit_price_rules" />
        </view>
        <view class="delivery-rules">
          <RuleViewer :rules="rule.delivery_fee_rules" />
        </view>
        <view class="action">
          <button size="mini" plain @click="editRule(rule)">编辑</button>
          <button size="mini" type="warn" plain @click="deleteRule(rule)">删除</button>
        </view>
      </view>
    </scroll-view>

    <!-- 新建按钮 -->
    <view class="footer">
      <button type="primary" @click="createRule">新建区域规则</button>
    </view>

    <!-- 编辑弹窗 -->
    <uni-popup ref="editPopup" type="center">
      <view class="editor-sheet">
        <RuleEditor
          v-model="editForm"
          :channelList="channelList"
          :categoryList="categoryList"
          @save="onSave"
          @cancel="closeEditPopup"
        />
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request } from '@/common/utils/request'
import RuleViewer from '@/components/RuleViewer.vue'
import RuleEditor from '@/components/RuleEditor.vue'

const regionRules = ref([])
const channelList = ref([])
const categoryList = ref([])

const editPopup = ref(null)
const editForm = ref({})

// 加载数据
async function loadData() {
  // 加载渠道和分类
  const [channelsRes, categoriesRes] = await Promise.all([
    request({ url: '/cal_price/channel_mgr/', method: 'POST', data: {} }),
    request({ url: '/cal_price/classify_mgr/', method: 'GET' })
  ])
  channelList.value = channelsRes?.data || []
  categoryList.value = categoriesRes?.data || []

  // 加载区域规则
  const rulesRes = await request({
    url: '/cal_price/region_rules/',
    method: 'GET'
  })
  regionRules.value = rulesRes?.data || []
}

// 工具函数
function getChannelName(code) {
  if (!code) return '全部'
  const c = channelList.value.find(item => item.channel_code === code)
  return c ? `${c.channel_code} - ${c.channel_name || ''}` : code
}

function getCategoryName(id) {
  if (!id || id === 0) return '全部'
  const c = categoryList.value.find(item => Number(item.category_id) === Number(id))
  return c ? c.main_category : id
}

// 交互
function createRule() {
  editForm.value = {
    channel: '',
    category_id: 0,
    region_rules: []
  }
  editPopup.value.open()
}

function editRule(rule) {
  editForm.value = { ...rule }
  editPopup.value.open()
}

function closeEditPopup() {
  editPopup.value.close()
}

async function onSave(payload) {
  const url = payload.id
    ? `/cal_price/region_rules/${payload.id}`
    : `/cal_price/region_rules/`
  const method = payload.id ? 'PUT' : 'POST'

  await request({ url, method, data: payload })
  uni.showToast({ title: '保存成功', icon: 'success' })
  closeEditPopup()
  loadData()
}

async function deleteRule(rule) {
  const res = await uni.showModal({ title: '提示', content: '确定要删除该规则吗？' })
  if (res.confirm) {
    await request({ url: `/cal_price/region_rules/${rule.id}`, method: 'DELETE' })
    uni.showToast({ title: '删除成功', icon: 'success' })
    loadData()
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.container {
  padding: 24rpx;
}

.table-head,
.table-row {
  display: flex;
  align-items: center;
  padding: 16rpx 20rpx;
  font-size: 26rpx;
  text-align: left;
  gap: 10rpx;
}

.table-head {
  font-weight: 600;
  background: #f2f3f5;
}

.table-row:not(:last-child) {
  border-bottom: 1px solid #eeeeee;
}

.id { flex: 0 0 50px; }
.channel { flex: 0 0 80px; }
.category { flex: 0 0 140px; }
.region-type { flex: 0 0 100px; }
.region-count { flex: 0 0 80px; }
.unit-rules,
.delivery-rules { flex: 1 1 300px; }
.action { flex: 0 0 170px; display: flex; flex-wrap: wrap; gap: 12rpx; }

.footer {
  margin-top: 32rpx;
  text-align: center;
}

.editor-sheet {
  width: 92vw;
  max-width: 1080px;
  max-height: 88vh;
  background:#fff;
  border-radius: 14rpx;
  overflow: auto;
  padding: 16rpx;
}
</style>