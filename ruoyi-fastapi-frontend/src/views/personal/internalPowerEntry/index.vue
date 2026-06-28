<template>
  <div class="app-container entry-conversion-page">
    <section class="entry-hero">
      <div>
        <p class="eyebrow">Personal Codex · 词条换算</p>
        <h1>内功词条管理</h1>
        <p>维护当前账号自己的进攻能力；固定上限由系统预设。</p>
      </div>
      <div class="hero-actions">
        <el-tag effect="plain" type="info">单位百分比 {{ formatPercent(unitPercent, 5) }}</el-tag>
        <el-button plain icon="Refresh" @click="loadData">刷新</el-button>
        <el-button type="primary" icon="Check" :loading="saving" @click="saveData">保存配置</el-button>
      </div>
    </section>

    <section class="baseline-panel">
      <div class="panel-heading">
        <strong>基准换算</strong>
        <span>填写一个已知进攻能力和百分比，系统按比例计算所有词条。</span>
      </div>
      <div class="baseline-grid">
        <el-form-item label="基准进攻能力">
          <el-input-number
            v-model="form.baseAttackPower"
            :min="0"
            :precision="0"
            controls-position="right"
            placeholder="例如 477"
          />
        </el-form-item>
        <el-form-item label="基准百分比">
          <el-input-number
            v-model="form.basePercent"
            :min="0"
            :precision="5"
            controls-position="right"
            placeholder="例如 7.4"
          />
          <span class="suffix">%</span>
        </el-form-item>
        <div class="unit-card">
          <span>1 进攻能力</span>
          <strong>{{ formatPercent(unitPercent, 5) }}</strong>
        </div>
      </div>
    </section>

    <section class="entry-table-panel">
      <div class="panel-heading">
        <strong>词条数值</strong>
        <span>{{ form.entries.length }} 条固定词条，不包含灵韵。</span>
      </div>

      <el-table v-loading="loading" :data="form.entries" border stripe>
        <el-table-column label="词条名称" prop="entryName" min-width="170" fixed />
        <el-table-column label="固定内功上限" align="center" width="140">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.limitText }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进攻能力" min-width="180">
          <template #default="{ row }">
            <el-input-number
              v-model="row.attackPower"
              :min="0"
              :precision="0"
              controls-position="right"
            />
          </template>
        </el-table-column>
        <el-table-column label="进攻能力百分比" align="center" width="170">
          <template #default="{ row }">
            <strong class="attack-percent">{{ formatPercent(calcAttackPercent(row.attackPower), 5) }}</strong>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup name="PersonalInternalPowerEntry">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getInternalPowerEntryConversion,
  saveInternalPowerEntryConversion
} from '@/api/personal/internalPowerEntry'

const loading = ref(false)
const saving = ref(false)

const form = reactive({
  baseAttackPower: 0,
  basePercent: 0,
  entries: []
})

const unitPercent = computed(() => {
  const baseAttackPower = Number(form.baseAttackPower || 0)
  const basePercent = Number(form.basePercent || 0)
  if (baseAttackPower <= 0) return 0
  return roundTo(basePercent / baseAttackPower, 5)
})

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const response = await getInternalPowerEntryConversion()
    applyResponse(response)
  } catch {
    ElMessage.error('内功词条换算加载失败')
  } finally {
    loading.value = false
  }
}

async function saveData() {
  if (!validateForm()) return
  saving.value = true
  try {
    const response = await saveInternalPowerEntryConversion({
      baseAttackPower: Number(form.baseAttackPower || 0),
      basePercent: Number(form.basePercent || 0),
      entries: form.entries.map(row => ({
        entryName: row.entryName,
        limitText: row.limitText,
        limitValue: row.limitValue,
        valueType: row.valueType,
        attackPower: Number(row.attackPower || 0),
        attackPercent: calcAttackPercent(row.attackPower)
      }))
    })
    applyResponse(response)
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败，请检查数值是否超过上限')
  } finally {
    saving.value = false
  }
}

function applyResponse(response = {}) {
  form.baseAttackPower = Number(response.baseAttackPower || 0)
  form.basePercent = Number(response.basePercent || 0)
  form.entries = (response.entries || []).map(normalizeRow)
}

function normalizeRow(row = {}) {
  return {
    entryName: String(row.entryName || ''),
    limitText: String(row.limitText || ''),
    limitValue: Number(row.limitValue || 0),
    valueType: row.valueType === 'percent' ? 'percent' : 'number',
    attackPower: Number(row.attackPower || 0),
    attackPercent: Number(row.attackPercent || 0)
  }
}

function validateForm() {
  if (Number(form.basePercent || 0) > 0 && Number(form.baseAttackPower || 0) <= 0) {
    ElMessage.warning('填写基准百分比时，基准进攻能力必须大于 0')
    return false
  }
  return true
}

function calcAttackPercent(attackPower) {
  return roundTo(Number(attackPower || 0) * unitPercent.value, 5)
}

function formatPercent(value, precision = 5) {
  return `${Number(value || 0).toFixed(precision)}%`
}

function roundTo(value, precision = 5) {
  const ratio = 10 ** precision
  return Math.round(Number(value || 0) * ratio) / ratio
}
</script>

<style scoped>
.entry-conversion-page {
  min-height: calc(100vh - 84px);
  padding: 24px;
  background:
    linear-gradient(135deg, rgba(248, 250, 255, 0.96), rgba(246, 248, 238, 0.9)),
    repeating-linear-gradient(0deg, rgba(60, 80, 110, 0.05) 0 1px, transparent 1px 24px),
    repeating-linear-gradient(90deg, rgba(60, 80, 110, 0.05) 0 1px, transparent 1px 24px);
}

.entry-hero,
.baseline-panel,
.entry-table-panel {
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 20px 50px rgba(30, 41, 59, 0.08);
}

.entry-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  padding: 24px 28px;
  border-radius: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #9a6a1f;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.entry-hero h1 {
  margin: 0;
  color: #172033;
  font-size: 30px;
  line-height: 1.2;
}

.entry-hero p {
  margin: 8px 0 0;
  color: #64748b;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.baseline-panel,
.entry-table-panel {
  margin-top: 18px;
  padding: 20px;
  border-radius: 14px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  color: #64748b;
}

.panel-heading strong {
  color: #172033;
  font-size: 16px;
}

.baseline-grid {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(220px, 280px) 1fr;
  gap: 16px;
  align-items: end;
}

.baseline-grid :deep(.el-form-item) {
  margin-bottom: 0;
}

.unit-card {
  min-height: 72px;
  border-radius: 12px;
  padding: 14px 16px;
  background: #1f2c3b;
  color: #e5edf6;
  display: grid;
  gap: 4px;
  align-content: center;
}

.unit-card span {
  color: #aab6c4;
  font-size: 12px;
}

.unit-card strong {
  color: #ffd37d;
  font-size: 24px;
}

.suffix {
  color: #64748b;
  font-size: 13px;
}

.attack-percent {
  color: #6d3df1;
}

@media (max-width: 900px) {
  .entry-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-actions {
    justify-content: flex-start;
  }

  .baseline-grid {
    grid-template-columns: 1fr;
  }
}
</style>
