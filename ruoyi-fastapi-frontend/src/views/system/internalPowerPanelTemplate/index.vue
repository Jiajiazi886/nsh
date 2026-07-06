<template>
  <div class="app-container panel-template-page">
    <el-form :model="queryParams" ref="queryRef" :inline="true" class="query-bar">
      <el-form-item label="模板名称" prop="templateName">
        <el-input
          v-model="queryParams.templateName"
          placeholder="请输入模板名称"
          clearable
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="模板状态" clearable>
          <el-option label="启用" value="0" />
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
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['system:internal-power-panel-template:add']">
          新增
        </el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="Edit"
          :disabled="single"
          @click="handleUpdate()"
          v-hasPermi="['system:internal-power-panel-template:edit']"
        >
          修改
        </el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="handleDelete()"
          v-hasPermi="['system:internal-power-panel-template:remove']"
        >
          删除
        </el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="templateList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="模板ID" prop="templateId" width="90" align="center" />
      <el-table-column label="模板名称" prop="templateName" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.status"
            active-value="0"
            inactive-value="1"
            :disabled="!hasStatusPerm"
            @change="handleStatusChange(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="攻击方摘要" min-width="230" show-overflow-tooltip>
        <template #default="{ row }">
          攻击 {{ row.attackPanel?.attack ?? '-' }} / 破防 {{ row.attackPanel?.breakDefense ?? '-' }} / 会心 {{ row.attackPanel?.crit ?? '-' }}
        </template>
      </el-table-column>
      <el-table-column label="受击方摘要" min-width="230" show-overflow-tooltip>
        <template #default="{ row }">
          防御 {{ row.targetPanel?.defense ?? '-' }} / 抵御 {{ row.targetPanel?.resist ?? '-' }} / 会心抗性 {{ row.targetPanel?.critResist ?? '-' }}
        </template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" width="170" align="center" />
      <el-table-column label="操作" align="center" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(row)" v-hasPermi="['system:internal-power-panel-template:edit']">
            修改
          </el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(row)" v-hasPermi="['system:internal-power-panel-template:remove']">
            删除
          </el-button>
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

    <el-drawer v-model="open" :title="title" size="820px" append-to-body>
      <el-form ref="templateRef" :model="form" :rules="rules" label-width="92px" class="template-form">
        <el-form-item label="模板名称" prop="templateName">
          <el-input v-model="form.templateName" placeholder="请输入模板名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="0">启用</el-radio>
            <el-radio label="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>

        <section class="form-section">
          <div class="section-title">
            <span>受击方面板</span>
            <div class="section-actions">
              <el-button link type="primary" @click="openJsonImport('target')">JSON导入</el-button>
              <el-button link type="info" @click="showJsonExample('target')">JSON示例</el-button>
            </div>
          </div>
          <div class="field-grid">
            <label v-for="field in targetFields" :key="field.key" class="field-item">
              <span>{{ field.label }}</span>
              <div class="number-wrap">
                <el-input-number
                  v-model="form.targetPanel[field.key]"
                  :min="0"
                  :precision="field.type === 'percent' ? 5 : 0"
                  controls-position="right"
                />
                <em v-if="field.type === 'percent'">%</em>
              </div>
            </label>
          </div>
        </section>

        <section class="form-section">
          <div class="section-title">
            <span>攻击方无内功基础面板</span>
            <div class="section-actions">
              <el-button link type="primary" @click="openJsonImport('attack')">JSON导入</el-button>
              <el-button link type="info" @click="showJsonExample('attack')">JSON示例</el-button>
            </div>
          </div>
          <div class="field-grid">
            <label v-for="field in attackFields" :key="field.key" class="field-item">
              <span>{{ field.label }}</span>
              <div class="number-wrap">
                <el-input-number
                  v-model="form.attackPanel[field.key]"
                  :min="0"
                  :precision="field.type === 'percent' ? 5 : 0"
                  controls-position="right"
                />
                <em v-if="field.type === 'percent'">%</em>
              </div>
            </label>
          </div>
        </section>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="submitForm">保存</el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="jsonImportDialog.open" :title="jsonImportTitle" width="680px" append-to-body>
      <el-form label-width="92px">
        <el-form-item label="导入目标">
          <el-radio-group v-model="jsonImportDialog.panelType">
            <el-radio-button label="target">受击方面板</el-radio-button>
            <el-radio-button label="attack">攻击方面板</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="JSON内容">
          <el-input
            v-model="jsonImportDialog.text"
            type="textarea"
            :rows="14"
            placeholder="粘贴 JSON，可使用中文字段或内部字段名。"
          />
        </el-form-item>
        <el-form-item label="示例">
          <pre class="json-example">{{ currentJsonExample }}</pre>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="jsonImportDialog.open = false">取消</el-button>
          <el-button plain @click="fillCurrentJsonExample">填入示例</el-button>
          <el-button type="primary" @click="applyJsonImport">导入</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="SystemInternalPowerPanelTemplate">
import { computed, getCurrentInstance, onMounted, reactive, ref, toRefs } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  addInternalPowerPanelTemplate,
  changeInternalPowerPanelTemplateStatus,
  delInternalPowerPanelTemplate,
  getInternalPowerPanelTemplate,
  listInternalPowerPanelTemplate,
  updateInternalPowerPanelTemplate
} from '@/api/system/internalPowerPanelTemplate'
import {
  ATTACK_FIELDS,
  DEFAULT_ATTACK,
  DEFAULT_TARGET,
  TARGET_FIELDS,
  fromPanelDisplayValue,
  normalizePanelSetting,
  toPanelDisplayValue
} from '@/utils/internalPowerBenefit'
import useUserStore from '@/store/modules/user'

const { proxy } = getCurrentInstance()
const userStore = useUserStore()
const targetFields = TARGET_FIELDS
const attackFields = ATTACK_FIELDS

const templateList = ref([])
const open = ref(false)
const loading = ref(false)
const submitLoading = ref(false)
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)
const title = ref('')
const jsonImportDialog = reactive({
  open: false,
  panelType: 'target',
  text: ''
})

const data = reactive({
  form: defaultForm(),
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    templateName: undefined,
    status: undefined
  },
  rules: {
    templateName: [{ required: true, message: '模板名称不能为空', trigger: 'blur' }]
  }
})

const { form, queryParams, rules } = toRefs(data)
const hasStatusPerm = computed(() => userStore.permissions?.includes('*:*:*') || userStore.permissions?.includes('system:internal-power-panel-template:status'))
const jsonImportTitle = computed(() => `${jsonImportDialog.panelType === 'attack' ? '攻击方' : '受击方'}面板 JSON 导入`)
const currentJsonExample = computed(() => getJsonExample(jsonImportDialog.panelType))

onMounted(() => {
  getList()
})

async function getList() {
  loading.value = true
  try {
    const response = await listInternalPowerPanelTemplate(queryParams.value)
    templateList.value = response.rows || []
    total.value = response.total || 0
  } finally {
    loading.value = false
  }
}

function cancel() {
  open.value = false
  reset()
}

function reset() {
  form.value = defaultForm()
  proxy?.resetForm?.('templateRef')
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  proxy?.resetForm?.('queryRef')
  handleQuery()
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.templateId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

function handleAdd() {
  reset()
  open.value = true
  title.value = '新增面板模板'
}

function openJsonImport(panelType) {
  jsonImportDialog.panelType = panelType
  jsonImportDialog.text = ''
  jsonImportDialog.open = true
}

function showJsonExample(panelType) {
  jsonImportDialog.panelType = panelType
  jsonImportDialog.text = getJsonExample(panelType)
  jsonImportDialog.open = true
}

function fillCurrentJsonExample() {
  jsonImportDialog.text = currentJsonExample.value
}

function applyJsonImport() {
  let parsed
  try {
    parsed = JSON.parse(jsonImportDialog.text || '{}')
  } catch {
    ElMessage.error('JSON格式错误，请检查逗号、引号和括号')
    return
  }

  const panelType = jsonImportDialog.panelType
  const fields = panelType === 'attack' ? attackFields : targetFields
  const importedPanel = parsePanelJson(parsed, panelType, fields)
  const validKeys = Object.keys(importedPanel)
  if (!validKeys.length) {
    ElMessage.warning('未识别到可导入的面板字段')
    return
  }

  const targetPanel = panelType === 'attack' ? form.value.attackPanel : form.value.targetPanel
  validKeys.forEach(key => {
    targetPanel[key] = importedPanel[key]
  })
  jsonImportDialog.open = false
  ElMessage.success(`已导入${validKeys.length}个字段`)
}

async function handleUpdate(row) {
  reset()
  const templateId = row?.templateId || ids.value[0]
  const response = await getInternalPowerPanelTemplate(templateId)
  const detail = response.data || response
  form.value = toForm(detail)
  open.value = true
  title.value = '修改面板模板'
}

async function submitForm() {
  await proxy.$refs.templateRef.validate()
  submitLoading.value = true
  try {
    const payload = buildPayload()
    if (payload.templateId) {
      await updateInternalPowerPanelTemplate(payload)
      ElMessage.success('修改成功')
    } else {
      await addInternalPowerPanelTemplate(payload)
      ElMessage.success('新增成功')
    }
    open.value = false
    getList()
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  const templateIds = row?.templateId || ids.value.join(',')
  await ElMessageBox.confirm(`是否确认删除面板模板编号为 ${templateIds} 的数据项？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await delInternalPowerPanelTemplate(templateIds)
  ElMessage.success('删除成功')
  getList()
}

async function handleStatusChange(row) {
  const text = row.status === '0' ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确认要${text}模板“${row.templateName}”吗？`, '状态确认', {
      type: 'warning'
    })
    await changeInternalPowerPanelTemplateStatus(row.templateId, row.status)
    ElMessage.success(`${text}成功`)
  } catch {
    row.status = row.status === '0' ? '1' : '0'
  }
}

function defaultForm() {
  return {
    templateId: undefined,
    templateName: '',
    status: '0',
    remark: '',
    targetPanel: toDisplayPanel(DEFAULT_TARGET, targetFields),
    attackPanel: toDisplayPanel(DEFAULT_ATTACK, attackFields)
  }
}

function toForm(value = {}) {
  const setting = normalizePanelSetting(value)
  return {
    templateId: value.templateId,
    templateName: value.templateName || '',
    status: value.status || '0',
    remark: value.remark || '',
    targetPanel: toDisplayPanel(setting.targetPanel, targetFields),
    attackPanel: toDisplayPanel(setting.attackPanel, attackFields)
  }
}

function buildPayload() {
  return {
    templateId: form.value.templateId,
    templateName: form.value.templateName,
    status: form.value.status,
    remark: form.value.remark,
    targetPanel: fromDisplayPanel(form.value.targetPanel, targetFields),
    attackPanel: fromDisplayPanel(form.value.attackPanel, attackFields)
  }
}

function toDisplayPanel(panel, fields) {
  return fields.reduce((out, field) => {
    out[field.key] = toPanelDisplayValue(field.key, panel[field.key])
    return out
  }, {})
}

function fromDisplayPanel(panel, fields) {
  return fields.reduce((out, field) => {
    out[field.key] = fromPanelDisplayValue(field.key, panel[field.key])
    return out
  }, {})
}

function parsePanelJson(raw, panelType, fields) {
  const source = pickPanelSource(raw, panelType)
  const fieldMap = buildPanelImportFieldMap(panelType, fields)
  return Object.entries(source || {}).reduce((out, [rawKey, rawValue]) => {
    const normalizedKey = normalizeImportKey(rawKey)
    const target = fieldMap[normalizedKey]
    if (!target) return out
    const value = normalizeImportNumber(rawValue)
    if (value === null) return out
    out[target.key] = normalizeImportedFieldValue(target, value)
    return out
  }, {})
}

function pickPanelSource(raw, panelType) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {}
  if (panelType === 'attack') {
    return raw.attackPanel || raw.attack_panel || raw.攻击方面板 || raw.攻击方 || raw
  }
  return raw.targetPanel || raw.target_panel || raw.受击方面板 || raw.受击方 || raw
}

function buildPanelImportFieldMap(panelType, fields) {
  const map = {}
  fields.forEach(field => {
    ;[field.key, field.label].forEach(alias => {
      map[normalizeImportKey(alias)] = field
    })
  })

  const aliases = panelType === 'attack'
    ? {
        attack: ['攻击'],
        breakDefense: ['破防'],
        restraintValue: ['流派克制', '克制数值'],
        crit: ['会心'],
        critDmg: ['会心伤害', '会伤', '会伤-100%'],
        extraCritRate: ['额外会心率'],
        restraintPct: ['流派克制百分比', '克制百分比'],
        skillBonusPct: ['技能增强百分比'],
        skillBonus: ['技能增强'],
        gearBonus: ['装备增伤比'],
        internalBonus: ['内功增伤比'],
        elementBonus: ['元素增伤百分比'],
        techniqueRestraint: ['攻击方技巧克制']
      }
    : {
        defense: ['防御'],
        resist: ['流派抵御', '抵御'],
        critResist: ['会心抗性', '会心抵抗'],
        resistPct: ['流派抵御百分比', '抵御百分比'],
        hp: ['血量', '气血', '气血上限'],
        critDefense: ['会心防御'],
        skillResist: ['技能抵御'],
        skillReductionPct: ['技能减免百分比'],
        techniqueResist: ['受击方技巧克制'],
        damageReductionPct: ['减伤百分比', '减伤百分比（日月区）']
      }

  Object.entries(aliases).forEach(([key, names]) => {
    const field = fields.find(item => item.key === key)
    if (!field) return
    names.forEach(name => {
      map[normalizeImportKey(name)] = field
    })
  })
  return map
}

function normalizeImportKey(key) {
  return String(key || '').replace(/[\s_（）()%％/\\-]/g, '').toLowerCase()
}

function normalizeImportNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const normalized = Number(String(value).replace(/,/g, '').replace(/%|％/g, '').trim())
  return Number.isFinite(normalized) ? normalized : null
}

function normalizeImportedFieldValue(field, value) {
  if (field.key === 'critDmg' && value > 100) {
    return roundDisplayNumber(value - 100)
  }
  if (field.type === 'percent' && Math.abs(value) <= 1) {
    return roundDisplayNumber(value * 100)
  }
  return roundDisplayNumber(value)
}

function roundDisplayNumber(value) {
  return Math.round(Number(value || 0) * 100000) / 100000
}

function getJsonExample(panelType) {
  const example = panelType === 'attack'
    ? {
        攻击: 1665,
        破防: 1529,
        会心: 1301,
        会心伤害: 142.0,
        流派克制: 301,
        流派克制百分比: 5.1,
        额外会心率: 0,
        技能增强百分比: 0,
        技能增强: 0,
        装备增伤比: 25,
        内功增伤比: 15,
        元素增伤百分比: 0,
        攻击方技巧克制: 0
      }
    : {
        防御: 2710,
        会心抗性: 911,
        会心防御: 0,
        流派抵御: 486,
        流派抵御百分比: 1.2,
        血量: 100000,
        技能抵御: 0,
        技能减免百分比: 0,
        受击方技巧克制: 0,
        减伤百分比: 0
      }
  return JSON.stringify(example, null, 2)
}
</script>

<style scoped lang="scss">
.panel-template-page {
  min-height: calc(100vh - 84px);
}

.query-bar {
  padding: 18px 18px 0;
  border: 1px solid rgba(31, 41, 55, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
}

.template-form {
  padding-right: 8px;
}

.form-section {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: #111827;
  font-size: 16px;
  font-weight: 700;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
}

.json-example {
  width: 100%;
  max-height: 220px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
}

.field-item {
  display: grid;
  gap: 7px;
  color: #344055;
  font-size: 13px;
  font-weight: 700;
}

.number-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.number-wrap :deep(.el-input-number) {
  width: 100%;
}

.number-wrap em {
  min-width: 18px;
  color: #687589;
  font-style: normal;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 760px) {
  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
