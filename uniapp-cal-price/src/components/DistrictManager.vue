<template>
  <view class="district-wrapper">
    <!-- 行政区列表 -->
    <uni-list>
      <view v-for="d in districts" :key="d.id">
        <!-- 行政区主行 -->
        <uni-list-item
          :title="d.name_cn"
          :rightText="d.name_en"
        >
          <template #footer>
            <button size="mini" class="mr-2" @click.stop="editDistrict(d)">编辑</button>
            <button size="mini" type="primary" @click.stop="addSub(d)">新增子区</button>
          </template>
        </uni-list-item>

        <!-- 子区列表：默认全部展开，无需折叠 -->
        <view v-for="sub in d.subs" :key="sub.id" class="sub-row">
          <text class="sub-text">{{ sub.name_cn }}（{{ sub.name_en }}）</text>
          <!-- <switch :checked="sub.is_remote" @change="onRemoteToggle(d.id, sub)" /> -->
          <button size="mini" class="ml-2" @click="editSub(d.id, sub)">编辑</button>
        </view>
      </view>
    </uni-list>

    <!-- 底部工具栏（可隐藏） -->
    <view v-if="showToolbar" class="btn-bar">
      <button type="primary" @click="addDistrict">新增行政区</button>
    </view>

    <!-- 弹窗表单（行政区 / 子区 共用） -->
    <uni-popup ref="popup" type="dialog">
      <view class="form">
        <view class="form-item">
          <input v-model.trim="form.name_cn" placeholder="中文名" class="input" />
        </view>
        <view class="form-item">
          <input v-model.trim="form.name_en" placeholder="英文名" class="input" />
        </view>
        <!-- <view v-if="popupMode === 'sub'" class="form-item remote-box">
          <text>是否偏远区</text>
          <switch v-model="form.is_remote" />
        </view> -->
        <view class="actions">
          <button size="mini" @click="popup.close">取消</button>
          <button size="mini" type="primary" @click="save">保存</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getDistricts,
  createDistrict,
  updateDistrict,
  createSub,
  updateSub,
  toggleRemote
} from '@/api/district'

const props = defineProps({
  showToolbar: { type: Boolean, default: true }
})
const emit = defineEmits(['refresh'])

const districts = ref([])
const popup = ref(null)
const popupMode = ref('district')
const editingId = ref(null)
const parentDistrictId = ref(null)
const form = ref({ name_cn: '', name_en: '', is_remote: false })

onMounted(fetchData)

function fetchData () {
  getDistricts().then(res => {
    districts.value = res.data
  })
}

function addDistrict () {
  popupMode.value = 'district'
  editingId.value = null
  form.value = { name_cn: '', name_en: '' }
  popup.value.open()
}

function editDistrict (d) {
  popupMode.value = 'district'
  editingId.value = d.id
  form.value = { name_cn: d.name_cn, name_en: d.name_en }
  popup.value.open()
}

function addSub (d) {
  popupMode.value = 'sub'
  parentDistrictId.value = d.id
  editingId.value = null
  form.value = { name_cn: '', name_en: '', is_remote: false }
  popup.value.open()
}

function editSub (dId, sub) {
  popupMode.value = 'sub'
  parentDistrictId.value = dId
  editingId.value = sub.id
  form.value = { name_cn: sub.name_cn, name_en: sub.name_en, is_remote: sub.is_remote }
  popup.value.open()
}

function save () {
  if (!form.value.name_cn || !form.value.name_en) {
    return uni.showToast({ title: '请填写完整', icon: 'none' })
  }
  const afterSave = () => {
    uni.showToast({ title: '保存成功' })
    popup.value.close()
    fetchData()
    emit('refresh')
  }
  if (popupMode.value === 'district') {
    const req = editingId.value
      ? updateDistrict(editingId.value, form.value)
      : createDistrict(form.value)
    req.then(afterSave)
  } else {
    const data = { ...form.value, district_id: parentDistrictId.value }
    const req = editingId.value
      ? updateSub(editingId.value, data)
      : createSub(data)
    req.then(afterSave)
  }
}

function onRemoteToggle (districtId, sub) {
  toggleRemote(districtId, sub.id, !sub.is_remote).then(() => {
    sub.is_remote = !sub.is_remote
  })
}
</script>

<style scoped>
.district-wrapper { padding: 24rpx; min-height: 100vh; background: #f5f6fa; }
.sub-row {
  padding: 16rpx 60rpx;
  background: #fff;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #eee;
}
.sub-text {
  color: #aaa;
  font-size: 26rpx;
  flex: 1;
}
.btn-bar { margin-top: 40rpx; text-align: center; }
.form { padding: 40rpx; width: 500rpx; }
.form-item { margin-bottom: 32rpx; }
.input { border: 1px solid #ccc; border-radius: 8rpx; padding: 16rpx; background: #fff; width: 100%; }
.actions { display: flex; justify-content: flex-end; gap: 24rpx; }
.remote-box { display: flex; align-items: center; gap: 16rpx; }
.mr-2 { margin-right: 16rpx; }
.ml-2 { margin-left: 16rpx; }
</style>
