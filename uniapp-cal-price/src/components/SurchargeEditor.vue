<template>
  <uni-popup ref="popup" type="dialog">
    <view class="dlg">
      <view class="dlg-title">附加费配置</view>

      <!-- 规则列表 -->
      <scroll-view scroll-y class="rule-list">
        <view v-if="form.surcharges.length === 0" class="empty">还没有附加费，点击下方【新增附加费】</view>

        <view v-for="(r, idx) in form.surcharges" :key="idx" class="rule-item">
          <view class="rule-head">
            <view class="rule-title">
              <text class="key">{{ r.key }}</text>
              <text class="title">（{{ r.title }}）</text>
              <uni-tag :text="r.type==='global' ? '全局' : '区域'" :type="r.type==='global' ? 'success' : 'primary'"
                size="mini" />
            </view>
            <view class="rule-actions">
              <button size="mini" plain @click="editRule(idx)">编辑</button>
              <button size="mini" type="warn" plain @click="removeRule(idx)">删</button>
            </view>
          </view>

          <view class="rule-body">
            <view class="row"><text class="lbl">价格</text><text>¥{{ r.price }}</text></view>
            <view class="row"
              v-if="r.conditions && (r.conditions.volume_range || r.conditions.weight_range || r.conditions.vehicle)">
              <text class="lbl">条件</text>
              <text>
                <template v-if="r.conditions.volume_range">体积: {{ r.conditions.volume_range }}；</template>
                <template v-if="r.conditions.weight_range">重量: {{ r.conditions.weight_range }}；</template>
                <template v-if="r.conditions.vehicle">车型: {{ r.conditions.vehicle }}；</template>
              </text>
            </view>
            <view class="row"><text class="lbl">合并</text><text>{{ r.combine || 'sum' }}</text></view>

            <template v-if="r.type==='area'">
              <!-- <view class="row"><text class="lbl">解析</text><text>{{ r.resolve || 'runtime' }}</text></view> -->
              <view class="row"><text class="lbl">范围</text>
                <text>
                  <template v-if="r.scope?.mode==='area_category'">按自定义区</template>
                  <template v-else-if="r.scope?.mode==='district'">按行政区</template>
                  <template v-else-if="r.scope?.mode==='sub_district'">按子区</template>
                </text>
              </view>
              <view class="row" v-if="r.scope?.ids?.length">
                <text class="lbl">已选</text>
                <text class="wrap">{{ renderScopeNames(r) }}</text>
              </view>
              <view class="row" v-if="r.sub_ids_snapshot?.length">
                <!-- <text class="lbl">快照</text> -->
                <text class="wrap">子区共 {{ r.sub_ids_snapshot.length }} 个</text>
              </view>
            </template>
          </view>
        </view>
      </scroll-view>

      <!-- 底部操作 -->
      <view class="dlg-actions">
        <button @click="popup.close()">取消</button>
        <button class="add" @click="openEditor()">新增附加费</button>
        <button type="primary" @click="save()">保存</button>
      </view>

      <!-- 新增/编辑 规则弹层 -->
      <uni-popup ref="innerPop" type="dialog">
        <view class="inner">
          <view class="inner-title">{{ editingIdx===null ? '新增附加费' : '编辑附加费' }}</view>

          <uni-forms :modelValue="ruleForm" ref="ruleFormRef" label-width="90px">
            <!-- <uni-forms-item name="key" label="唯一键">
              <uni-easyinput v-model.trim="ruleForm.key" placeholder="如 sea_crossing_fee_van"/>
            </uni-forms-item> -->
            <uni-forms-item name="title" label="标题">
              <uni-easyinput v-model.trim="ruleForm.title" placeholder="展示名称" />
            </uni-forms-item>

            <uni-forms-item name="type" label="类型">
              <picker :range="typeOptions" range-key="label" @change="onTypeChange">
                <view class="picker">{{ typeOptions.find(v=>v.value===ruleForm.type)?.label }}</view>
              </picker>
            </uni-forms-item>

            <uni-forms-item name="price" label="价格">
              <uni-easyinput v-model.number="ruleForm.price" type="number" placeholder="整数，单位元" />
            </uni-forms-item>

            <uni-forms-item name="combine" label="合并">
              <picker :range="combineOptions" range-key="label" @change="onCombineChange">
                <view class="picker">{{ combineOptions.find(v=>v.value===ruleForm.combine)?.label }}</view>
              </picker>
            </uni-forms-item>

            <uni-forms-item label="条件(选填)">
              <view class="cond">
                <uni-easyinput v-model.trim="ruleForm.conditions.volume_range" placeholder="体积范围 例: 0-0.2" />
                <uni-easyinput v-model.trim="ruleForm.conditions.weight_range" placeholder="重量范围 例: 0-40" />
                <uni-easyinput v-model.trim="ruleForm.conditions.vehicle" placeholder="车型 例: van/truck" />
              </view>
            </uni-forms-item>

            <!-- 区域相关 -->
            <view v-if="ruleForm.type==='area'">
              <!-- <uni-forms-item name="resolve" label="解析">
                <picker :range="resolveOptions" range-key="label" @change="onResolveChange">
                  <view class="picker">{{ resolveOptions.find(v=>v.value===ruleForm.resolve)?.label }}</view>
                </picker>
              </uni-forms-item> -->

              <uni-forms-item name="scopeMode" label="关联到">
                <picker :range="scopeModeOptions" range-key="label" @change="onScopeModeChange">
                  <view class="picker">{{ scopeModeOptions.find(v=>v.value===ruleForm.scope.mode)?.label }}</view>
                </picker>
              </uni-forms-item>

              <view class="chooser">
                <view class="chooser-head">
                  <input v-model.trim="keyword" class="search" placeholder="搜索" />
                </view>

                <!-- 用 checkbox-group 管理 pickedIds -->
                <checkbox-group :value="pickedIds" @change="onPickChange">
                  <scroll-view scroll-y class="chooser-list">
                    <label v-for="opt in filteredOptions" :key="opt.id" class="opt">
                      <checkbox :value="String(opt.id)" :checked="pickedIds.includes(String(opt.id))" />
                      <text class="name">{{ opt.name }}</text>
                      <text v-if="opt.parent" class="parent">（{{ opt.parent }}）</text>
                    </label>
                  </scroll-view>
                </checkbox-group>

                <!-- 统计条 -->
<view class="picked-bar">
  <text>已选：{{ pickedIds.length }} / {{ totalOptionsCount }} 个</text>
  <view class="picked-actions">
    <text class="link" @click="toggleShowPicked">{{ showPicked ? '收起' : '查看' }}</text>
    <text class="link danger" v-if="pickedIds.length" @click="clearPicked">清空</text>
  </view>
</view>

<!-- 已选项（可展开为标签，支持单个移除） -->
<view v-if="showPicked && pickedList.length" class="picked-chips">
  <view class="chip" v-for="item in pickedList" :key="item.id">
    <text class="chip-text">{{ item.name }}</text>
    <text class="chip-close" @click="removePicked(item.id)">×</text>
  </view>
</view>

              </view>


            </view>
          </uni-forms>

          <view class="inner-actions">
            <button @click="innerPop.close()">取消</button>
            <button type="primary" @click="commitRule()">确定</button>
          </view>
        </view>
      </uni-popup>
    </view>
  </uni-popup>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { getChannelSurcharges, saveChannelSurcharges, getAreaCategories, getDistricts } from '@/api/channel'

const emit = defineEmits(['saved'])


const popup = ref(null)
const innerPop = ref(null)
const ruleFormRef = ref(null)

const chanId = ref(null)
const form = reactive({ surcharges: [] })

// 下拉选项
const typeOptions = [
  { label: '全局（与区域无关）', value: 'global' },
  { label: '区域（与区域相关）', value: 'area' }
]
const combineOptions = [
  { label: '叠加(sum)', value: 'sum' },
  { label: '取最大(max)', value: 'max' },
  { label: '取第一条(first)', value: 'first' }
]
const resolveOptions = [
  { label: '运行时解析(runtime)', value: 'runtime' },
  { label: '保存时快照(snapshot)', value: 'snapshot' }
]
const scopeModeOptions = [
  { label: '自定义区', value: 'area_category' },
  { label: '行政区', value: 'district' },
  { label: '子区', value: 'sub_district' },
]

// 区域选择数据
const areaCats = ref([])      // [{id,name}]
const districts = ref([])     // [{id,name_cn,subs:[{id,name_cn}]}]
const subFlat = ref([])       // [{id,name,parent}]
const distFlat = ref([])      // [{id,name}]

// 选项过滤
const keyword = ref('')
const options = computed(() => {
  const mode = ruleForm.scope.mode
  if (mode === 'area_category') return areaCats.value.map(i => ({ id: i.id, name: i.name }))
  if (mode === 'district')     return distFlat.value
  return subFlat.value
})
const filteredOptions = computed(() => {
  if (!keyword.value) return options.value
  return options.value.filter(o => o.name.includes(keyword.value) || (o.parent && o.parent.includes(keyword.value)))
})
const pickedIds = ref([])

// 正在编辑的 rule
const editingIdx = ref(null)
const ruleForm = reactive({
  key: '', title: '', type: 'global',
  price: 0, combine: 'sum',
  conditions: { volume_range: '', weight_range: '', vehicle: '' },
  resolve: 'runtime',
  scope: { mode: 'area_category', ids: [] },
  sub_ids_snapshot: null,
})

// ====== 外部调用：打开弹窗 ======
function open(id, initialPayload = null) {
  chanId.value = id
  // 预加载区域数据
  preloadOptions()
  // 读取渠道已有 surcharges
  if (initialPayload && initialPayload.surcharges) {
    form.surcharges = JSON.parse(JSON.stringify(initialPayload.surcharges))
  } else {
    getChannelSurcharges(id).then(res => {
      console.log('getChannelSurcharges ->', res)
      form.surcharges = (res?.surcharges) || []
    })
  }
  popup.value.open()
}

// ====== 保存到后端 ======
function save() {
  saveChannelSurcharges(chanId.value, { surcharges: form.surcharges }).then(() => {
    uni.showToast({ title: '已保存', icon: 'success' })
    popup.value.close()
    // 通知父组件刷新
    emit('saved')
  })
}

// ====== 列表操作 ======
function openEditor() {
  editingIdx.value = null
  resetRuleForm()
  innerPop.value.open()
}

function editRule(idx) {
  editingIdx.value = idx
  Object.assign(ruleForm, JSON.parse(JSON.stringify(form.surcharges[idx])))
  // pickedIds.value = (ruleForm.scope?.ids || []).slice()
  console.log("scope:", ruleForm.scope?.ids)
  pickedIds.value = (ruleForm.scope?.ids || []).map(String)

  innerPop.value.open()
}

function onPickChange(e) {
  // 可见项（当前过滤结果）
  const visible = new Set(filteredOptions.value.map(o => String(o.id)))
  // 可见区的新勾选结果
  const nextVisibleChecked = new Set((e.detail.value || []).map(String))

  // 先从旧的选择集开始
  const selected = new Set(pickedIds.value.map(String))

  // 1) 处理可见区的“取消勾选”：可见但没在 nextVisibleChecked 里的，去掉
  for (const id of visible) {
    if (!nextVisibleChecked.has(id)) selected.delete(id)
  }
  // 2) 处理可见区的“新增勾选”：加上
  for (const id of nextVisibleChecked) {
    selected.add(id)
  }

  pickedIds.value = Array.from(selected) // 仍然是 string[]
}

function removeRule(idx) {
  uni.showModal({ title: '删除', content: '确认删除该附加费？' }).then(res => {
    if (res.confirm) form.surcharges.splice(idx, 1)
  })
}


function commitRule() {
  // 简单校验
  if (!ruleForm.title) {
    return uni.showToast({ title: '请填写标题', icon: 'none' })
  }
  console.log(ruleForm.type, pickedIds.value.length)
  if (ruleForm.type === 'area' && pickedIds.value.length === 0) {
    return uni.showToast({ title: '请选择关联范围', icon: 'none' })
  }

  const data = JSON.parse(JSON.stringify(ruleForm))

  // 保存时把 scope.ids 填进去
  if (data.type === 'area') {
    data.scope.ids = pickedIds.value.map(v => Number(v)) // 转成数字数组
  }

  if (editingIdx.value === null) {
    form.surcharges.push(data)
  } else {
    form.surcharges.splice(editingIdx.value, 1, data)
  }

  innerPop.value.close()
}


// ====== 小工具 / 事件 ======
function renderScopeNames(r) {
  const ids = r.scope?.ids || []
  const mode = r.scope?.mode
  const map = new Map()
  if (mode === 'area_category') {
    areaCats.value.forEach(i => map.set(i.id, i.name))
  } else if (mode === 'district') {
    distFlat.value.forEach(i => map.set(i.id, i.name))
  } else {
    subFlat.value.forEach(i => map.set(i.id, `${i.parent}·${i.name}`))
  }
  return ids.map(id => map.get(id)).filter(Boolean).join('、')
}

function onTypeChange(e) {
  ruleForm.type = typeOptions[e.detail.value].value
}
function onCombineChange(e) {
  ruleForm.combine = combineOptions[e.detail.value].value
}
function onResolveChange(e) {
  ruleForm.resolve = resolveOptions[e.detail.value].value
}
function onScopeModeChange(e) {
  const v = scopeModeOptions[e.detail.value].value
  ruleForm.scope.mode = v
  pickedIds.value = []
}

function resetRuleForm() {
  Object.assign(ruleForm, {
    key: '', title: '', type: 'global', price: 0, combine: 'sum',
    conditions: { volume_range: '', weight_range: '', vehicle: '' },
    resolve: 'runtime', scope: { mode: 'area_category', ids: [] }, sub_ids_snapshot: null
  })
  pickedIds.value = []
}

// 选项数据预加载 & 扁平化
function preloadOptions() {
  getAreaCategories().then(res => { areaCats.value = res || [] })
  getDistricts().then(res => {
    // const ds = res.data || []
    const ds = res || []
    districts.value = ds
    distFlat.value = ds.map(d => ({ id: d.id, name: d.name_cn }))
    subFlat.value = ds.flatMap(d => (d.subs||[]).map(s => ({ id: s.id, name: s.name_cn, parent: d.name_cn })))
  })
}

// ====== 对外暴露 ======
defineExpose({ open })

// 展开/收起与清空
const showPicked = ref(false)
function toggleShowPicked() { showPicked.value = !showPicked.value }
function clearPicked() { pickedIds.value = [] }
function removePicked(id) {
  pickedIds.value = pickedIds.value.filter(v => String(v) !== String(id))
}

// 当前模式下的“全部选项”字典 & 总数（不受搜索影响）
const activeOptionMap = computed(() => {
  const m = new Map()
  if (ruleForm.scope.mode === 'area_category') {
    for (const i of areaCats.value) m.set(String(i.id), i.name)
  } else if (ruleForm.scope.mode === 'district') {
    for (const i of distFlat.value) m.set(String(i.id), i.name)
  } else {
    for (const i of subFlat.value) {
      const nm = i.parent ? `${i.parent}·${i.name}` : i.name
      m.set(String(i.id), nm)
    }
  }
  return m
})

const totalOptionsCount = computed(() => {
  if (ruleForm.scope.mode === 'area_category') return areaCats.value.length
  if (ruleForm.scope.mode === 'district') return distFlat.value.length
  return subFlat.value.length
})

// 已选列表（用于展示标签）
const pickedList = computed(() =>
  pickedIds.value.map(id => ({
    id: String(id),
    name: activeOptionMap.value.get(String(id)) || String(id),
  }))
)

</script>

<style scoped>
.dlg { width: 860rpx; background:#fff; border-radius:16rpx; padding:24rpx; }
.dlg-title { font-size:32rpx; font-weight:600; margin-bottom:16rpx; text-align:center; }

.rule-list { max-height: 60vh; }
.empty { color:#999; text-align:center; padding:40rpx 0; }

.rule-item { border:1px solid #eee; border-radius:12rpx; padding:16rpx; margin-bottom:16rpx; background:#fafafa; }
.rule-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8rpx; }
.rule-title .key { font-weight:600; margin-right:8rpx; }
.rule-title .title { color:#666; }
.rule-actions { display:flex; gap:12rpx; }

.rule-body .row { display:flex; gap:12rpx; margin:6rpx 0; }
.rule-body .lbl { width:100rpx; color:#666; }
.rule-body .wrap { white-space:normal; word-break:break-all; }

.dlg-actions { display:flex; justify-content:flex-end; gap:16rpx; margin-top:14rpx; }
.dlg-actions .add { background:#f6f7fb; }

.inner { width: 90%; height: 90%;  background:#fff; border-radius:16rpx; padding:20rpx; overflow: auto;}
.inner-title { font-size:28rpx; font-weight:600; margin-bottom:10rpx; text-align:center; }
.picker { padding: 8rpx 12rpx; color:#666; min-height: 60rpx; display:flex; align-items:center; border:1px solid #eee; border-radius:8rpx; }
.cond { display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 8rpx; }
.chooser { margin-top:8rpx; }
.chooser-head { display:flex; }
.search { border:1px solid #ddd; border-radius:8rpx; padding:10rpx 12rpx; width:100%; }
.chooser-list { max-height: 40vh; border:1px solid #eee; border-radius:8rpx; margin-top:8rpx; }
.opt { display:flex; align-items:center; gap:10rpx; padding:10rpx 12rpx; }
.opt + .opt { border-top:1px dashed #f0f0f0; }
.opt .parent { color:#999; }
.picked { margin-top:6rpx; color:#666; }
.inner-actions { display:flex; justify-content:flex-end; gap:16rpx; margin-top:12rpx; }

.picked-bar {
  display:flex; justify-content:space-between; align-items:center;
  margin-top:10rpx; color:#666;
}
.picked-actions { display:flex; gap:20rpx; }
.link { color:#1677ff; }
.link.danger { color:#ff4d4f; }

.picked-chips {
  display:flex; flex-wrap:wrap; gap:10rpx; margin-top:8rpx;
}
.chip {
  display:inline-flex; align-items:center; gap:8rpx;
  padding:6rpx 10rpx; border:1px solid #e5e6eb; border-radius:999px; background:#fafafa;
}
.chip-text { max-width: 420rpx; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.chip-close { padding:0 4rpx; font-weight:600; }


</style>
