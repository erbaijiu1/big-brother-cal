<template>
  <view class="page">
    <!-- 类别列表 -->
    <uni-table border stripe>
      <uni-tr>
        <uni-th width="180">名称</uni-th>
        <uni-th width="100">子区数</uni-th>
        <uni-th width="200">操作</uni-th>
      </uni-tr>
      <uni-tr v-for="c in cats" :key="c.id">
        <uni-td>{{ c.name }}</uni-td>
        <uni-td>{{ c.sub_ids.length }}</uni-td>
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
    <uni-popup ref="editPop" type="dialog">
      <view class="form">
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
const subsAll = ref([])     // 全部子区，带 full 文本

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
  const req = editing.value ? updCat(editing.value, form.value)
                           : addCat(form.value)
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
const currentCat = ref(null) // 当前操作的类别对象
const bindList   = ref([])   // 已选子区
const keyword    = ref('')

const filteredUnbind = computed(() => subsAll.value
  .filter(s => !bindList.value.find(b => b.id === s.id))
  .filter(s => s.full.includes(keyword.value)))

function openBind (cat) {
  currentCat.value = cat
  // 初始化已绑定
  bindList.value = subsAll.value.filter(s => cat.sub_ids.includes(s.id))
  drawer.value.open()
}

function select (sub)   { bindList.value.push(sub) }
function unselect (sub) { bindList.value = bindList.value.filter(s => s.id !== sub.id) }

function saveBind () {
  const ids = bindList.value.map(s => s.id)
  bindSubs(currentCat.value.id, ids).then(() => {
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
      d.subs.map(s => ({ id: s.id, full: `${d.name_cn} · ${s.name_cn}` }))
    )
  })
}

onMounted(() => { fetchCats(); fetchSubs() })
</script>

<style scoped>
.page { padding: 24rpx; }
.add-btn { margin-top: 32rpx; }
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
