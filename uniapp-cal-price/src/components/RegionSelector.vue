<template>
  <view class="region-selector">
    <!-- 区域类型选择 -->
    <uni-segmented-control
      v-if="!hideTabs"
      :current="currentTab"
      :values="tabs"
      style-type="text"
      @clickItem="onTabChange"
    />
    
    <!-- 类别区域 -->
    <view v-show="currentTab === 0" class="tab-content">
      <view class="search-box">
        <uni-easyinput
          v-model="categoryKeyword"
          placeholder="搜索类别"
          suffixIcon="search"
          @iconClick="loadCategories"
        />
      </view>
      <scroll-view scroll-y class="list">
        <view v-for="cat in filteredCategories" :key="cat.id" class="list-item">
          <checkbox-group @change="(e) => onCategoryChange(e, cat.id)">
            <label class="checkbox-label">
              <checkbox :value="cat.id" :checked="selectedCategoryIds.includes(cat.id)" />
              <text>{{ cat.name }}</text>
            </label>
          </checkbox-group>
        </view>
      </scroll-view>
    </view>
    
    <!-- 行政区区域 -->
    <view v-show="currentTab === 1" class="tab-content">
      <view class="search-box">
        <uni-easyinput
          v-model="districtKeyword"
          placeholder="搜索行政区"
          suffixIcon="search"
          @iconClick="loadDistricts"
        />
      </view>
      <scroll-view scroll-y class="list">
        <view v-for="dist in filteredDistricts" :key="dist.id" class="list-item">
          <checkbox-group @change="(e) => onDistrictChange(e, dist.id)">
            <label class="checkbox-label">
              <checkbox :value="dist.id" :checked="selectedDistrictIds.includes(dist.id)" />
              <text>{{ dist.name_cn }} ({{ dist.name_en }})</text>
            </label>
          </checkbox-group>
        </view>
      </scroll-view>
    </view>
    
    <!-- 子区区域 -->
    <view v-show="currentTab === 2" class="tab-content">
      <view class="search-box">
        <uni-easyinput
          v-model="subDistrictKeyword"
          placeholder="搜索子区"
          suffixIcon="search"
          @iconClick="loadDistricts"
        />
      </view>

      <!-- 快捷操作栏 -->
      <view class="quick-actions">
        <button size="mini" type="primary" plain @click="selectAllSubs">全选</button>
        <button size="mini" type="warn" plain @click="selectRemoteSubs">全选偏远</button>
        <button size="mini" type="default" plain @click="invertSubSelection">反选</button>
      </view>

      <scroll-view scroll-y class="list">
        <view v-for="sub in filteredSubDistricts" :key="sub.id" class="list-item">
          <checkbox-group @change="(e) => onSubDistrictChange(e, sub.id)">
            <label class="checkbox-label">
              <checkbox :value="sub.id" :checked="selectedSubDistrictIds.includes(sub.id)" />
              <text>{{ sub.name_cn }} ({{ sub.parent_name }})</text>
            </label>
          </checkbox-group>
        </view>
      </scroll-view>
    </view>
    
    <!-- 已选区域显示 -->
    <view class="selected-summary" v-if="selectedCount > 0">
      <text>已选 {{ selectedCount }} 个区域</text>
      <button size="mini" @click="clearSelection">清空</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getCats } from '@/api/areaCategory'
import { getDistricts } from '@/api/district'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  regionType: {
    type: String,
    default: 'category' // 'category' | 'district' | 'sub_district'
  },
  hideTabs: {
    type: Boolean,
    default: false
  },
  exclusiveType: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'update:regionType'])

const tabs = ['类别', '行政区', '子区']
const currentTab = ref(0)
const onTabChange = (e) => {
  if (typeof e === 'number') {
    currentTab.value = e
  } else if (e && e.currentIndex !== undefined) {
    currentTab.value = e.currentIndex
  }
}


const categories = ref([])
const districts = ref([])

const categoryKeyword = ref('')
const districtKeyword = ref('')
const subDistrictKeyword = ref('')

const selectedCategoryIds = ref([])
const selectedDistrictIds = ref([])
const selectedSubDistrictIds = ref([])

// 根据当前选项卡设置区域类型
watch(currentTab, (tab) => {
  const typeMap = { 0: 'category', 1: 'district', 2: 'sub_district' }
  emit('update:regionType', typeMap[tab])
  
  // 如果是独占模式，切换tab时触发一次emit，以便清空其他类型的选择
  if (props.exclusiveType) {
    emitSelection()
  }
})

// 过滤列表
const filteredCategories = computed(() => {
  const kw = categoryKeyword.value.trim().toLowerCase()
  if (!kw) return categories.value
  return categories.value.filter(cat => 
    cat.name.toLowerCase().includes(kw)
  )
})

const filteredDistricts = computed(() => {
  const kw = districtKeyword.value.trim().toLowerCase()
  if (!kw) return districts.value
  return districts.value.filter(dist => 
    dist.name_cn.toLowerCase().includes(kw) ||
    dist.name_en.toLowerCase().includes(kw)
  )
})

const filteredSubDistricts = computed(() => {
  // Flatten sub-districts
  const flatSubs = districts.value.flatMap(d => 
    (d.subs || []).map(s => ({
      ...s,
      parent_name: d.name_cn,
      parent_en: d.name_en
    }))
  )
  
  const kw = subDistrictKeyword.value.trim().toLowerCase()
  if (!kw) return flatSubs
  return flatSubs.filter(sub => 
    sub.name_cn.toLowerCase().includes(kw) ||
    sub.name_en.toLowerCase().includes(kw) ||
    sub.parent_name.toLowerCase().includes(kw)
  )
})

// 已选总数 (Context Aware: Only show count for current tab)
const selectedCount = computed(() => {
  if (currentTab.value === 0) return selectedCategoryIds.value.length
  if (currentTab.value === 1) return selectedDistrictIds.value.length
  if (currentTab.value === 2) return selectedSubDistrictIds.value.length
  return 0
})

// 加载数据
function loadCategories() {
  getCats().then(res => {
    const data = Array.isArray(res) ? res : (res?.data || [])
    categories.value = data.map(cat => ({
      id: String(cat.id),
      name: cat.name
    }))
  })
}

function loadDistricts() {
  getDistricts().then(res => {
    const data = Array.isArray(res) ? res : (res?.data || [])
    districts.value = data.map(dist => ({
      id: String(dist.id),
      name_cn: dist.name_cn,
      name_en: dist.name_en,
      subs: (dist.subs || []).map(sub => ({
        id: String(sub.id),
        name_cn: sub.name_cn,
        name_en: sub.name_en,
        is_remote: sub.is_remote || sub.remote // Handle potential field name differences
      }))
    }))
  })
}

// 复选框变化处理
function onCategoryChange(e, id) {
  const targetId = String(id)
  const isChecked = e.detail.value.includes(targetId)
  
  if (isChecked) {
    if (!selectedCategoryIds.value.includes(targetId)) {
      selectedCategoryIds.value.push(targetId)
    }
  } else {
    selectedCategoryIds.value = selectedCategoryIds.value.filter(x => x !== targetId)
  }
  emitSelection()
}

function onDistrictChange(e, id) {
  const targetId = String(id)
  const isChecked = e.detail.value.includes(targetId)
  
  if (isChecked) {
    if (!selectedDistrictIds.value.includes(targetId)) {
      selectedDistrictIds.value.push(targetId)
    }
  } else {
    selectedDistrictIds.value = selectedDistrictIds.value.filter(x => x !== targetId)
  }
  emitSelection()
}

function onSubDistrictChange(e, id) {
  const targetId = String(id)
  const isChecked = e.detail.value.includes(targetId)
  
  if (isChecked) {
    if (!selectedSubDistrictIds.value.includes(targetId)) {
      selectedSubDistrictIds.value.push(targetId)
    }
  } else {
    selectedSubDistrictIds.value = selectedSubDistrictIds.value.filter(x => x !== targetId)
  }
  emitSelection()
}

// 子区快捷操作
function selectAllSubs() {
  const allIds = filteredSubDistricts.value.map(s => String(s.id))
  // Merge with existing to avoid duplicates
  const newSet = new Set([...selectedSubDistrictIds.value, ...allIds])
  selectedSubDistrictIds.value = Array.from(newSet)
  emitSelection()
}

function selectRemoteSubs() {
  // 筛选出所有 is_remote 为 true 的子区
  const remoteIds = filteredSubDistricts.value
    .filter(s => s.is_remote)
    .map(s => String(s.id))
  
  if (remoteIds.length === 0) {
    uni.showToast({ title: '当前列表无偏远地区', icon: 'none' })
    return
  }

  const newSet = new Set([...selectedSubDistrictIds.value, ...remoteIds])
  selectedSubDistrictIds.value = Array.from(newSet)
  emitSelection()
}

function invertSubSelection() {
  // 对当前过滤列表显示的项进行反选
  const currentVisibleIds = filteredSubDistricts.value.map(s => String(s.id))
  const newSelected = []
  
  // 1. 保留原本已选但不在当前显示列表中的项 (防止搜索筛选时反选丢失其他隐藏项)
  selectedSubDistrictIds.value.forEach(id => {
    if (!currentVisibleIds.includes(id)) {
      newSelected.push(id)
    }
  })
  
  // 2. 对当前显示列表项反转状态
  currentVisibleIds.forEach(id => {
    if (!selectedSubDistrictIds.value.includes(id)) {
      newSelected.push(id)
    }
  })
  
  selectedSubDistrictIds.value = newSelected
  emitSelection()
}

// 发出选中的区域ID和类型
function emitSelection() {
  let selectedItems = []
  
  // 如果是独占模式，只收集当前 Tab 类型的选中项
  // 否则收集所有类型
  const shouldCollectAll = !props.exclusiveType
  
  if (shouldCollectAll || currentTab.value === 0) {
    selectedItems.push(...selectedCategoryIds.value.map(id => ({ id, type: 'category' })))
  }
  
  if (shouldCollectAll || currentTab.value === 1) {
    selectedItems.push(...selectedDistrictIds.value.map(id => ({ id, type: 'district' })))
  }
  
  if (shouldCollectAll || currentTab.value === 2) {
    selectedItems.push(...selectedSubDistrictIds.value.map(id => ({ id, type: 'sub_district' })))
  }
  
  emit('update:modelValue', selectedItems)
}

// 清空选择
function clearSelection() {
  selectedCategoryIds.value = []
  selectedDistrictIds.value = []
  selectedSubDistrictIds.value = []
  emitSelection()
}

// 根据外部传入的regionType设置当前选项卡
watch(() => props.regionType, (type) => {
  const tabMap = { category: 0, district: 1, sub_district: 2 }
  currentTab.value = tabMap[type] || 0
}, { immediate: true })

// 根据外部传入的modelValue更新选中ID
watch(() => props.modelValue, (newVal) => {
  const val = Array.isArray(newVal) ? newVal : []
  
  selectedCategoryIds.value = val
    .filter(item => item.type === 'category')
    .map(item => String(item.id))
    
  selectedDistrictIds.value = val
    .filter(item => item.type === 'district')
    .map(item => String(item.id))
    
  selectedSubDistrictIds.value = val
    .filter(item => item.type === 'sub_district')
    .map(item => String(item.id))
}, { immediate: true, deep: true })

onMounted(() => {
  loadCategories()
  loadDistricts()
})
</script>

<style scoped>
.region-selector {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.search-box {
  padding: 8rpx 0;
}

.quick-actions {
  display: flex;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.list {
  flex: 1;
  max-height: 400rpx;
  border: 1px solid #eee;
  border-radius: 8rpx;
  padding: 12rpx;
}

.list-item {
  padding: 16rpx;
  border-bottom: 1px solid #f5f5f5;
}

.sub-item {
  padding-left: 40rpx;
}

.district-header {
  font-weight: 600;
  color: #333;
  padding: 12rpx 16rpx;
  background: #f9f9f9;
  border-radius: 4rpx;
  margin-top: 8rpx;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.selected-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 16rpx;
  background: #f0f9ff;
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #0066cc;
}
</style>