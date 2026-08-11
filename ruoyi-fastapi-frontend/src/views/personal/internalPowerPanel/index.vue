<template>
  <div class="app-container panel-setting-page">
    <section class="panel-toolbar">
      <div>
        <p class="eyebrow">Personal · PVP 收益面板</p>
        <h1>面板设置</h1>
        <p>读取防守计算器的防守方面板和系统进攻方面板，内功页会使用同一套坦度公式。</p>
      </div>
      <div class="toolbar-actions">
        <el-tag effect="plain" type="info">公式来源 PVP 计算器 4.1</el-tag>
        <el-button plain icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button plain icon="RefreshLeft" @click="resetDefaults">恢复默认</el-button>
        <el-button type="primary" icon="Check" :loading="saving" @click="saveData">保存到防守计算器</el-button>
      </div>
    </section>

    <section class="assist-grid">
      <div class="assist-panel">
        <div class="panel-heading">
          <strong>预设模板</strong>
          <span>套用管理员维护的整套攻击方和受击方面板。</span>
        </div>
        <div class="template-row">
          <el-select
            v-model="selectedTemplateId"
            placeholder="选择面板模板"
            filterable
            clearable
            :loading="templateLoading"
          >
            <el-option
              v-for="item in templates"
              :key="item.templateId"
              :label="item.templateName"
              :value="item.templateId"
            />
          </el-select>
          <el-button type="primary" plain icon="SetUp" :disabled="!selectedTemplate" @click="applySelectedTemplate">
            应用模板
          </el-button>
        </div>
        <p v-if="selectedTemplate?.remark" class="subtle">{{ selectedTemplate.remark }}</p>
      </div>

      <div class="assist-panel">
        <div class="panel-heading">
          <strong>面板识别</strong>
          <span>上传玩家面板截图，识别后可分别写入攻击方或受击方。</span>
        </div>
        <div class="recognition-row">
          <el-upload
            class="panel-upload"
            drag
            action="#"
            accept="image/*"
            :limit="1"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageChange"
          >
            <el-icon><UploadFilled /></el-icon>
            <div class="el-upload__text">拖入图片或点击选择</div>
          </el-upload>
          <div class="recognition-side">
            <div v-if="previewUrl" class="preview-box">
              <img :src="previewUrl" alt="面板截图预览" />
            </div>
            <div v-else class="preview-box empty">未选择图片</div>
            <div class="recognition-actions">
              <el-button type="primary" icon="View" :loading="recognizing" :disabled="!selectedImageFile" @click="recognizeImage">
                开始识别
              </el-button>
              <el-button plain icon="Clock" @click="openHistory">识别历史</el-button>
            </div>
          </div>
        </div>
        <div v-if="recognitionResult" class="recognition-result">
          <div class="result-head">
            <strong>识别结果</strong>
            <el-tag :type="recognitionResult.success ? 'success' : 'danger'" effect="plain">
              {{ recognitionResult.success ? '成功' : '失败' }}
            </el-tag>
          </div>
          <el-alert
            v-if="recognitionResult.error"
            :title="recognitionResult.error"
            type="error"
            :closable="false"
            show-icon
          />
          <div v-if="recognitionResult.parsed" class="result-grid">
            <span v-for="field in recognitionFields" :key="field">
              {{ field }}：{{ recognitionResult.parsed[field] ?? '-' }}
            </span>
          </div>
          <div class="recognition-actions">
            <el-button type="success" plain :disabled="!recognitionResult.success" @click="applyRecognizedAttack">
              设为攻击方面板
            </el-button>
            <el-button type="warning" plain :disabled="!recognitionResult.success" @click="applyRecognizedTarget">
              设为受击方面板
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="setting-grid">
      <div class="setting-panel">
        <div class="panel-heading">
          <strong>防守方面板</strong>
          <span>与防守计算器共用，修改后会同步用于内功坦度收益。</span>
        </div>
        <div class="field-grid">
          <label v-for="field in targetFields" :key="field.key" class="field-item">
            <span>{{ field.label }}</span>
            <div class="number-wrap">
              <el-input-number
                v-model="form.targetPanel[field.key]"
                :min="0"
                :step="field.step || 1"
                :precision="field.precision ?? (field.type === 'percent' ? 5 : 0)"
                controls-position="right"
              />
              <em v-if="field.suffix || field.type === 'percent'">{{ field.suffix || '%' }}</em>
            </div>
          </label>
        </div>
      </div>

      <div class="setting-panel">
        <div class="panel-heading">
          <strong>进攻方面板</strong>
          <span>可选系统参考面板或当前账号的个人攻击方面板。</span>
        </div>
        <el-select v-model="selectedAttackPanelKey" class="attack-panel-select" :loading="loading" @change="applySelectedAttackPanel">
          <el-option-group label="我的攻击方面板"><el-option v-for="panel in personalAttackPanels" :key="`personal-${panel.panelId}`" :label="panel.panelName" :value="panelKey('personal', panel.panelId)" /></el-option-group>
          <el-option-group label="系统参考面板"><el-option v-for="panel in systemAttackPanels" :key="`system-${panel.panelId}`" :label="panel.panelName" :value="panelKey('system', panel.panelId)" /></el-option-group>
        </el-select>
        <div class="field-grid">
          <label v-for="field in attackFields" :key="field.key" class="field-item">
            <span>{{ field.label }}</span>
            <div class="number-wrap">
              <el-input-number
                :model-value="form.attackPanel[field.key]"
                :min="0"
                :precision="field.type === 'percent' ? 5 : 0"
                controls-position="right"
                disabled
              />
              <em v-if="field.type === 'percent'">%</em>
            </div>
          </label>
        </div>
      </div>
    </section>

    <el-drawer v-model="historyDrawerVisible" title="面板识别历史" size="520px">
      <div class="history-head">
        <span>仅展示最近 {{ historyVisibleLimit }} 条，VIP/管理员可查看 10 条。</span>
        <el-button plain size="small" icon="Delete" @click="clearHistory">清空</el-button>
      </div>
      <el-empty v-if="!histories.length" description="暂无识别历史" />
      <div v-else class="history-list">
        <div v-for="item in histories" :key="item.recordId" class="history-item">
          <img
            v-if="item.imageBase64"
            :src="`data:${item.mimeType || 'image/png'};base64,${item.imageBase64}`"
            alt="识别历史缩略图"
          />
          <div class="history-body">
            <div class="history-title">
              <strong>{{ item.fileName || '面板图片' }}</strong>
              <el-tag :type="item.status === 'recognized' ? 'success' : 'danger'" effect="plain" size="small">
                {{ item.status === 'recognized' ? '成功' : '失败' }}
              </el-tag>
            </div>
            <p>{{ item.createTime || '-' }}</p>
            <p v-if="item.error" class="history-error">{{ item.error }}</p>
            <div v-if="item.parsed" class="history-json">
              {{ JSON.stringify(item.parsed) }}
            </div>
            <div v-if="item.parsed && item.status === 'recognized'" class="history-actions">
              <el-button size="small" plain @click="useHistoryResult(item, 'attack')">设为攻击方</el-button>
              <el-button size="small" plain @click="useHistoryResult(item, 'target')">设为受击方</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup name="PersonalInternalPowerPanel">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import {
  clearInternalPowerPanelRecognitionHistory,
  getInternalPowerPanelRecognitionHistory,
  getInternalPowerPanelTemplates,
  recognizeInternalPowerPanelImage
} from '@/api/personal/internalPowerPanel'
import {
  getDefenseCalculatorSetting,
  listDefenseAttackPanels,
  listPersonalDefenseAttackPanels,
  saveDefenseCalculatorSetting,
  updatePersonalDefenseAttackPanel
} from '@/api/personal/defenseCalculator'
import {
  ATTACK_FIELDS,
  DEFAULT_ATTACK,
  DEFAULT_TARGET,
  TARGET_FIELDS,
  fromPanelDisplayValue,
  normalizePanelSetting,
  toPanelDisplayValue
} from '@/utils/internalPowerBenefit'
import {
  DEFAULT_ATTACK_PANEL,
  DEFENDER_FIELDS,
  createDefaultDefender
} from '@/utils/personalDefenseCalculator'

const loading = ref(false)
const saving = ref(false)
const templateLoading = ref(false)
const recognizing = ref(false)
const targetFields = DEFENDER_FIELDS
const attackFields = [
  { key: 'attack', label: '攻击', type: 'number' },
  { key: 'breakDefense', label: '破防', type: 'number' },
  { key: 'restraintValue', label: '克制', type: 'number' },
  { key: 'crit', label: '会心', type: 'number' },
  { key: 'critDmg', label: '会伤', type: 'percent' },
  { key: 'restraintPct', label: '流派克制', type: 'percent' }
]
const recognitionFields = [
  '攻击',
  '破防',
  '会心',
  '会心伤害',
  '流派克制',
  '流派克制百分比',
  '防御',
  '会心抗性',
  '会心防御',
  '流派抵御',
  '流派抵御百分比'
]

const form = reactive({
  targetPanel: {},
  attackPanel: {}
})
const systemAttackPanels = ref([])
const personalAttackPanels = ref([])
const selectedAttackPanelKey = ref(panelKey('system', 0))
const templates = ref([])
const selectedTemplateId = ref(null)
const selectedImageFile = ref(null)
const previewUrl = ref('')
const recognitionResult = ref(null)
const autoAppliedAttackSnapshot = ref(null)
const historyDrawerVisible = ref(false)
const histories = ref([])
const historyVisibleLimit = ref(5)

const selectedTemplate = computed(() => templates.value.find(item => item.templateId === selectedTemplateId.value))

onMounted(() => {
  loadData()
  loadTemplates()
})

async function loadData() {
  loading.value = true
  try {
    const [settingResponse, systemResponse, personalResponse] = await Promise.all([
      getDefenseCalculatorSetting(),
      listDefenseAttackPanels(),
      listPersonalDefenseAttackPanels()
    ])
    const setting = settingResponse.data || settingResponse || {}
    systemAttackPanels.value = systemResponse.data?.length ? systemResponse.data : [DEFAULT_ATTACK_PANEL]
    personalAttackPanels.value = personalResponse.data || []
    selectedAttackPanelKey.value = panelKey(setting.selectedPanelSource, setting.selectedPanelId)
    form.targetPanel = { ...createDefaultDefender(), ...(setting.defender || {}) }
    ensureSelectedAttackPanel()
    applySelectedAttackPanel()
  } catch {
    systemAttackPanels.value = [DEFAULT_ATTACK_PANEL]
    personalAttackPanels.value = []
    selectedAttackPanelKey.value = panelKey('system', DEFAULT_ATTACK_PANEL.panelId)
    form.targetPanel = createDefaultDefender()
    form.attackPanel = { ...DEFAULT_ATTACK_PANEL }
    ElMessage.error('防守计算器面板加载失败，已使用默认面板')
  } finally {
    loading.value = false
  }
}

async function loadTemplates() {
  templateLoading.value = true
  try {
    const response = await getInternalPowerPanelTemplates()
    templates.value = response.data || response || []
  } catch {
    templates.value = []
  } finally {
    templateLoading.value = false
  }
}

async function saveData() {
  saving.value = true
  try {
    const selected = parsePanelKey(selectedAttackPanelKey.value)
    if (selected.source === 'personal') {
      await updatePersonalDefenseAttackPanel(selected.panelId, attackPanelPayload(form.attackPanel))
    }
    await saveDefenseCalculatorSetting({
      defender: form.targetPanel,
      selectedPanelSource: selected.source,
      selectedPanelId: selected.panelId
    })
    ElMessage.success('已保存到防守计算器，内功页会按同一面板计算坦度收益')
  } catch {
    ElMessage.error('保存失败，请检查面板数值')
  } finally {
    saving.value = false
  }
}

async function resetDefaults() {
  try {
    await ElMessageBox.confirm('恢复为源项目默认面板，当前未保存修改会被覆盖。', '恢复默认', {
      type: 'warning',
      confirmButtonText: '恢复',
      cancelButtonText: '取消'
    })
    form.targetPanel = createDefaultDefender()
    selectedAttackPanelKey.value = panelKey('system', systemAttackPanels.value[0]?.panelId || DEFAULT_ATTACK_PANEL.panelId)
    applySelectedAttackPanel()
  } catch {}
}

function applySelectedTemplate() {
  if (!selectedTemplate.value) return
  applyPanelSetting(selectedTemplate.value)
  ElMessage.success('已应用模板，请确认后保存配置')
}

function applySelectedAttackPanel() {
  const selected = parsePanelKey(selectedAttackPanelKey.value)
  form.attackPanel = {
    ...((selected.source === 'personal' ? personalAttackPanels.value : systemAttackPanels.value)
      .find(item => item.panelId === selected.panelId) || DEFAULT_ATTACK_PANEL)
  }
}

function ensureSelectedAttackPanel() {
  const selected = parsePanelKey(selectedAttackPanelKey.value)
  const panels = selected.source === 'personal' ? personalAttackPanels.value : systemAttackPanels.value
  if (panels.some(item => item.panelId === selected.panelId)) return
  const fallback = personalAttackPanels.value[0] || systemAttackPanels.value[0] || DEFAULT_ATTACK_PANEL
  const source = personalAttackPanels.value.some(item => item.panelId === fallback.panelId) ? 'personal' : 'system'
  selectedAttackPanelKey.value = panelKey(source, fallback.panelId)
}

function panelKey(source, panelId) {
  return `${source === 'personal' ? 'personal' : 'system'}:${Number(panelId) || 0}`
}

function parsePanelKey(value) {
  const [source, panelId] = String(value || '').split(':')
  return { source: source === 'personal' ? 'personal' : 'system', panelId: Number(panelId) || 0 }
}

function attackPanelPayload(panel = {}) {
  return Object.fromEntries(Object.keys(DEFAULT_ATTACK_PANEL)
    .filter(key => !['panelId', 'panelName'].includes(key))
    .map(key => [key, Number(panel[key]) || 0]))
}

function handleImageChange(uploadFile) {
  selectedImageFile.value = uploadFile.raw
  recognitionResult.value = null
  autoAppliedAttackSnapshot.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = uploadFile.raw ? URL.createObjectURL(uploadFile.raw) : ''
}

async function recognizeImage() {
  if (!selectedImageFile.value) {
    ElMessage.warning('请先选择面板截图')
    return
  }
  recognizing.value = true
  try {
    const response = await recognizeInternalPowerPanelImage(selectedImageFile.value)
    recognitionResult.value = response.data || response
    if (recognitionResult.value?.success) {
      if (!autoAppliedAttackSnapshot.value) {
        autoAppliedAttackSnapshot.value = clonePanel(form.attackPanel)
      }
      applyRecognizedPanel(recognitionResult.value.parsed, 'attack', { silent: true })
      ElMessage.success('识别成功，已默认写入攻击方面板')
    } else {
      ElMessage.error(recognitionResult.value?.error || '识别失败')
    }
  } catch (error) {
    recognitionResult.value = null
    ElMessage.error(error?.msg || '识别失败')
  } finally {
    recognizing.value = false
  }
}

function applyRecognizedAttack() {
  if (!recognitionResult.value?.parsed) return
  applyRecognizedPanel(recognitionResult.value.parsed, 'attack')
}

function applyRecognizedTarget() {
  if (!recognitionResult.value?.parsed) return
  applyRecognizedPanel(recognitionResult.value.parsed, 'target')
}

function applyRecognizedPanel(parsed, type, options = {}) {
  if (type === 'attack') {
    assignIfNumber(form.attackPanel, 'attack', parsed['攻击'])
    assignIfNumber(form.attackPanel, 'breakDefense', parsed['破防'])
    assignIfNumber(form.attackPanel, 'crit', parsed['会心'])
    assignIfNumber(form.attackPanel, 'critDmg', toCritDamageDisplay(parsed['会心伤害']))
    assignIfNumber(form.attackPanel, 'restraintValue', parsed['流派克制'])
    assignIfNumber(form.attackPanel, 'restraintPct', parsed['流派克制百分比'])
    if (!options.silent) {
      ElMessage.success('已写入攻击方面板，请确认后保存')
    }
    return
  }
  restoreAutoAppliedAttackPanel()
  assignIfNumber(form.targetPanel, 'defense', parsed['防御'])
  assignIfNumber(form.targetPanel, 'critResist', parsed['会心抗性'])
  assignIfNumber(form.targetPanel, 'critDefense', parsed['会心防御'])
  assignIfNumber(form.targetPanel, 'resist', parsed['流派抵御'])
  assignIfNumber(form.targetPanel, 'resistPct', parsed['流派抵御百分比'])
  ElMessage.success('已写入受击方面板，请确认后保存')
}

async function openHistory() {
  historyDrawerVisible.value = true
  await loadHistory()
}

async function loadHistory() {
  try {
    const response = await getInternalPowerPanelRecognitionHistory()
    const data = response.data || response || {}
    histories.value = data.rows || []
    historyVisibleLimit.value = data.visibleLimit || 5
  } catch {
    histories.value = []
    ElMessage.error('识别历史加载失败')
  }
}

async function clearHistory() {
  try {
    await ElMessageBox.confirm('确认清空当前账号的面板识别历史？', '清空历史', {
      type: 'warning',
      confirmButtonText: '清空',
      cancelButtonText: '取消'
    })
    await clearInternalPowerPanelRecognitionHistory()
    histories.value = []
    ElMessage.success('已清空')
  } catch {}
}

function useHistoryResult(item, type) {
  applyRecognizedPanel(item.parsed, type)
  historyDrawerVisible.value = false
}

function applyPanelSetting(value = {}) {
  const setting = normalizePanelSetting(value)
  form.targetPanel = toDisplayPanel(setting.targetPanel, targetFields)
  form.attackPanel = toDisplayPanel(setting.attackPanel, attackFields)
  autoAppliedAttackSnapshot.value = null
}

function buildPayload() {
  return {
    targetPanel: fromDisplayPanel(form.targetPanel, targetFields),
    attackPanel: fromDisplayPanel(form.attackPanel, attackFields)
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

function assignIfNumber(target, key, value) {
  if (value === null || value === undefined || value === '') return
  const numberValue = Number(value)
  if (Number.isFinite(numberValue)) {
    target[key] = numberValue
  }
}

function restoreAutoAppliedAttackPanel() {
  if (!autoAppliedAttackSnapshot.value) return
  form.attackPanel = clonePanel(autoAppliedAttackSnapshot.value)
  autoAppliedAttackSnapshot.value = null
}

function clonePanel(panel = {}) {
  return { ...panel }
}

function toCritDamageDisplay(value) {
  if (value === null || value === undefined || value === '') return null
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? Math.max(0, numberValue - 100) : null
}
</script>

<style scoped lang="scss">
.panel-setting-page {
  min-height: calc(100vh - 84px);
  padding: 24px;
  color: #1f2937;
  background:
    linear-gradient(135deg, rgba(244, 247, 251, 0.9), rgba(252, 249, 242, 0.86)),
    #f6f4ef;
}

.panel-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #84663c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.2;
  color: #111827;
}

.panel-toolbar p:last-child {
  margin: 8px 0 0;
  color: #637083;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

.assist-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.8fr) minmax(0, 1.2fr);
  gap: 18px;
  margin-bottom: 18px;
}

.assist-panel {
  padding: 20px;
  border: 1px solid rgba(31, 41, 55, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 14px 32px rgba(31, 41, 55, 0.08);
}

.template-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.subtle {
  margin: 10px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.recognition-row {
  display: grid;
  grid-template-columns: minmax(220px, 0.9fr) minmax(220px, 1fr);
  gap: 14px;
}

.panel-upload :deep(.el-upload),
.panel-upload :deep(.el-upload-dragger) {
  width: 100%;
}

.panel-upload :deep(.el-upload-dragger) {
  height: 176px;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.9);
}

.recognition-side {
  display: grid;
  gap: 10px;
}

.preview-box {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 118px;
  overflow: hidden;
  border: 1px dashed rgba(100, 116, 139, 0.32);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.84);
  color: #94a3b8;
  font-size: 13px;
}

.preview-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recognition-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.recognition-result {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.86);
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 10px 0 12px;
  color: #334155;
  font-size: 13px;
}

.setting-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.setting-panel {
  padding: 20px;
  border: 1px solid rgba(31, 41, 55, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 14px 32px rgba(31, 41, 55, 0.08);
}

.panel-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-heading strong {
  color: #101827;
  font-size: 17px;
}

.panel-heading span {
  color: #7b8493;
  font-size: 13px;
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

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: #64748b;
  font-size: 13px;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(31, 41, 55, 0.08);
  border-radius: 8px;
  background: #fff;
}

.history-item img {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.history-body {
  min-width: 0;
}

.history-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.history-body p {
  margin: 5px 0;
  color: #94a3b8;
  font-size: 12px;
}

.history-error {
  color: #ef4444 !important;
}

.history-json {
  padding: 8px;
  overflow: hidden;
  border-radius: 6px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

@media (max-width: 1180px) {
  .panel-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .assist-grid,
  .setting-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .panel-setting-page {
    padding: 16px;
  }

  .template-row,
  .recognition-row,
  .field-grid {
    grid-template-columns: 1fr;
  }

  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
