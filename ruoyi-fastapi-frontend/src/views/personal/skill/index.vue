<template>
  <div class="app-container internal-power-page">
    <section class="power-hero">
      <div>
        <p class="eyebrow">Personal Codex · 内功册</p>
        <h1>内功管理</h1>
        <p>先把内功、词条和五行配比管理起来；随机数值与后端同步留给下一轮。</p>
      </div>
      <div class="hero-actions">
        <el-tag effect="plain" type="info">AI识图剩余 {{ aiRecognitionCount }} 次</el-tag>
        <el-button plain @click="openRecognitionDialog">图片识别</el-button>
        <el-button v-if="canEditPowerValues" plain @click="openValueEditor">内功数值编辑</el-button>
        <el-button plain @click="resetSamples">重置示例</el-button>
        <el-button type="primary" :disabled="!canCreateMore" @click="createPower">新增内功</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article class="summary-card">
        <span>内功数量</span>
        <strong>{{ powers.length }}</strong>
        <small>{{ quotaSummaryText }}</small>
      </article>
      <article class="summary-card">
        <span>平均加成</span>
        <strong>{{ averageBonus }}%</strong>
        <small>后续可接随机生成</small>
      </article>
      <article class="summary-card">
        <span>词条总数</span>
        <strong>{{ totalEntries }}</strong>
        <small>可手动维护占位</small>
      </article>
      <article class="summary-card">
        <span>AI识图次数</span>
        <strong>{{ aiRecognitionCount }}</strong>
        <small>每张图片消耗 1 次</small>
      </article>
      <article class="summary-card element-summary">
        <span>五行分布</span>
        <div class="element-strip">
          <i
            v-for="item in elementOptions"
            :key="item.key"
            :style="{ '--element-color': item.color, flexGrow: elementTotals[item.key] || 1 }"
          />
        </div>
        <small>{{ elementSummaryText }}</small>
      </article>
    </section>

    <section class="power-board" v-loading="pageLoading">
      <div class="board-header">
        <div class="panel-title">
          <div>
            <strong>内功库（{{ Math.max(filteredPowers.length, 20) }}个槽位）</strong>
        <span>{{ filteredPowers.length }} 个内功 · {{ limitText }}</span>
          </div>
        </div>

        <div class="filters">
          <el-input v-model.trim="filters.keyword" clearable placeholder="搜索内功名字" />
          <el-select v-model="filters.category" clearable placeholder="全部种类">
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-select v-model="filters.element" clearable placeholder="包含元素">
            <el-option
              v-for="item in elementOptions"
              :key="item.key"
              :label="item.label"
              :value="item.key"
            />
          </el-select>
          <el-button v-if="canEditPowerValues" plain @click="openValueEditor">内功数值编辑</el-button>
          <el-button plain :disabled="!powers.length" @click="toggleBatchMode">
            {{ batchMode ? '退出批量' : '批量管理' }}
          </el-button>
          <el-button v-if="batchMode" plain :disabled="!filteredPowers.length" @click="toggleSelectAllFiltered">
            {{ isAllFilteredSelected ? '取消全选' : '全选当前' }}
          </el-button>
          <el-button v-if="batchMode" type="danger" plain :disabled="!selectedBatchPowers.length" @click="deleteBatchPowers">
            删除选中 {{ selectedBatchPowers.length }}
          </el-button>
          <el-button type="danger" plain :disabled="!powers.length" @click="clearAllPowers">清空内功</el-button>
          <el-button plain @click="resetSamples">重置示例</el-button>
          <el-button type="primary" :disabled="!canCreateMore" @click="createPower">新增内功</el-button>
        </div>
      </div>

      <div class="power-grid">
        <article
          v-for="item in filteredPowers"
          :key="item.id"
          class="power-card"
          :class="{ active: item.id === selectedId, 'batch-selected': isPowerSelected(item.id) }"
          @click="handleCardClick(item)"
        >
          <el-checkbox
            v-if="batchMode"
            class="batch-checkbox"
            :model-value="isPowerSelected(item.id)"
            @click.stop
            @change="togglePowerSelection(item.id)"
          />
          <button class="delete-card" type="button" @click.stop="deletePower(item)">×</button>
          <div class="score-badge">
            <strong>{{ formatBonus(getPowerScore(item)) }}</strong>
            <span>特性：{{ formatBonus(getPowerScore(item) * 0.62) }}</span>
            <span>词条：{{ formatBonus(getPowerScore(item) * 0.38) }}</span>
          </div>

          <div class="card-center">
            <h2>{{ item.name || '未命名内功' }}</h2>
            <p class="element-sequence" :title="formatElementCounts(item.elements)">
              {{ formatElementSequence(item.elements) }}
            </p>
            <div class="entry-pills">
              <span v-for="entry in item.entries" :key="entry.id">{{ getEntryLabel(entry) }}</span>
              <span v-if="!item.entries?.length" class="muted">词条等待后期随机开发</span>
            </div>
          </div>
        </article>

        <button
          v-for="slot in emptySlots"
          :key="slot"
          type="button"
          class="empty-slot-card"
          :disabled="!canCreateMore"
          @click="createPower"
        >
          <span>+</span>
          <strong>空槽位</strong>
          <small>点击新增内功</small>
        </button>
      </div>

      <el-empty v-if="!filteredPowers.length && !emptySlots.length" description="没有匹配的内功" />
    </section>

    <el-dialog
      v-model="deleteConfirmVisible"
      :title="deleteConfirmTitle"
      width="420px"
      append-to-body
      destroy-on-close
      class="delete-confirm-dialog"
      @close="cancelDeleteConfirm"
    >
      <p class="delete-confirm-message">{{ deleteConfirmMessage }}</p>
      <el-checkbox v-model="deleteConfirmSkipForSession">本次登录不再提示删除确认</el-checkbox>
      <template #footer>
        <el-button @click="cancelDeleteConfirm">取消</el-button>
        <el-button type="danger" @click="acceptDeleteConfirm">确认删除</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="recognitionDialogVisible"
      title="内功图片识别"
      width="620px"
      append-to-body
      destroy-on-close
      class="recognition-dialog"
      @closed="resetRecognitionDialog"
    >
      <div class="recognition-panel">
        <el-alert
          title="当前是占位功能：会正常扣除次数，但后端暂时返回空识别结果。"
          type="info"
          show-icon
          :closable="false"
        />
        <div class="recognition-quota">
          <span>剩余次数</span>
          <strong>{{ aiRecognitionCount }}</strong>
          <small>已选择 {{ recognitionFileList.length }} 张，将消耗 {{ recognitionFileList.length }} 次</small>
        </div>
        <el-upload
          drag
          multiple
          accept="image/*"
          :auto-upload="false"
          :file-list="recognitionFileList"
          :on-change="handleRecognitionFileChange"
          :on-remove="handleRecognitionFileRemove"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖入内功截图，或 <em>点击选择图片</em></div>
          <template #tip>
            <div class="el-upload__tip">支持多张图片；每张图片消耗 1 次 AI 识图次数。</div>
          </template>
        </el-upload>
        <div v-if="recognitionResult" class="recognition-result">
          <strong>识别结果</strong>
          <p>AI识图结果待接入，当前返回空对象。</p>
          <code>{{ recognitionResult }}</code>
        </div>
      </div>
      <template #footer>
        <el-button @click="recognitionDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="recognitionSubmitting"
          :disabled="!recognitionFileList.length || recognitionFileList.length > aiRecognitionCount"
          @click="submitRecognition"
        >
          开始识别
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="editingVisible"
      size="min(1080px, 96vw)"
      :with-header="false"
      append-to-body
      destroy-on-close
      class="power-editor-drawer"
    >
      <main class="editor-shell" v-if="draft">
        <header class="editor-topbar">
          <div>
            <span class="editor-kicker">{{ selectedPower ? '编辑内功' : '新增内功' }}</span>
            <h2>{{ draft.name || '未命名内功' }}</h2>
            <p>{{ editorStatusText }}</p>
          </div>
          <div class="editor-actions">
            <el-button plain @click="duplicateSelected">复制</el-button>
            <el-button v-if="selectedPower" plain type="danger" @click="deleteSelected">删除</el-button>
            <button type="button" class="editor-close" @click="editingVisible = false">×</button>
          </div>
        </header>

        <div class="editor-layout">
          <el-form
            ref="formRef"
            :model="draft"
            :rules="rules"
            label-position="top"
            class="power-form"
          >
            <section class="editor-section">
              <div class="section-heading">
                <strong>基础信息</strong>
                <span>决定卡片标题、类型和主加成</span>
              </div>
              <div class="basic-grid">
                <el-form-item label="内功名字" prop="name">
                  <el-input v-model.trim="draft.name" maxlength="24" show-word-limit placeholder="例如：破晓" />
                </el-form-item>

                <el-form-item label="内功种类" prop="category">
                  <el-select v-model="draft.category" placeholder="请选择种类" style="width: 100%" @change="handleCategoryChange">
                    <el-option
                      v-for="item in categoryOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="种类特性" prop="categoryTrait">
                  <el-input v-model.trim="draft.categoryTrait" maxlength="40" placeholder="例如：偏爆发 / 偏承伤 / 偏恢复" />
                </el-form-item>

                <el-form-item label="基础百分比增伤" prop="bonusPercent">
                  <div class="bonus-editor">
                    <el-slider v-model="draft.bonusPercent" :min="0" :max="100" :step="0.1" />
                    <el-input-number v-model="draft.bonusPercent" :min="0" :max="100" :precision="1" controls-position="right" />
                  </div>
                </el-form-item>
              </div>
            </section>

            <section class="editor-section">
              <div class="section-heading">
                <strong>五行元素</strong>
                <span>{{ formatElementCounts(draft.elements) }}</span>
              </div>
              <div class="elements-editor">
                <div class="element-total" :class="{ invalid: elementTotal !== 5 }">
                  <span>当前 {{ elementTotal }} / 5</span>
                  <strong>{{ elementTotal === 5 ? '配比完整' : '必须刚好 5 个元素' }}</strong>
                </div>
                <div class="element-controls">
                  <div
                    v-for="item in elementOptions"
                    :key="item.key"
                    class="element-control"
                    :style="{ '--element-color': item.color, '--element-bg': item.bg }"
                  >
                    <span>{{ item.label }}</span>
                    <div>
                      <el-button size="small" circle @click="changeElement(item.key, -1)">-</el-button>
                      <strong>{{ draft.elements[item.key] || 0 }}</strong>
                      <el-button size="small" circle @click="changeElement(item.key, 1)">+</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="editor-section">
              <div class="section-heading">
                <strong>内功词条</strong>
                <span>{{ draft.entries.length || 0 }} 条</span>
              </div>
              <div class="entries-editor">
                <div
                  v-for="(entry, index) in draft.entries"
                  :key="entry.id"
                  class="entry-row"
                >
                  <el-input v-model.trim="entry.name" placeholder="词条名称，例如：会心伤害" />
                  <el-input v-model.trim="entry.value" placeholder="数值占位，例如：随机" />
                  <el-button text type="danger" @click="removeEntry(index)">删除</el-button>
                </div>
                <el-button plain @click="addEntry">添加词条占位</el-button>
                <p v-if="!draft.entries.length" class="placeholder-note">暂无词条，等待后期随机开发。</p>
              </div>
            </section>

            <section class="editor-section">
              <el-form-item label="备注">
                <el-input
                  v-model.trim="draft.remark"
                  type="textarea"
                  :rows="3"
                  maxlength="160"
                  show-word-limit
                  placeholder="记录这套内功适合什么玩法。"
                />
              </el-form-item>
            </section>
          </el-form>

          <aside class="preview-panel">
            <div class="preview-card">
              <div class="seal">内</div>
              <h2>{{ draft.name || '未命名' }}</h2>
              <p>{{ draft.category }} · {{ draft.categoryTrait || '未设特性' }}</p>
              <strong>{{ formatBonus(draft.bonusPercent) }}</strong>
              <div class="full-elements preview-elements">
                <span
                  v-for="item in elementOptions"
                  :key="item.key"
                  :style="{ '--element-color': item.color, '--element-bg': item.bg }"
                >
                  <b>{{ item.label }}</b>
                  <strong>{{ draft.elements[item.key] || 0 }}</strong>
                </span>
              </div>
              <div class="full-entries preview-entries">
                <span v-for="entry in draft.entries" :key="entry.id">
                  {{ getEntryLabel(entry) }}
                </span>
                <span v-if="!draft.entries.length" class="muted">词条等待后期随机开发</span>
              </div>
            </div>
            <div class="editor-note-card">
              <strong>卡片预览</strong>
              <span>保存后会同步到内功库卡片墙。五行必须刚好 5 个，词条可先用“待随机”占位。</span>
            </div>
          </aside>
        </div>

        <footer class="editor-footer">
          <span>{{ footerStatusText }}</span>
          <div>
            <el-button @click="restoreDraft">撤销改动</el-button>
            <el-button type="primary" :disabled="!canSave" @click="saveDraft">保存内功</el-button>
          </div>
        </footer>
      </main>
    </el-drawer>

    <el-dialog
      v-model="valueEditorVisible"
      title="内功数值编辑"
      width="min(1120px, 96vw)"
      append-to-body
      class="power-value-dialog"
    >
      <div class="value-editor-intro">
        <div>
          <strong>新赛年内功种类与基础增伤</strong>
          <span>这些数值只表示内功本体固定基础增伤，不包含随机词条。当前保存在本机浏览器，后续可迁移到后端。</span>
        </div>
        <div class="value-editor-actions">
          <el-button plain @click="addCatalogRow">新增种类</el-button>
          <el-button plain @click="resetCatalogDraft">恢复默认</el-button>
        </div>
      </div>

      <div class="catalog-table">
        <div class="catalog-head">
          <span>内功种类</span>
          <span>赛年</span>
          <span>级别</span>
          <span>推荐元素</span>
          <span>基础增伤</span>
          <span>特性</span>
          <span>操作</span>
        </div>
        <div v-for="(item, index) in catalogDraft" :key="item.id" class="catalog-row">
          <el-input v-model.trim="item.name" placeholder="内功名" />
          <el-tag effect="plain" type="success">新赛年</el-tag>
          <el-select v-model="item.rarity" placeholder="级别">
            <el-option label="稀有" value="rare" />
            <el-option label="普通" value="common" />
          </el-select>
          <el-select v-model="item.primaryElement" placeholder="元素">
            <el-option label="不限定" value="mixed" />
            <el-option
              v-for="element in elementOptions"
              :key="element.key"
              :label="element.label"
              :value="element.key"
            />
          </el-select>
          <el-input-number v-model="item.baseBonus" :min="0" :max="100" :precision="1" controls-position="right" />
          <el-input v-model.trim="item.trait" placeholder="例如：偏爆发 / 通用增伤" />
          <el-button text type="danger" @click="removeCatalogRow(index)">删除</el-button>
        </div>
      </div>

      <template #footer>
        <div class="value-dialog-footer">
          <span>保存后，新建内功和切换种类会自动带出基础增伤。</span>
          <div>
            <el-button @click="valueEditorVisible = false">取消</el-button>
            <el-button type="primary" @click="saveCatalogDraft">保存配置</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import useUserStore from '@/store/modules/user'
import { checkPermi } from '@/utils/permission'
import {
  addInternalPower,
  deleteInternalPower,
  importLocalInternalPowers,
  listInternalPowers,
  recognizeInternalPowerImages,
  updateInternalPower
} from '@/api/personal/internalPower'

const userStore = useUserStore()
const formRef = ref(null)
const powers = ref([])
const quota = ref({ count: 0, maxCount: 20, unlimited: false, isVip: '0', vipExpireTime: null })
const pageLoading = ref(false)
const selectedId = ref('')
const batchMode = ref(false)
const selectedBatchIds = ref([])
const draft = ref(null)
const savedDraftSignature = ref('')
const editingVisible = ref(false)
const valueEditorVisible = ref(false)
const powerCatalog = ref([])
const catalogDraft = ref([])
const deleteConfirmVisible = ref(false)
const deleteConfirmTitle = ref('删除内功')
const deleteConfirmMessage = ref('')
const deleteConfirmSkipForSession = ref(false)
const deleteConfirmResolve = ref(null)
const recognitionDialogVisible = ref(false)
const recognitionFileList = ref([])
const recognitionSubmitting = ref(false)
const recognitionResult = ref(null)

const filters = reactive({
  keyword: '',
  category: '',
  element: ''
})

const elementOptions = [
  { key: 'metal', label: '金', color: '#c7922e', bg: 'rgba(199, 146, 46, 0.14)' },
  { key: 'wood', label: '木', color: '#2f8f55', bg: 'rgba(47, 143, 85, 0.14)' },
  { key: 'water', label: '水', color: '#2776c7', bg: 'rgba(39, 118, 199, 0.14)' },
  { key: 'fire', label: '火', color: '#d74b37', bg: 'rgba(215, 75, 55, 0.14)' },
  { key: 'earth', label: '土', color: '#8c6a3e', bg: 'rgba(140, 106, 62, 0.16)' }
]

const rules = {
  name: [{ required: true, message: '内功名字不能为空', trigger: 'blur' }],
  category: [{ required: true, message: '请选择内功种类', trigger: 'change' }],
  bonusPercent: [{ required: true, message: '百分比加成不能为空', trigger: 'blur' }]
}

const storageKey = computed(() => {
  if (!userStore.id) return ''
  return `personal-skill:internal-powers:v1:${userStore.id}`
})
const migrationKey = computed(() => {
  if (!userStore.id) return ''
  return `personal-skill:migrated-to-backend:v1:${userStore.id}`
})
const deleteConfirmSkipKey = computed(() => {
  if (!userStore.id) return ''
  return `personal-skill:skip-delete-confirm:v1:${userStore.id}`
})
const catalogStorageKey = 'personal-skill:power-catalog:v1'
const canEditPowerValues = computed(() => checkPermi(['personal:skill:value-edit']))
const aiRecognitionCount = computed(() => Number(userStore.aiImageRecognitionCount || 0))
const canCreateMore = computed(() => quota.value.unlimited || powers.value.length < Number(quota.value.maxCount || 20))
const limitText = computed(() => quota.value.unlimited ? `${powers.value.length} 个已保存 · 不限上限` : `${powers.value.length}/${quota.value.maxCount || 20} 个已保存`)
const quotaSummaryText = computed(() => {
  if (quota.value.unlimited) return quota.value.isVip === '1' ? 'VIP不限内功数' : '管理员不限内功数'
  return `后端保存 · 上限 ${quota.value.maxCount || 20}`
})

const categoryOptions = computed(() => {
  const options = powerCatalog.value.map(item => ({
    label: `${item.name} · ${formatBonus(item.baseBonus)}`,
    value: item.name
  }))
  const existingCategories = powers.value
    .map(item => item.category)
    .filter(Boolean)
    .filter(category => !powerCatalog.value.some(item => item.name === category))
    .map(category => ({ label: `${category} · 自定义`, value: category }))
  return [...options, ...existingCategories]
})

const filteredPowers = computed(() => {
  const keyword = filters.keyword.toLowerCase()
  return powers.value
    .filter(item => {
      const matchKeyword = !keyword || item.name.toLowerCase().includes(keyword) || item.categoryTrait.toLowerCase().includes(keyword)
      const matchCategory = !filters.category || item.category === filters.category
      const matchElement = !filters.element || Number(item.elements?.[filters.element] || 0) > 0
      return matchKeyword && matchCategory && matchElement
    })
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
})

const selectedPower = computed(() => powers.value.find(item => item.id === selectedId.value) || null)
const selectedBatchPowers = computed(() => powers.value.filter(item => selectedBatchIds.value.includes(item.id)))
const isAllFilteredSelected = computed(() => {
  return !!filteredPowers.value.length && filteredPowers.value.every(item => selectedBatchIds.value.includes(item.id))
})
const elementTotal = computed(() => sumElements(draft.value?.elements))
const canSave = computed(() => draft.value && elementTotal.value === 5)
const isDirty = computed(() => draft.value && savedDraftSignature.value !== JSON.stringify(draft.value))
const editorStatusText = computed(() => {
  if (!selectedPower.value) {
    return isDirty.value ? '新建内功有未保存内容' : '新建内功，保存后进入卡片墙'
  }
  return isDirty.value ? '有未保存改动，保存后同步到卡片墙' : '已保存到后端内功库'
})
const footerStatusText = computed(() => {
  if (!canSave.value) return '五行数量未满足 5 个'
  return selectedPower.value ? '可以保存当前改动' : '保存后新增到内功库'
})
const emptySlots = computed(() => {
  const visibleSlots = quota.value.unlimited ? Math.max(20, filteredPowers.value.length + 1) : Math.max(20, quota.value.maxCount || 20)
  const slotCount = Math.max(0, visibleSlots - filteredPowers.value.length)
  return Array.from({ length: slotCount }, (_, index) => `slot-${index}`)
})

const averageBonus = computed(() => {
  if (!powers.value.length) return '0.0'
  const total = powers.value.reduce((sum, item) => sum + getPowerScore(item), 0)
  return (total / powers.value.length).toFixed(1)
})

const totalEntries = computed(() => powers.value.reduce((sum, item) => sum + (item.entries?.length || 0), 0))

const elementTotals = computed(() => {
  const totals = createEmptyElements()
  powers.value.forEach(item => {
    elementOptions.forEach(element => {
      totals[element.key] += Number(item.elements?.[element.key] || 0)
    })
  })
  return totals
})

const elementSummaryText = computed(() => {
  return elementOptions.map(item => `${item.label}${elementTotals.value[item.key] || 0}`).join(' / ')
})

onMounted(async () => {
  loadPowerCatalog()
  await loadPowers()
})

function loadPowerCatalog() {
  try {
    const stored = JSON.parse(localStorage.getItem(catalogStorageKey) || '[]')
    powerCatalog.value = mergePowerCatalog(Array.isArray(stored) ? stored : [])
  } catch {
    powerCatalog.value = createDefaultPowerCatalog()
  }
}

function persistPowerCatalog() {
  localStorage.setItem(catalogStorageKey, JSON.stringify(powerCatalog.value))
}

async function loadPowers() {
  pageLoading.value = true
  try {
    const response = await listInternalPowers()
    applyPowerResponse(response)
    await migrateLocalPowersIfNeeded(response.powers || [])
  } catch (error) {
    ElMessage.error('内功列表加载失败，请稍后重试')
  } finally {
    pageLoading.value = false
  }
}

function isLegacySampleLibrary(items = []) {
  const legacyCategories = new Set(['攻击', '防御', '治疗', '通用'])
  const hasNewSeasonCategory = items.some(item => powerCatalog.value.some(catalog => catalog.name === item.category))
  const hasLegacyCategory = items.some(item => legacyCategories.has(item.category))
  return hasLegacyCategory && !hasNewSeasonCategory
}

function isGeneratedSampleLibrary(items = []) {
  return items.length > 0 && items.every(item => String(item.id || '').startsWith('sample-'))
}

async function migrateLocalPowersIfNeeded(serverPowers = []) {
  if (!userStore.id || !migrationKey.value || !storageKey.value) return
  if (localStorage.getItem(migrationKey.value) === '1') return
  if (serverPowers.length) {
    localStorage.setItem(migrationKey.value, '1')
    return
  }
  let localPowers = []
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey.value) || '[]')
    if (Array.isArray(stored) && stored.length) {
      const normalized = stored.map(normalizePower)
      localPowers = (isLegacySampleLibrary(normalized) || isGeneratedSampleLibrary(normalized)) ? [] : normalized
    }
  } catch {
    localPowers = []
  }
  if (!localPowers.length) {
    localStorage.setItem(migrationKey.value, '1')
    return
  }
  const response = await importLocalInternalPowers(localPowers.map(toPowerPayload))
  applyPowerResponse(response)
  localStorage.setItem(migrationKey.value, '1')
}

function applyPowerResponse(response = {}) {
  powers.value = (response.powers || []).map(normalizePower)
  quota.value = {
    count: response.quota?.count ?? powers.value.length,
    maxCount: response.quota?.maxCount ?? 20,
    unlimited: !!response.quota?.unlimited,
    isVip: response.quota?.isVip || '0',
    vipExpireTime: response.quota?.vipExpireTime || null
  }
}

function updateQuotaCount() {
  quota.value = {
    ...quota.value,
    count: powers.value.length
  }
}

function openRecognitionDialog() {
  recognitionDialogVisible.value = true
}

function handleRecognitionFileChange(file, fileList) {
  recognitionResult.value = null
  recognitionFileList.value = fileList.filter(item => item.raw?.type?.startsWith('image/'))
  if (recognitionFileList.value.length !== fileList.length) {
    ElMessage.warning('只能选择图片文件')
  }
}

function handleRecognitionFileRemove(file, fileList) {
  recognitionResult.value = null
  recognitionFileList.value = fileList
}

function resetRecognitionDialog() {
  recognitionFileList.value = []
  recognitionSubmitting.value = false
  recognitionResult.value = null
}

async function submitRecognition() {
  const files = recognitionFileList.value.map(item => item.raw).filter(Boolean)
  if (!files.length) {
    ElMessage.warning('请先选择图片')
    return
  }
  if (files.length > aiRecognitionCount.value) {
    ElMessage.warning(`AI识图次数不足，当前剩余 ${aiRecognitionCount.value} 次`)
    return
  }
  recognitionSubmitting.value = true
  try {
    const response = await recognizeInternalPowerImages(files)
    const remaining = Number(response.remainingAiImageRecognitionCount ?? aiRecognitionCount.value - files.length)
    userStore.aiImageRecognitionCount = Math.max(0, remaining)
    recognitionResult.value = JSON.stringify(response.result || {}, null, 2)
    recognitionFileList.value = []
    ElMessage.success(response.msg || '识别完成，AI结果待接入')
  } finally {
    recognitionSubmitting.value = false
  }
}

function selectPower(id) {
  selectedId.value = id
  draft.value = clonePower(selectedPower.value)
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

function handleCardClick(item) {
  if (batchMode.value) {
    togglePowerSelection(item.id)
    return
  }
  selectPower(item.id)
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selectedBatchIds.value = []
}

function isPowerSelected(id) {
  return selectedBatchIds.value.includes(id)
}

function togglePowerSelection(id) {
  if (selectedBatchIds.value.includes(id)) {
    selectedBatchIds.value = selectedBatchIds.value.filter(item => item !== id)
    return
  }
  selectedBatchIds.value = [...selectedBatchIds.value, id]
}

function toggleSelectAllFiltered() {
  if (isAllFilteredSelected.value) {
    const filteredIds = new Set(filteredPowers.value.map(item => item.id))
    selectedBatchIds.value = selectedBatchIds.value.filter(id => !filteredIds.has(id))
    return
  }
  const nextIds = new Set(selectedBatchIds.value)
  filteredPowers.value.forEach(item => nextIds.add(item.id))
  selectedBatchIds.value = Array.from(nextIds)
}

function createPower() {
  if (!canCreateMore.value) {
    ElMessage.warning('已超过当前内功上限，请删除后再新增或联系管理员调整上限')
    return
  }
  const firstCatalog = powerCatalog.value[0] || null
  selectedId.value = ''
  draft.value = normalizePower({
    id: createId(),
    name: firstCatalog?.name || '新内功',
    category: firstCatalog?.name || '通用',
    categoryTrait: firstCatalog?.trait || '等待定位',
    bonusPercent: firstCatalog?.baseBonus || 0,
    entries: [],
    elements: createElementsFromPrimary(firstCatalog?.primaryElement),
    remark: '',
    updatedAt: new Date().toISOString()
  })
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

async function saveDraft() {
  if (!draft.value) return
  if (elementTotal.value !== 5) {
    ElMessage.warning('五行元素总数必须刚好为 5')
    return
  }
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  const nextPower = normalizePower({
    ...draft.value,
    updatedAt: new Date().toISOString()
  })
  const response = nextPower.powerId
    ? await updateInternalPower(nextPower.powerId, toPowerPayload(nextPower))
    : await addInternalPower(toPowerPayload(nextPower))
  const savedPower = normalizePower(response)
  const index = powers.value.findIndex(item => item.id === savedPower.id)
  if (index >= 0) {
    powers.value.splice(index, 1, savedPower)
  } else {
    powers.value.unshift(savedPower)
  }
  updateQuotaCount()
  selectedId.value = savedPower.id
  draft.value = clonePower(savedPower)
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = false
  ElMessage.success('内功已保存到后端')
}

function restoreDraft() {
  if (!draft.value) return
  const initialDraft = savedDraftSignature.value ? JSON.parse(savedDraftSignature.value) : null
  const source = selectedPower.value || initialDraft
  if (!source) return
  draft.value = normalizePower(source)
  savedDraftSignature.value = JSON.stringify(draft.value)
  nextTick(() => formRef.value?.clearValidate())
}

async function duplicateSelected() {
  if (!draft.value) return
  if (!canCreateMore.value) {
    ElMessage.warning('已超过当前内功上限，请删除后再复制')
    return
  }
  const copy = normalizePower({
    ...clonePower(draft.value),
    id: createId(),
    powerId: undefined,
    name: `${draft.value.name || '未命名'} 副本`,
    updatedAt: new Date().toISOString()
  })
  const savedPower = normalizePower(await addInternalPower(toPowerPayload(copy)))
  powers.value.unshift(savedPower)
  updateQuotaCount()
  selectPower(savedPower.id)
  ElMessage.success('已复制内功')
}

async function deletePower(power) {
  if (!power) return
  const confirmed = await confirmDeleteAction({
    title: '删除内功',
    message: `确认删除「${power.name || '未命名内功'}」吗？`
  })
  if (!confirmed) {
    return
  }
  await removePowers([power])
  ElMessage.success('已删除')
}

async function deleteSelected() {
  if (!selectedPower.value) return
  const power = selectedPower.value
  const confirmed = await confirmDeleteAction({
    title: '删除内功',
    message: `确认删除「${power.name || '未命名内功'}」吗？`
  })
  if (!confirmed) {
    return
  }
  await removePowers([power])
  ElMessage.success('已删除')
}

async function deleteBatchPowers() {
  if (!selectedBatchPowers.value.length) return
  const count = selectedBatchPowers.value.length
  const confirmed = await confirmDeleteAction({
    title: '批量删除内功',
    message: `确认删除已选中的 ${count} 个内功吗？`
  })
  if (!confirmed) return
  await removePowers(selectedBatchPowers.value)
  selectedBatchIds.value = []
  batchMode.value = false
  ElMessage.success(`已删除 ${count} 个内功`)
}

async function clearAllPowers() {
  if (!powers.value.length) return
  const count = powers.value.length
  const confirmed = await confirmDeleteAction({
    title: '清空内功',
    message: `确认清空当前账号的全部 ${count} 个内功吗？此操作不可恢复。`
  })
  if (!confirmed) return
  await removePowers([...powers.value])
  selectedBatchIds.value = []
  batchMode.value = false
  ElMessage.success('内功已清空')
}

async function removePowers(targetPowers = []) {
  const targets = targetPowers.filter(Boolean)
  for (const power of targets) {
    if (power.powerId) {
      await deleteInternalPower(power.powerId)
    }
  }
  const removeIds = new Set(targets.map(item => item.id))
  powers.value = powers.value.filter(item => !removeIds.has(item.id))
  selectedBatchIds.value = selectedBatchIds.value.filter(id => !removeIds.has(id))
  if (removeIds.has(selectedId.value)) {
    selectedId.value = ''
    draft.value = null
    savedDraftSignature.value = ''
    editingVisible.value = false
  }
  updateQuotaCount()
}

function confirmDeleteAction({ title, message }) {
  if (deleteConfirmSkipKey.value && sessionStorage.getItem(deleteConfirmSkipKey.value) === '1') {
    return Promise.resolve(true)
  }
  deleteConfirmTitle.value = title
  deleteConfirmMessage.value = message
  deleteConfirmSkipForSession.value = false
  deleteConfirmVisible.value = true
  return new Promise(resolve => {
    deleteConfirmResolve.value = resolve
  })
}

function acceptDeleteConfirm() {
  if (deleteConfirmSkipForSession.value && deleteConfirmSkipKey.value) {
    sessionStorage.setItem(deleteConfirmSkipKey.value, '1')
  }
  deleteConfirmResolve.value?.(true)
  deleteConfirmResolve.value = null
  deleteConfirmVisible.value = false
}

function cancelDeleteConfirm() {
  deleteConfirmResolve.value?.(false)
  deleteConfirmResolve.value = null
  deleteConfirmVisible.value = false
}

async function resetSamples() {
  try {
    await ElMessageBox.confirm('这会覆盖当前账号后端保存的内功示例，是否继续？', '重置示例', {
      type: 'warning',
      confirmButtonText: '重置',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  for (const power of powers.value) {
    if (power.powerId) {
      await deleteInternalPower(power.powerId)
    }
  }
  const response = await importLocalInternalPowers(getSamplePowersForQuota().map(toPowerPayload))
  applyPowerResponse(response)
  selectedId.value = ''
  draft.value = null
  savedDraftSignature.value = ''
  editingVisible.value = false
  ElMessage.success('示例内功已重置')
}

function addEntry() {
  draft.value.entries.push({
    id: createId(),
    name: '',
    value: '待随机'
  })
}

function handleCategoryChange(value) {
  if (!draft.value) return
  const catalog = getCatalogByName(value)
  if (!catalog) return
  if (!draft.value.name || draft.value.name === '新内功' || powerCatalog.value.some(item => item.name === draft.value.name)) {
    draft.value.name = catalog.name
  }
  draft.value.categoryTrait = catalog.trait
  draft.value.bonusPercent = catalog.baseBonus
  draft.value.elements = createElementsFromPrimary(catalog.primaryElement)
}

function openValueEditor() {
  catalogDraft.value = powerCatalog.value.map(item => ({ ...item }))
  valueEditorVisible.value = true
}

function addCatalogRow() {
  catalogDraft.value.push(normalizeCatalogItem({
    id: createId(),
    name: '新内功种类',
    rarity: 'common',
    primaryElement: 'mixed',
    baseBonus: 4,
    trait: '待配置'
  }))
}

function removeCatalogRow(index) {
  catalogDraft.value.splice(index, 1)
}

function resetCatalogDraft() {
  catalogDraft.value = createDefaultPowerCatalog().map(item => ({ ...item }))
}

function saveCatalogDraft() {
  const seen = new Set()
  const nextCatalog = []
  for (const item of catalogDraft.value) {
    const normalized = normalizeCatalogItem(item)
    if (!normalized.name) {
      ElMessage.warning('内功种类名称不能为空')
      return
    }
    if (seen.has(normalized.name)) {
      ElMessage.warning(`内功种类「${normalized.name}」重复`)
      return
    }
    seen.add(normalized.name)
    nextCatalog.push(normalized)
  }
  if (!nextCatalog.length) {
    ElMessage.warning('至少保留一个内功种类')
    return
  }
  powerCatalog.value = nextCatalog
  powers.value = powers.value.map(power => {
    const catalog = nextCatalog.find(item => item.name === power.category)
    if (!catalog) return power
    return normalizePower({
      ...power,
      name: power.name || catalog.name,
      categoryTrait: catalog.trait,
      bonusPercent: catalog.baseBonus
    })
  })
  persistPowerCatalog()
  valueEditorVisible.value = false
  ElMessage.success('内功数值配置已保存')
}

function removeEntry(index) {
  draft.value.entries.splice(index, 1)
}

function formatBonus(value) {
  return `+${Number(value || 0).toFixed(1)}%`
}

function getEntryLabel(entry = {}) {
  const name = String(entry.name || '').trim() || '随机词条'
  const value = String(entry.value || '').trim() || '待随机'
  return `${name} ${value}`
}

function formatElementSequence(elements = {}) {
  const sequence = elementOptions
    .flatMap(item => Array.from({ length: Number(elements[item.key] || 0) }, () => item.label))
    .join('')
  return sequence || '未配置元素'
}

function formatElementCounts(elements = {}) {
  return elementOptions.map(item => `${item.label}${Number(elements[item.key] || 0)}`).join(' ')
}

function getPowerScore(power = {}) {
  const catalog = getCatalogByName(power.category)
  return Number(catalog?.baseBonus ?? power.bonusPercent ?? 0)
}

function getCatalogByName(name) {
  return powerCatalog.value.find(item => item.name === name) || null
}

function changeElement(key, delta) {
  const current = Number(draft.value.elements[key] || 0)
  const nextValue = Math.max(0, Math.min(5, current + delta))
  draft.value.elements[key] = nextValue
}

function normalizePower(value) {
  return {
    id: String(value.id || value.powerId || createId()),
    powerId: value.powerId || value.power_id || undefined,
    name: String(value.name || ''),
    category: String(value.category || '通用'),
    categoryTrait: String(value.categoryTrait || ''),
    bonusPercent: clampBonus(value.bonusPercent),
    entries: Array.isArray(value.entries)
      ? value.entries.map(entry => ({
          id: String(entry.id || createId()),
          name: String(entry.name || ''),
          value: String(entry.value || '')
        }))
      : [],
    elements: normalizeElements(value.elements),
    remark: String(value.remark || ''),
    updatedAt: value.updatedAt || new Date().toISOString()
  }
}

function toPowerPayload(power) {
  return {
    id: power.id,
    powerId: power.powerId,
    name: power.name,
    category: power.category,
    categoryTrait: power.categoryTrait,
    bonusPercent: power.bonusPercent,
    entries: power.entries || [],
    elements: power.elements || createEmptyElements(),
    remark: power.remark || '',
    updatedAt: power.updatedAt
  }
}

function normalizeElements(value = {}) {
  const elements = createEmptyElements()
  elementOptions.forEach(item => {
    elements[item.key] = Math.max(0, Math.min(5, Number(value[item.key] || 0)))
  })
  return elements
}

function sumElements(elements = {}) {
  return elementOptions.reduce((sum, item) => sum + Number(elements[item.key] || 0), 0)
}

function createEmptyElements() {
  return { metal: 0, wood: 0, water: 0, fire: 0, earth: 0 }
}

function createElementsFromPrimary(primaryElement = 'mixed') {
  if (primaryElement && primaryElement !== 'mixed') {
    return {
      ...createEmptyElements(),
      [primaryElement]: 5
    }
  }
  return { metal: 1, wood: 1, water: 1, fire: 1, earth: 1 }
}

function clonePower(value) {
  return value ? JSON.parse(JSON.stringify(value)) : null
}

function clampBonus(value) {
  const numberValue = Number(value || 0)
  if (!Number.isFinite(numberValue)) return 0
  return Math.max(0, Math.min(100, Number(numberValue.toFixed(1))))
}

function createId() {
  return `skill-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

function normalizeCatalogItem(value = {}) {
  return {
    id: String(value.id || createId()),
    name: String(value.name || '').trim(),
    season: 'new',
    rarity: value.rarity === 'rare' ? 'rare' : 'common',
    primaryElement: ['metal', 'wood', 'water', 'fire', 'earth', 'mixed'].includes(value.primaryElement)
      ? value.primaryElement
      : 'mixed',
    baseBonus: clampBonus(value.baseBonus),
    trait: String(value.trait || '').trim() || '待配置'
  }
}

function mergePowerCatalog(stored = []) {
  const storedMap = new Map(stored.map(item => [String(item.name || '').trim(), item]))
  const defaults = createDefaultPowerCatalog()
  const merged = defaults.map(item => normalizeCatalogItem({ ...item, ...(storedMap.get(item.name) || {}) }))
  stored.forEach(item => {
    const name = String(item.name || '').trim()
    if (name && !merged.some(defaultItem => defaultItem.name === name)) {
      merged.push(normalizeCatalogItem(item))
    }
  })
  return merged
}

function createDefaultPowerCatalog() {
  return [
    { id: 'catalog-rare-ry-fire', name: '日月两仪·火', rarity: 'rare', primaryElement: 'fire', baseBonus: 6, trait: '稀有火系基础增伤' },
    { id: 'catalog-rare-ry-earth', name: '日月两仪·土', rarity: 'rare', primaryElement: 'earth', baseBonus: 6, trait: '稀有土系基础增伤' },
    { id: 'catalog-rare-jd-metal', name: '绝电惊沙·金', rarity: 'rare', primaryElement: 'metal', baseBonus: 6, trait: '稀有金系基础增伤' },
    { id: 'catalog-rare-jd-wood', name: '绝电惊沙·木', rarity: 'rare', primaryElement: 'wood', baseBonus: 6, trait: '稀有木系基础增伤' },
    { id: 'catalog-rare-cy-fire', name: '承影锋烁·火', rarity: 'rare', primaryElement: 'fire', baseBonus: 6, trait: '稀有火系基础增伤' },
    { id: 'catalog-rare-cy-metal', name: '承影锋烁·金', rarity: 'rare', primaryElement: 'metal', baseBonus: 6, trait: '稀有金系基础增伤' },
    { id: 'catalog-rare-bd-wood', name: '不动明王·木', rarity: 'rare', primaryElement: 'wood', baseBonus: 6, trait: '稀有木系基础增伤' },
    { id: 'catalog-rare-bd-water', name: '不动明王·水', rarity: 'rare', primaryElement: 'water', baseBonus: 6, trait: '稀有水系基础增伤' },
    { id: 'catalog-common-wyy', name: '五韵谣', rarity: 'common', primaryElement: 'mixed', baseBonus: 4, trait: '普通通用基础增伤' },
    { id: 'catalog-common-wjc', name: '望惊川', rarity: 'common', primaryElement: 'water', baseBonus: 4, trait: '普通水系基础增伤' },
    { id: 'catalog-common-zm', name: '珠明', rarity: 'common', primaryElement: 'water', baseBonus: 4, trait: '普通水系基础增伤' },
    { id: 'catalog-common-gx', name: '固玺', rarity: 'common', primaryElement: 'earth', baseBonus: 4, trait: '普通土系基础增伤' },
    { id: 'catalog-common-yqz', name: '御千嶂', rarity: 'common', primaryElement: 'earth', baseBonus: 4, trait: '普通土系基础增伤' },
    { id: 'catalog-common-pzy', name: '破重云', rarity: 'common', primaryElement: 'wood', baseBonus: 4, trait: '普通木系基础增伤' },
    { id: 'catalog-common-lq', name: '凌穹', rarity: 'common', primaryElement: 'wood', baseBonus: 4, trait: '普通木系基础增伤' },
    { id: 'catalog-common-pf', name: '破釜', rarity: 'common', primaryElement: 'fire', baseBonus: 4, trait: '普通火系基础增伤' },
    { id: 'catalog-common-gsy', name: '贯山月', rarity: 'common', primaryElement: 'metal', baseBonus: 4, trait: '普通金系基础增伤' },
    { id: 'catalog-common-zmiao', name: '众妙', rarity: 'common', primaryElement: 'fire', baseBonus: 4, trait: '普通火系基础增伤' },
    { id: 'catalog-common-cy', name: '炽原', rarity: 'common', primaryElement: 'fire', baseBonus: 4, trait: '普通火系基础增伤' }
  ].map(normalizeCatalogItem)
}

function createSamplePowers() {
  const samples = powerCatalog.value.length ? powerCatalog.value : createDefaultPowerCatalog()
  return samples.map((item, index) => normalizePower({
    id: `sample-${item.id}`,
    name: item.name,
    category: item.name,
    categoryTrait: item.trait,
    bonusPercent: item.baseBonus,
    entries: [
      { id: `sample-${item.id}-entry-1`, name: '固定基础', value: formatBonus(item.baseBonus) },
      { id: `sample-${item.id}-entry-2`, name: '随机词条', value: '待随机' }
    ],
    elements: createElementsFromPrimary(item.primaryElement),
    remark: item.rarity === 'rare' ? '新赛年稀有内功，基础数值可在权限面板调整。' : '新赛年普通内功，基础数值可在权限面板调整。',
    updatedAt: new Date(Date.UTC(2026, 5, 20, 8, 0, 0) - index * 60000).toISOString()
  }))
}

function getSamplePowersForQuota() {
  const samples = createSamplePowers()
  if (quota.value.unlimited) return samples
  return samples.slice(0, Math.max(20, Number(quota.value.maxCount || 20)))
}
</script>

<style scoped>
.internal-power-page {
  --ink: #18202d;
  --paper: #f8f3e9;
  --paper-deep: #efe2cf;
  --line: rgba(61, 43, 25, 0.14);
  --gold: #b9852c;
  color: var(--ink);
  background:
    radial-gradient(circle at 10% 8%, rgba(185, 133, 44, 0.16), transparent 32%),
    radial-gradient(circle at 86% 12%, rgba(32, 73, 86, 0.14), transparent 28%),
    linear-gradient(135deg, #fbf7ee, #edf3f2 48%, #f8f3e9);
  min-height: calc(100vh - 84px);
}

.power-hero,
.summary-card,
.power-board {
  border: 1px solid var(--line);
  box-shadow: 0 18px 38px rgba(55, 43, 28, 0.08);
}

.power-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  border-radius: 20px;
  padding: 26px 28px;
  background:
    linear-gradient(135deg, rgba(24, 32, 45, 0.96), rgba(55, 71, 75, 0.9)),
    var(--ink);
  color: #fff8e8;
  overflow: hidden;
  position: relative;
}

.power-hero::after {
  content: "";
  position: absolute;
  inset: auto -30px -52px auto;
  width: 230px;
  height: 230px;
  border-radius: 50%;
  border: 34px solid rgba(185, 133, 44, 0.16);
}

.eyebrow {
  margin: 0 0 8px;
  color: #e7bf73;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.power-hero h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0.08em;
}

.power-hero p:last-child {
  margin: 10px 0 0;
  max-width: 620px;
  color: rgba(255, 248, 232, 0.74);
  font-weight: 600;
}

.hero-actions {
  display: flex;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 14px;
  margin: 16px 0;
}

.summary-card {
  border-radius: 16px;
  padding: 16px;
  background: rgba(255, 252, 244, 0.78);
  backdrop-filter: blur(12px);
}

.summary-card span,
.summary-card small {
  display: block;
  color: #6b5b48;
  font-size: 12px;
  font-weight: 700;
}

.summary-card strong {
  display: block;
  margin: 6px 0 2px;
  font-size: 30px;
  color: var(--ink);
}

.element-strip {
  display: flex;
  gap: 3px;
  height: 18px;
  margin: 10px 0 8px;
}

.element-strip i {
  min-width: 12px;
  border-radius: 999px;
  background: var(--element-color);
}

.power-board {
  border-radius: 18px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
}

.board-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 16px;
  margin-bottom: 14px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title div:first-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.panel-title strong {
  font-size: 16px;
}

.panel-title span {
  color: #786957;
  font-size: 12px;
  font-weight: 700;
}

.filters {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.filters :deep(.el-input),
.filters :deep(.el-select) {
  width: 170px;
}

.power-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(220px, 1fr));
  gap: 12px;
}

.power-card {
  position: relative;
  min-height: 320px;
  border: 2px solid #b8dcff;
  border-radius: 8px;
  padding: 14px;
  background: #ffffff;
  cursor: pointer;
  color: #111827;
  overflow: hidden;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.power-card:hover,
.power-card.active {
  transform: translateY(-1px);
  border-color: #4aa3ff;
  box-shadow: 0 12px 28px rgba(59, 130, 246, 0.14);
}

.power-card.batch-selected {
  border-color: #7c3aed;
  background: linear-gradient(180deg, rgba(124, 58, 237, 0.1), #ffffff 38%);
  box-shadow: 0 14px 30px rgba(124, 58, 237, 0.18);
}

.batch-checkbox {
  position: absolute;
  top: 10px;
  left: 102px;
  z-index: 2;
  border-radius: 999px;
  padding: 2px 7px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
}

.score-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  min-width: 74px;
  border: 1px solid #d8dfe8;
  border-radius: 4px;
  padding: 6px 9px;
  background: rgba(255, 255, 255, 0.92);
  display: grid;
  gap: 3px;
}

.score-badge strong {
  color: #2f89ff;
  font-size: 14px;
  line-height: 1;
}

.score-badge span {
  color: #16a34a;
  font-size: 11px;
  line-height: 1.15;
  white-space: nowrap;
}

.delete-card {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 999px;
  background: #ff4d5a;
  color: #ffffff;
  font-size: 19px;
  line-height: 20px;
  cursor: pointer;
  display: grid;
  place-items: center;
  box-shadow: 0 6px 16px rgba(255, 77, 90, 0.22);
}

.card-center {
  min-height: 286px;
  padding: 72px 8px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.card-center h2 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: 20px;
  font-weight: 900;
  word-break: break-word;
}

.element-sequence {
  margin: 0 0 12px;
  color: #334155;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.06em;
  word-break: break-word;
}

.entry-pills {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 7px;
}

.entry-pills span {
  border-radius: 5px;
  padding: 6px 9px;
  background: #eef4ff;
  color: #334155;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.2;
  word-break: break-word;
}

.entry-pills .muted {
  color: #94a3b8;
}

.empty-slot-card {
  min-height: 320px;
  border: 2px solid #d8e1eb;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.48);
  color: #94a3b8;
  cursor: pointer;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
}

.empty-slot-card:hover {
  border-color: #93c5fd;
  color: #2563eb;
}

.empty-slot-card:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.empty-slot-card span {
  font-size: 28px;
  line-height: 1;
}

.empty-slot-card strong {
  color: inherit;
  font-size: 16px;
}

.empty-slot-card small {
  font-size: 12px;
}

.delete-confirm-message {
  margin: 0 0 14px;
  color: #334155;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.7;
}

.full-elements {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
  margin-top: 10px;
}

.full-elements > span {
  border: 1px solid color-mix(in srgb, var(--element-color), transparent 74%);
  border-radius: 12px;
  padding: 7px 6px;
  background: var(--element-bg);
  color: var(--element-color);
  display: grid;
  place-items: center;
  gap: 2px;
}

.full-elements b {
  font-size: 12px;
  font-weight: 900;
}

.full-elements strong {
  color: #151c26;
  font-size: 17px;
  line-height: 1;
}

.full-entries {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}

.full-entries > span {
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(255, 247, 232, 0.92);
  border: 1px solid rgba(185, 133, 44, 0.2);
  color: #3f3326;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  white-space: normal;
  word-break: break-word;
}

.full-entries .muted {
  color: #82705c;
}

.editor-shell {
  --editor-bg: #f6f0e6;
  --editor-card: rgba(255, 252, 246, 0.94);
  --editor-line: rgba(38, 50, 68, 0.1);
  min-height: 100%;
  padding: 18px;
  background:
    radial-gradient(circle at 92% 8%, rgba(185, 133, 44, 0.16), transparent 26%),
    linear-gradient(135deg, #fbf7ef, var(--editor-bg));
}

.editor-topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  border: 1px solid var(--editor-line);
  border-radius: 20px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 16px 38px rgba(38, 50, 68, 0.08);
}

.editor-kicker {
  color: #9a6b28;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.editor-topbar h2 {
  margin: 4px 0;
  color: #111827;
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.08;
}

.editor-topbar p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-close {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: #fff;
  color: #1f2937;
  cursor: pointer;
  font-size: 25px;
  line-height: 1;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.editor-close:hover {
  transform: rotate(8deg) scale(1.04);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
}

.editor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
  gap: 16px;
  align-items: start;
  padding-bottom: 78px;
}

.power-form {
  display: grid;
  gap: 14px;
}

.editor-section,
.preview-card,
.editor-note-card,
.editor-footer {
  border: 1px solid var(--editor-line);
  border-radius: 20px;
  background: var(--editor-card);
  box-shadow: 0 14px 34px rgba(51, 65, 85, 0.07);
}

.editor-section {
  padding: 16px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-heading strong {
  color: #172033;
  font-size: 15px;
}

.section-heading span {
  color: #8a7862;
  font-size: 12px;
  font-weight: 800;
  text-align: right;
}

.basic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 14px;
}

.power-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.power-form :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 900;
}

.power-form :deep(.el-input__wrapper),
.power-form :deep(.el-select__wrapper),
.power-form :deep(.el-textarea__inner),
.power-form :deep(.el-input-number) {
  border-radius: 14px;
}

.bonus-editor {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 138px;
  gap: 14px;
  align-items: center;
}

.elements-editor,
.entries-editor {
  width: 100%;
}

.element-total {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  border-radius: 16px;
  padding: 10px 12px;
  background: rgba(34, 197, 94, 0.11);
  color: #14783d;
  font-weight: 900;
}

.element-total.invalid {
  background: rgba(239, 68, 68, 0.12);
  color: #b42318;
}

.element-controls {
  display: grid;
  grid-template-columns: repeat(5, minmax(86px, 1fr));
  gap: 10px;
}

.element-control {
  border: 1px solid color-mix(in srgb, var(--element-color), transparent 72%);
  border-radius: 18px;
  padding: 12px 10px;
  background: var(--element-bg);
}

.element-control > span {
  display: block;
  color: var(--element-color);
  font-size: 14px;
  font-weight: 1000;
  text-align: center;
}

.element-control > div {
  display: grid;
  grid-template-columns: 28px minmax(20px, 1fr) 28px;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}

.element-control strong {
  color: #111827;
  font-size: 20px;
  text-align: center;
}

.entry-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(100px, 140px) auto;
  gap: 8px;
  margin-bottom: 8px;
}

.placeholder-note {
  margin: 8px 0 0;
  color: #8a7862;
  font-size: 12px;
  font-weight: 800;
}

.preview-panel {
  position: sticky;
  top: 14px;
  display: grid;
  gap: 12px;
}

.preview-card {
  padding: 24px;
  background:
    linear-gradient(145deg, rgba(25, 34, 48, 0.98), rgba(48, 62, 58, 0.96));
  color: #fff8e8;
}

.seal {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--gold);
  color: #20170c;
  font-size: 24px;
  font-weight: 1000;
}

.preview-card h2 {
  margin: 18px 0 6px;
  font-size: 30px;
  word-break: break-word;
}

.preview-card p {
  margin: 0;
  color: rgba(255, 248, 232, 0.72);
  font-weight: 800;
}

.preview-card > strong {
  display: block;
  margin: 18px 0;
  color: #f3c875;
  font-size: 42px;
  line-height: 1;
}

.preview-elements {
  margin-top: 0;
}

.preview-entries {
  margin-top: 14px;
}

.preview-entries > span {
  background: rgba(255, 248, 232, 0.1);
  border-color: rgba(255, 248, 232, 0.18);
  color: #fff8e8;
}

.preview-entries .muted {
  color: rgba(255, 248, 232, 0.62);
}

.editor-note-card {
  padding: 14px;
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.editor-note-card strong,
.editor-note-card span {
  display: block;
}

.editor-note-card strong {
  margin-bottom: 5px;
  color: #172033;
}

.editor-footer {
  position: sticky;
  bottom: 0;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: -62px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
}

.editor-footer span {
  color: #64748b;
  font-size: 13px;
  font-weight: 900;
}

.editor-footer > div {
  display: flex;
  gap: 8px;
}

:deep(.power-editor-drawer.el-drawer) {
  max-width: 100vw;
}

:deep(.power-editor-drawer .el-drawer__body) {
  padding: 0;
  background: #f6f0e6;
  overflow: auto;
}

.value-editor-intro {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 14px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 16px;
  background:
    radial-gradient(circle at 12% 16%, rgba(199, 146, 46, 0.13), transparent 28%),
    linear-gradient(135deg, rgba(248, 250, 252, 0.98), rgba(239, 246, 255, 0.92));
}

.value-editor-intro strong,
.value-editor-intro span {
  display: block;
}

.value-editor-intro strong {
  color: #172033;
  font-size: 16px;
}

.value-editor-intro span {
  margin-top: 5px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.value-editor-actions {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
}

.catalog-table {
  display: grid;
  gap: 8px;
  max-height: min(62vh, 620px);
  margin-top: 14px;
  overflow: auto;
  padding-right: 4px;
}

.catalog-head,
.catalog-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) 74px 96px 112px 126px minmax(180px, 1fr) 64px;
  gap: 8px;
  align-items: center;
}

.catalog-head {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 10px 12px;
  border-radius: 12px;
  background: #18202d;
  color: #fff8e8;
  font-size: 12px;
  font-weight: 900;
}

.catalog-row {
  padding: 10px 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
}

.value-dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.value-dialog-footer span {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.value-dialog-footer > div {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
}

:deep(.power-value-dialog .el-dialog) {
  border-radius: 18px;
}

:deep(.power-value-dialog .el-dialog__body) {
  padding-top: 10px;
}

.recognition-panel {
  display: grid;
  gap: 16px;
}

.recognition-quota {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(59, 130, 246, 0.16);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.9), rgba(255, 247, 237, 0.78));
}

.recognition-quota span,
.recognition-quota small {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.recognition-quota strong {
  color: #2563eb;
  font-size: 28px;
  font-weight: 950;
}

.recognition-result {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: #0f172a;
  color: #dbeafe;
}

.recognition-result p {
  margin: 0;
  color: #93a4bd;
  font-size: 13px;
}

.recognition-result code {
  white-space: pre-wrap;
  color: #bfdbfe;
}

@media (max-width: 1180px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .board-header {
    grid-template-columns: 1fr;
  }

  .filters {
    justify-content: flex-start;
  }

  .power-grid {
    grid-template-columns: repeat(2, minmax(220px, 1fr));
  }

  .editor-layout {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
    grid-template-columns: minmax(0, 1fr) minmax(240px, 0.72fr);
    align-items: stretch;
  }

  .element-controls {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .catalog-head {
    display: none;
  }

  .catalog-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .internal-power-page {
    padding: 12px;
  }

  .power-hero {
    align-items: stretch;
    flex-direction: column;
    padding: 22px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .board-header {
    gap: 10px;
  }

  .filters,
  .hero-actions {
    width: 100%;
  }

  .filters > .el-button,
  .hero-actions > .el-button {
    flex: 1;
  }

  .editor-shell {
    padding: 10px;
  }

  .editor-topbar {
    flex-direction: column;
    border-radius: 16px;
    padding: 14px;
  }

  .editor-actions {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .editor-actions :deep(.el-button) {
    flex: 1;
  }

  .editor-layout {
    padding-bottom: 0;
  }

  .editor-section,
  .preview-card,
  .editor-note-card,
  .editor-footer {
    border-radius: 16px;
  }

  .section-heading {
    flex-direction: column;
    gap: 4px;
  }

  .section-heading span {
    text-align: left;
  }

  .basic-grid,
  .bonus-editor,
  .entry-row {
    grid-template-columns: 1fr;
  }

  .element-controls {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    grid-template-columns: 1fr;
  }

  .preview-card {
    padding: 20px;
  }

  .preview-card > strong {
    font-size: 34px;
  }

  .editor-footer {
    position: static;
    align-items: stretch;
    flex-direction: column;
    margin-top: 12px;
  }

  .editor-footer > div {
    width: 100%;
  }

  .editor-footer > div :deep(.el-button) {
    flex: 1;
  }

  .full-elements {
    grid-template-columns: repeat(5, minmax(44px, 1fr));
  }

  .power-grid {
    grid-template-columns: 1fr;
  }

  .filters :deep(.el-input),
  .filters :deep(.el-select) {
    width: 100%;
  }

  .value-editor-intro,
  .value-dialog-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .value-editor-actions,
  .value-dialog-footer > div {
    width: 100%;
  }

  .value-editor-actions :deep(.el-button),
  .value-dialog-footer :deep(.el-button) {
    flex: 1;
  }

  .catalog-row {
    grid-template-columns: 1fr;
  }
}
</style>
