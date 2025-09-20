<template>
  <view class="page">
    <!-- 类别列表 -->
    <uni-table border stripe>
      <uni-tr>
        <uni-th width="180">名称</uni-th>
        <uni-th width="100">子区数</uni-th>
        <uni-th>子区（按行政区分组展示）</uni-th>
        <uni-th width="240">操作</uni-th>
      </uni-tr>

      <uni-tr v-for="c in cats" :key="c.id">
        <uni-td><text class="cat-name">{{ c.name }}</text></uni-td>
        <uni-td><text>{{ c.sub_ids.length }}</text></uni-td>
        <uni-td>
          <text class="group-text">
            {{ groupedTextFor(c) || '（未配置子区）' }}
          </text>
        </uni-td>
        <uni-td>
          <button size="mini" class="mr-1" @click="openEdit(c)">编辑</button>
          <button size="mini" type="primary" class="mr-1" @click="openBind(c)">配置地区</button>
          <button size="mini" type="warn" @click="remove(c.id)">删除</button>
        </uni-td>
      </uni-tr>
    </uni-table>

    <!-- 新增类别按钮 -->
    <button class="add-btn" type="primary" @click="openAdd">新增类别</button>

    <!-- 新增 / 编辑 弹窗 -->
    <uni-popup ref="editPop" type="dialog" :style="{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }">
      <view class="form" style="background-color: white; border-radius: 8rpx; padding: 32rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.1);">
        <input v-model.trim="form.name" placeholder="类别名称" class="input" />
        <view class="actions">
          <button size="mini" @click="editPop.close">取消</button>
          <button size="mini" type="primary" @click="saveCat">保存</button>
        </view>
      </view>
    </uni-popup>

    <!-- 绑定子区 抽屉 -->
    <uni-drawer ref="drawer" mode="right" width="70%">
      <view class="drawer-body">
        <input v-model="keyword" placeholder="搜索子区" class="search" />
        <!-- 可选子区 -->
        <scroll-view scroll-y class="list">
          <view v-for="sub in filteredUnbind" :key="sub.id" class="row" @click="select(sub)">
            <checkbox :checked="false" />
            <text>{{ sub.full }}</text>
          </view>
        </scroll-view>
        <!-- 已绑定子区 -->
        <scroll-view scroll-y class="list">
          <view v-for="sub in bindList" :key="sub.id" class="row bind">
            <checkbox :checked="true" />
            <text>{{ sub.full }}</text>
            <button size="mini" type="warn" @click.stop="unselect(sub)">×</button>
          </view>
        </scroll-view>
        <button type="primary" class="save-btn" @click="saveBind">保存</button>
      </view>
    </uni-drawer>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCats, addCat, updCat, delCat, bindSubs } from '@/api/areaCategory'
import { getDistricts } from '@/api/district'

/* ------------------ 数据 ------------------ */
const cats    = ref([])     // 类别列表
// 全部子区：包含区名与子区名，便于分组
// { id, district_id, district_cn, sub_cn, full }
const subsAll = ref([])

/* 建立 subId -> 详细信息 的映射，O(1) 查询 */
const subDetailMap = computed(() => {
  const m = new Map()
  subsAll.value.forEach(s => m.set(s.id, s))
  return m
})

/* 把类别 sub_ids 转为“区（子区…）; 区（子区…）”的字符串 */
function groupedTextFor (cat) {
  if (!cat?.sub_ids?.length) return ''
  // 分组：district_cn -> [sub names]
  const groups = new Map()
  cat.sub_ids.forEach(id => {
    const detail = subDetailMap.value.get(id)
    if (!detail) return
    if (!groups.has(detail.district_cn)) groups.set(detail.district_cn, [])
    groups.get(detail.district_cn).push(detail.sub_cn)
  })
  // 字典序可选：让展示稳定
  const parts = []
  Array.from(groups.keys()).sort().forEach(dName => {
    const subs = groups.get(dName).sort()
    parts.push(`${dName}（${subs.join('、')}）`)
  })
  return parts.join('； ')
}

/* 弹窗 / 抽屉 */
const editPop = ref(null)
const drawer  = ref(null)

/* ------------------ 新增 / 编辑类别 ------------------ */
const form    = ref({ name: '' })
const editing = ref(null)   // null -> 新增

function openAdd () {
  editing.value = null
  form.value = { name: '' }
  editPop.value.open()
}

function openEdit (c) {
  editing.value = c.id
  form.value = { name: c.name }
  editPop.value.open()
}

function saveCat () {
  const req = editing.value ? updCat(editing.value, form.value) : addCat(form.value)
  req.then(() => {
    uni.showToast({ title: '已保存' })
    editPop.value.close()
    fetchCats()
  })
}

function remove (id) {
  uni.showModal({ title: '删除', content: '确认删除？', success: res => {
    if (res.confirm) delCat(id).then(fetchCats)
  }})
}

/* ------------------ 绑定子区 ------------------ */
const currentCat = ref(null)
const bindList   = ref([])
const keyword    = ref('')

const filteredUnbind = computed(() => subsAll.value
  .filter(s => !bindList.value.find(b => b.id === s.id))
  .filter(s => s.full.includes(keyword.value)))

function openBind (cat) {
  currentCat.value = cat
  bindList.value = subsAll.value.filter(s => cat.sub_ids.includes(s.id))
  drawer.value.open()
}

function select (sub)   { bindList.value.push(sub) }
function unselect (sub) { bindList.value = bindList.value.filter(s => s.id !== sub.id) }

function saveBind () {
  const ids = bindList.value.map(s => s.id)
  // 后端若要求 Body: { sub_ids: [...] }
  bindSubs(currentCat.value.id, { sub_ids: ids }).then(() => {
    uni.showToast({ title: '已保存' })
    drawer.value.close()
    fetchCats()
  })
}

/* ------------------ 初始化 ------------------ */
function fetchCats () {
  getCats().then(res => (cats.value = res.data))
}

function fetchSubs () {
  getDistricts().then(res => {
    subsAll.value = res.data.flatMap(d =>
      d.subs.map(s => ({
        id: s.id,
        district_id: d.id,
        district_cn: d.name_cn,
        sub_cn: s.name_cn,
        full: `${d.name_cn} · ${s.name_cn}`
      }))
    )
  })
}

onMounted(() => { fetchCats(); fetchSubs() })
</script>

<style scoped>
.page { padding: 24rpx; }
.add-btn { margin-top: 32rpx; }
.cat-name { font-weight: 600; }

/* 分组文案 */
.group-text {
  display: inline-block;
  white-space: pre-wrap;
  word-break: break-all;
  color: #374151;
  line-height: 1.8;
}

.form { padding: 32rpx; width: 500rpx; }
.input { border: 1px solid #ccc; border-radius: 8rpx; padding: 16rpx; width: 100%; margin-bottom: 24rpx; }
.actions { display: flex; justify-content: flex-end; gap: 24rpx; }

.drawer-body { display: flex; flex-direction: column; height: 100%; padding: 24rpx; gap: 24rpx; }
.list { flex: 1; border: 1px solid #ddd; border-radius: 8rpx; overflow-y: auto; }
.row { display: flex; align-items: center; padding: 12rpx 16rpx; gap: 12rpx; }
.bind { background: #f5faff; }
.save-btn { width: 100%; margin-top: 16rpx; }
.search { border: 1px solid #ccc; border-radius: 8rpx; padding: 12rpx 16rpx; width: 100%; }
.mr-1 { margin-right: 8rpx; }
</style>
