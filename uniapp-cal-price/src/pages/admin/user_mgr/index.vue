<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { request } from '@/common/utils/request.js'   // ✅ 引入封装
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
  category_id: 0,
  keyword: '',
  include_deleted: false
})

const editPopup = ref(null)
const editDialog = reactive({ form: { id: null, channel: '', category_id: 0 } })

/** 工具：JSON→数组 */
function toArr(val) {
  if (Array.isArray(val)) return val
  if (typeof val === 'string') {
    try { const a = JSON.parse(val); return Array.isArray(a) ? a : [] } catch { return [] }
  }
  return []
}

/** 渠道/分类获取 */
async function fetchChannelList() {
  const res = await request({ url: '/cal_price/channel_mgr/', method: 'POST' })
  channelList.value = res.data || []
}
async function fetchCategoryList() {
  const res = await request({ url: '/cal_price/classify_mgr/', method: 'GET' })
  categoryList.value = res.data || []
}

function getChannelName(code) {
  const c = channelList.value.find(item => item.channel_code === code)
  return c ? `${c.channel_code} - ${c.channel_name}` : code
}
function getCategoryName(id) {
  if (!id || id === 0) return '全部'
  const c = categoryList.value.find(item => Number(item.category_id) === Number(id))
  return c ? c.main_category : id
}

/** 生命周期 */
onMounted(() => { fetchChannelList(); fetchCategoryList(); fetchData() })

/** 列表请求 */
async function fetchData() {
  const res = await request({
    url: '/cal_price/pricing_mgr/',
    method: 'GET',
    data: { ...query, include_deleted: query.include_deleted ? 1 : 0 }
  })
  const arr = res.data || []
  list.value = arr.map(item => ({
    ...item,
    unit_price_rules: toArr(item.unit_price_rules),
    surcharge_fee_rules: toArr(item.surcharge_fee_rules),
    delivery_fee_rules: toArr(item.delivery_fee_rules),
  }))
  total.value = res.total || 0
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

/** ==== 渠道选择 ==== */
const channelOptions = computed(() => [
  { channel_code: '', channel_name: '', display: '全部' },
  ...(channelList.value || []).map(x => ({ ...x, display: `${x.channel_code} - ${x.channel_name || ''}` }))
])
const channelIndex = computed(() =>
  channelOptions.value.findIndex(opt => String(opt.channel_code) === String(query.channel)) || 0
)
const channelDisplay = computed(() => channelOptions.value[channelIndex.value]?.display || '全部')
function onChannelChange(e) { query.channel = channelOptions.value[e.detail.value]?.channel_code || '' }

/** ==== 分类选择 ==== */
const categoryOptions = computed(() => [
  { category_id: 0, main_category: '全部' },
  ...(categoryList.value || [])
])
const categoryIndex = computed(() =>
  categoryOptions.value.findIndex(opt => Number(opt.category_id) === Number(query.category_id)) || 0
)
const categoryDisplay = computed(() => categoryOptions.value[categoryIndex.value]?.main_category || '全部')
function onCategoryChange(e) { query.category_id = categoryOptions.value[e.detail.value]?.category_id || 0 }

/** 其他交互 */
function onIncludeDeletedChange(e) { query.include_deleted = !!e.detail.value; fetchData() }

/** 编辑弹窗 */
function showEditDialog(row = null) {
  if (row) {
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
function closeEditDialog() { editPopup.value.close() }

/** 保存 */
async function onSaveFromChild(payload) {
  const url = payload.id
    ? `/cal_price/pricing_mgr/${payload.id}`
    : `/cal_price/pricing_mgr/`
  const method = payload.id ? 'PUT' : 'POST'

  await request({ url, method, data: payload })
  uni.showToast({ title: '保存成功', icon: 'success' })
  closeEditDialog()
  fetchData()
}

/** 删除/恢复 */
async function handleDelete(row) {
  const [err, res] = await uni.showModal({ title: '提示', content: '确定要删除该规则吗？' })
  if (res?.confirm) {
    await request({ url: `/cal_price/pricing_mgr/${row.id}`, method: 'DELETE' })
    uni.showToast({ title: '删除成功', icon: 'success' })
    fetchData()
  }
}
async function handleRecover(row) {
  await request({ url: `/cal_price/pricing_mgr/recover/${row.id}`, method: 'POST' })
  uni.showToast({ title: '恢复成功', icon: 'success' })
  fetchData()
}

/** 下拉刷新 */
onPullDownRefresh(() => { fetchData(); uni.stopPullDownRefresh() })
</script>
