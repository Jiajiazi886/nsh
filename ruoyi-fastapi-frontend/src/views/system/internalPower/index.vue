<template>
  <div class="app-container internal-power-admin">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="76px">
      <el-form-item label="内功名称" prop="name">
        <el-input v-model.trim="queryParams.name" clearable placeholder="请输入内功名称" style="width: 220px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" clearable placeholder="全部状态" style="width: 160px">
          <el-option label="正常" value="0" />
          <el-option label="停用" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['system:internal-power:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="Edit" :disabled="single" @click="handleUpdate" v-hasPermi="['system:internal-power:edit']">修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['system:internal-power:remove']">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="presetList" border stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="预设ID" prop="presetId" align="center" width="90" />
      <el-table-column label="图片" align="center" width="92">
        <template #default="{ row }">
          <div class="preset-thumb" :class="{ empty: !resolveImageUrl(row.imageUrl) }">
            <img v-if="resolveImageUrl(row.imageUrl)" :src="resolveImageUrl(row.imageUrl)" :alt="`${row.displayName || row.name}图片`" />
            <span v-else>未上传</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="内功名称" prop="name" min-width="160" :show-overflow-tooltip="true" />
      <el-table-column label="展示名称" prop="displayName" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="增益" min-width="220">
        <template #default="{ row }">
          <div class="bonus-cell">
            <strong>{{ formatBonus(row.bonusPercent) }}</strong>
            <span>{{ row.bonusType || '未设置类型' }}</span>
            <small>{{ row.bonusDesc || '词条和具体数值后续设计' }}</small>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="灵韵增益" align="center" width="120">
        <template #default="{ row }">
          <strong class="lingyun-value">{{ formatBonus(row.lingyunBonusPercent) }}</strong>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '0' ? 'success' : 'info'">{{ row.status === '0' ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" align="center" width="180">
        <template #default="{ row }">
          <span>{{ parseTime(row.updateTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(row)" v-hasPermi="['system:internal-power:edit']">修改</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(row)" v-hasPermi="['system:internal-power:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <el-drawer v-model="open" :title="title" size="min(720px, 96vw)" append-to-body destroy-on-close>
      <el-form ref="presetRef" :model="form" :rules="rules" label-position="top" class="preset-form">
        <el-form-item label="内功名称" prop="name">
          <el-input v-model.trim="form.name" maxlength="64" show-word-limit placeholder="例如：破釜" />
        </el-form-item>
        <el-form-item label="内功图片">
          <div class="image-editor">
            <div class="image-preview" :class="{ empty: !resolveImageUrl(form.imageUrl) }">
              <img v-if="resolveImageUrl(form.imageUrl)" :src="resolveImageUrl(form.imageUrl)" :alt="`${form.name || '内功'}图片预览`" />
              <span v-else>暂无图片</span>
            </div>
            <div class="image-actions">
              <el-upload
                :action="uploadUrl"
                :headers="uploadHeaders"
                :show-file-list="false"
                :before-upload="beforePresetImageUpload"
                :on-success="handlePresetImageSuccess"
                :on-error="handlePresetImageError"
                accept=".png,.jpg,.jpeg,.webp"
              >
                <el-button type="primary" plain icon="Upload">上传内功图片</el-button>
              </el-upload>
              <el-button v-if="form.imageUrl" plain icon="Delete" @click="clearPresetImage">清除图片</el-button>
              <p>新增内功信息时建议上传对应图片；内置图标路径会自动回填。</p>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="基础百分比增益" prop="bonusPercent">
          <el-input-number v-model="form.bonusPercent" :min="0" :max="100" :precision="1" controls-position="right" style="width: 220px" />
        </el-form-item>
        <el-form-item label="灵韵百分比提升" prop="lingyunBonusPercent">
          <el-input-number v-model="form.lingyunBonusPercent" :min="0" :max="100" :precision="1" controls-position="right" style="width: 220px" />
        </el-form-item>
        <el-form-item label="增益类型">
          <el-input v-model.trim="form.bonusType" maxlength="32" placeholder="例如：攻击提升 / 防御提升" />
        </el-form-item>
        <el-form-item label="增益描述">
          <el-input v-model.trim="form.bonusDesc" type="textarea" :rows="3" maxlength="255" show-word-limit placeholder="暂时作为描述预留，具体公式后续设计。" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="0">正常</el-radio>
            <el-radio value="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model.trim="form.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <span>{{ form.entries?.length || 0 }} 个词条占位，默认保留空数据。</span>
          <div>
            <el-button @click="cancel">取消</el-button>
            <el-button type="primary" @click="submitForm">确定</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup name="SystemInternalPower">
import { getToken } from '@/utils/auth'
import {
  addInternalPowerPreset,
  delInternalPowerPreset,
  getInternalPowerPreset,
  listInternalPowerPreset,
  updateInternalPowerPreset
} from '@/api/system/internalPowerPreset'
import { getInternalPowerImageDisplayStatus } from '@/api/system/internalPowerImageDisplay'

const { proxy } = getCurrentInstance()
const baseApi = import.meta.env.VITE_APP_BASE_API
const uploadUrl = `${baseApi}/common/upload`
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${getToken()}` }))

const elementOptions = [
  { key: 'metal', label: '金', color: '#b8902f' },
  { key: 'wood', label: '木', color: '#2f9d62' },
  { key: 'water', label: '水', color: '#2878d8' },
  { key: 'fire', label: '火', color: '#e35335' },
  { key: 'earth', label: '土', color: '#9b6a34' },
  { key: 'mixed', label: '全元素', color: '#6750a4' }
]

const presetList = ref([])
const imageDisplayEnabled = ref(true)
const loading = ref(true)
const showSearch = ref(true)
const open = ref(false)
const title = ref('')
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: undefined,
    status: undefined
  },
  rules: {
    name: [{ required: true, message: '内功名称不能为空', trigger: 'blur' }],
    bonusPercent: [{ required: true, message: '基础百分比增益不能为空', trigger: 'blur' }],
    lingyunBonusPercent: [{ required: true, message: '灵韵百分比提升不能为空', trigger: 'blur' }]
  }
})

const { queryParams, form, rules } = toRefs(data)

const elementTotal = computed(() => Object.values(form.value.elements || {}).reduce((sum, value) => sum + Number(value || 0), 0))
const isElementTotalValid = computed(() => {
  const elements = form.value.elements || {}
  if (form.value.elementKey === 'mixed') {
    return elementTotal.value === 5 && elementOptions.slice(0, 5).every(item => Number(elements[item.key] || 0) === 1)
  }
  return elementTotal.value === 4 && Number(elements[form.value.elementKey] || 0) === 4
})

function getList() {
  loading.value = true
  listInternalPowerPreset(queryParams.value).then(response => {
    presetList.value = (response.rows || []).map(normalizePreset)
    total.value = response.total || 0
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

function reset() {
  form.value = normalizePreset({
    presetId: undefined,
    name: '',
    elementKey: 'metal',
    elements: createElementsByKey('metal'),
    bonusPercent: 0,
    lingyunBonusPercent: 0,
    bonusType: '',
    bonusDesc: '',
    entries: [],
    imageUrl: '',
    status: '0',
    remark: ''
  })
  proxy.resetForm('presetRef')
}

function handleAdd() {
  reset()
  open.value = true
  title.value = '新增内功信息'
}

function handleUpdate(row) {
  reset()
  const presetId = row.presetId || ids.value
  getInternalPowerPreset(presetId).then(response => {
    form.value = normalizePreset(response.data)
    open.value = true
    title.value = '修改内功信息'
  })
}

function submitForm() {
  proxy.$refs.presetRef.validate(valid => {
    if (!valid) return
    const payload = toPayload(form.value)
    const request = payload.presetId ? updateInternalPowerPreset(payload) : addInternalPowerPreset(payload)
    request.then(() => {
      proxy.$modal.msgSuccess(payload.presetId ? '修改成功' : '新增成功')
      open.value = false
      getList()
    })
  })
}

function handleDelete(row) {
  const presetIds = row.presetId || ids.value
  proxy.$modal.confirm(`是否确认删除内功信息编号为"${presetIds}"的数据项？`).then(() => {
    return delInternalPowerPreset(presetIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.presetId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

function cancel() {
  open.value = false
  reset()
}

function applyElementTemplate(value) {
  form.value.elements = createElementsByKey(value)
}

function createElementsByKey(elementKey) {
  const elements = { metal: 0, wood: 0, water: 0, fire: 0, earth: 0 }
  if (elementKey === 'mixed') {
    return { metal: 1, wood: 1, water: 1, fire: 1, earth: 1 }
  }
  elements[elementKey] = 4
  return elements
}

function normalizePreset(value = {}) {
  return {
    presetId: value.presetId,
    name: value.name || '',
    elementKey: value.elementKey || 'metal',
    elements: {
      metal: Number(value.elements?.metal || 0),
      wood: Number(value.elements?.wood || 0),
      water: Number(value.elements?.water || 0),
      fire: Number(value.elements?.fire || 0),
      earth: Number(value.elements?.earth || 0)
    },
    bonusPercent: Number(value.bonusPercent || 0),
    lingyunBonusPercent: Number(value.lingyunBonusPercent ?? value.lingyun_bonus_percent ?? 0),
    bonusType: value.bonusType || '',
    bonusDesc: value.bonusDesc || '',
    imageUrl: value.imageUrl || '',
    entries: Array.isArray(value.entries) ? value.entries : [],
    status: value.status || '0',
    remark: value.remark || '',
    displayName: value.displayName || buildDisplayName(value.name, value.elementKey),
    createTime: value.createTime,
    updateTime: value.updateTime
  }
}

function toPayload(value) {
  const payload = normalizePreset(value)
  payload.entries = []
  return payload
}

async function loadImageDisplayStatus() {
  try {
    const response = await getInternalPowerImageDisplayStatus()
    imageDisplayEnabled.value = response.data?.enabled !== false
  } catch {
    imageDisplayEnabled.value = true
  }
}

function resolveImageUrl(url = '') {
  if (!imageDisplayEnabled.value) return ''
  const value = String(url || '').trim()
  if (!value) return ''
  if (/^(https?:)?\/\//.test(value) || value.startsWith('data:') || value.startsWith('blob:')) return value
  if (value.startsWith('/profile/')) return `${baseApi}${value}`
  return value
}

function beforePresetImageUpload(file) {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const allowTypes = ['png', 'jpg', 'jpeg', 'webp']
  if (!allowTypes.includes(extension)) {
    proxy.$modal.msgError('请上传 png、jpg、jpeg 或 webp 格式的内功图片')
    return false
  }
  if (file.size / 1024 / 1024 > 5) {
    proxy.$modal.msgError('内功图片大小不能超过 5MB')
    return false
  }
  return true
}

function handlePresetImageSuccess(response) {
  if (response.code !== 200) {
    proxy.$modal.msgError(response.msg || '上传内功图片失败')
    return
  }
  form.value.imageUrl = response.fileName || response.data?.fileName || ''
  proxy.$modal.msgSuccess('内功图片上传成功')
}

function handlePresetImageError() {
  proxy.$modal.msgError('上传内功图片失败')
}

function clearPresetImage() {
  form.value.imageUrl = ''
}

function buildDisplayName(name, elementKey) {
  const element = elementOptions.find(item => item.key === elementKey)
  return name ? `${name}（${element?.label || elementKey}）` : ''
}

function formatBonus(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

loadImageDisplayStatus().finally(getList)
</script>

<style scoped>
.internal-power-admin {
  --line: rgba(32, 38, 52, 0.12);
  --ink: #18202d;
}

.element-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.element-badges span {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 3px 7px;
  background: #f7f8fb;
  color: #778091;
  font-size: 12px;
  font-weight: 800;
}

.element-badges span.active {
  border-color: color-mix(in srgb, var(--element-color), transparent 54%);
  background: color-mix(in srgb, var(--element-color), white 88%);
  color: var(--element-color);
}

.preset-thumb {
  width: 52px;
  height: 52px;
  margin: 0 auto;
  border: 1px solid #d8e3f0;
  border-radius: 8px;
  background: #f8fafc;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.preset-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.preset-thumb span {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 800;
}

.bonus-cell {
  display: grid;
  gap: 2px;
}

.bonus-cell strong {
  color: #2563eb;
}

.lingyun-value {
  color: #7c3aed;
}

.bonus-cell span,
.bonus-cell small {
  color: #64748b;
  font-size: 12px;
}

.preset-form {
  padding-right: 8px;
}

.element-editor {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.element-editor-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid color-mix(in srgb, var(--element-color), transparent 72%);
  border-radius: 8px;
  padding: 10px 12px;
  background: color-mix(in srgb, var(--element-color), white 92%);
}

.element-editor-item span {
  color: var(--element-color);
  font-weight: 900;
}

.element-hint {
  margin: 8px 0 0;
  color: #16a34a;
  font-size: 12px;
  font-weight: 800;
}

.element-hint.invalid {
  color: #dc2626;
}

.image-editor {
  display: flex;
  align-items: center;
  gap: 16px;
}

.image-preview {
  width: 96px;
  height: 96px;
  border: 1px solid #d8e3f0;
  border-radius: 8px;
  background:
    linear-gradient(135deg, #f8fafc, #ffffff),
    repeating-linear-gradient(45deg, rgba(148, 163, 184, 0.1) 0 8px, transparent 8px 16px);
  display: grid;
  place-items: center;
  overflow: hidden;
  flex: 0 0 auto;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.image-preview span {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 800;
}

.image-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.image-actions p {
  flex-basis: 100%;
  margin: 0;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.drawer-footer span {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.drawer-footer > div {
  display: flex;
  gap: 8px;
}

@media (max-width: 720px) {
  .element-editor {
    grid-template-columns: 1fr;
  }

  .image-editor {
    align-items: flex-start;
    flex-direction: column;
  }

  .drawer-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .drawer-footer > div {
    justify-content: flex-end;
  }
}
</style>
