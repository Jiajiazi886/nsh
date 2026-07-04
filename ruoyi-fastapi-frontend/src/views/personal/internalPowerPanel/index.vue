<template>
  <div class="app-container panel-setting-page">
    <section class="panel-toolbar">
      <div>
        <p class="eyebrow">Personal · PVP 收益面板</p>
        <h1>面板设置</h1>
        <p>保存攻击方无内功基础面板和受击方面板，内功页会用同一套公式动态计算词条收益。</p>
      </div>
      <div class="toolbar-actions">
        <el-tag effect="plain" type="info">公式来源 PVP 计算器 4.1</el-tag>
        <el-button plain icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
        <el-button plain icon="RefreshLeft" @click="resetDefaults">恢复默认</el-button>
        <el-button type="primary" icon="Check" :loading="saving" @click="saveData">保存配置</el-button>
      </div>
    </section>

    <section class="setting-grid">
      <div class="setting-panel">
        <div class="panel-heading">
          <strong>受击方面板</strong>
          <span>防御、抵御、血量、减伤等目标属性。</span>
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
      </div>

      <div class="setting-panel">
        <div class="panel-heading">
          <strong>攻击方无内功基础面板</strong>
          <span>攻击、破防、会心、克制与各伤害乘区。</span>
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
      </div>
    </section>
  </div>
</template>

<script setup name="PersonalInternalPowerPanel">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getInternalPowerPanelSetting,
  saveInternalPowerPanelSetting
} from '@/api/personal/internalPowerPanel'
import {
  ATTACK_FIELDS,
  DEFAULT_ATTACK,
  DEFAULT_TARGET,
  TARGET_FIELDS,
  fromPanelDisplayValue,
  normalizePanelSetting,
  toPanelDisplayValue
} from '@/utils/internalPowerBenefit'

const loading = ref(false)
const saving = ref(false)
const targetFields = TARGET_FIELDS
const attackFields = ATTACK_FIELDS

const form = reactive({
  targetPanel: {},
  attackPanel: {}
})

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const response = await getInternalPowerPanelSetting()
    applyPanelSetting(response.data || response)
  } catch {
    ElMessage.error('面板设置加载失败')
    applyPanelSetting({ targetPanel: DEFAULT_TARGET, attackPanel: DEFAULT_ATTACK })
  } finally {
    loading.value = false
  }
}

async function saveData() {
  saving.value = true
  try {
    const payload = buildPayload()
    const response = await saveInternalPowerPanelSetting(payload)
    applyPanelSetting(response.data || response || payload)
    ElMessage.success('保存成功，内功页收益会按新面板重新计算')
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
    applyPanelSetting({ targetPanel: DEFAULT_TARGET, attackPanel: DEFAULT_ATTACK })
  } catch {}
}

function applyPanelSetting(value = {}) {
  const setting = normalizePanelSetting(value)
  form.targetPanel = toDisplayPanel(setting.targetPanel, targetFields)
  form.attackPanel = toDisplayPanel(setting.attackPanel, attackFields)
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

@media (max-width: 1180px) {
  .panel-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .setting-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .panel-setting-page {
    padding: 16px;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
