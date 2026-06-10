<template>
  <div class="app-container guild-info-page">
    <section class="guild-hero" v-loading="loading">
      <div class="hero-main">
        <span class="eyebrow">Guild Profile</span>
        <h2>{{ info.guild_name || '未命名帮会' }}</h2>
        <p>这里展示当前帮会的基础信息、成员规模和职业构成。</p>
      </div>
      <div class="hero-editor">
        <label>帮会名称</label>
        <div class="name-row">
          <el-input
            v-model="form.guildName"
            maxlength="30"
            show-word-limit
            placeholder="请输入帮会名称"
            :disabled="saving"
            @keyup.enter="saveGuildName"
          />
          <el-button
            v-hasPermi="['guild:member:edit']"
            type="primary"
            :loading="saving"
            @click="saveGuildName"
          >
            保存
          </el-button>
        </div>
      </div>
    </section>

    <section class="metric-grid" v-loading="loading">
      <div class="metric-panel">
        <span>帮会成员</span>
        <strong>{{ info.member_count || 0 }}</strong>
        <small>当前已审核通过且有效的成员</small>
      </div>
      <div class="metric-panel">
        <span>职业数量</span>
        <strong>{{ info.class_count || 0 }}</strong>
        <small>按主职业统计</small>
      </div>
      <div class="metric-panel">
        <span>人数最多职业</span>
        <strong>{{ topClassLabel }}</strong>
        <small>{{ topClassCountLabel }}</small>
      </div>
    </section>

    <section class="class-section" v-loading="loading">
      <div class="section-heading">
        <div>
          <span class="eyebrow">Class Distribution</span>
          <h3>职业人数</h3>
        </div>
        <span class="total-pill">共 {{ info.member_count || 0 }} 人</span>
      </div>

      <div v-if="classStats.length" class="class-list">
        <div v-for="item in classStats" :key="item.class_name" class="class-row">
          <div class="class-row-title">
            <strong class="class-chip" :style="getGuildClassStyle(item.class_name)">{{ item.class_name }}</strong>
            <span>{{ item.count }} 人</span>
          </div>
          <div class="class-bar">
            <i :style="{ width: getClassPercent(item.count) + '%', ...getGuildClassBarStyle(item.class_name) }"></i>
          </div>
        </div>
      </div>
      <el-empty v-else description="当前帮会还没有可统计的成员" />
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getGuildInfo, updateGuildName } from '@/api/guild/member'
import { useGuildClassColors } from '@/utils/guildClassColor'

const loading = ref(false)
const saving = ref(false)
const info = ref({
  guild_name: '',
  member_count: 0,
  class_count: 0,
  class_stats: []
})
const form = reactive({
  guildName: ''
})
const { getGuildClassBarStyle, getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

const classStats = computed(() => info.value.class_stats || [])
const topClass = computed(() => classStats.value[0] || null)
const topClassLabel = computed(() => topClass.value?.class_name || '--')
const topClassCountLabel = computed(() => (topClass.value ? `${topClass.value.count} 人` : '暂无成员数据'))

function getClassPercent(count) {
  const total = info.value.member_count || 0
  if (!total) return 0
  return Math.max(8, Math.round((count / total) * 100))
}

async function fetchGuildInfo() {
  loading.value = true
  try {
    const res = await getGuildInfo()
    info.value = res.data || {}
    form.guildName = info.value.guild_name || ''
  } finally {
    loading.value = false
  }
}

async function saveGuildName() {
  const name = form.guildName.trim()
  if (!name) {
    ElMessage.warning('请输入帮会名称')
    return
  }
  saving.value = true
  try {
    await updateGuildName(name)
    ElMessage.success('帮会名称已保存')
    await fetchGuildInfo()
  } finally {
    saving.value = false
  }
}

function handleMemberDataChanged() {
  fetchGuildInfo()
}

onMounted(() => {
  fetchGuildInfo()
  loadGuildClassColors()
  window.addEventListener('guild-member-data-changed', handleMemberDataChanged)
})

onBeforeUnmount(() => {
  window.removeEventListener('guild-member-data-changed', handleMemberDataChanged)
})
</script>

<style scoped>
.guild-info-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.guild-hero,
.metric-panel,
.class-section {
  border: 1px solid rgba(38, 50, 69, 0.08);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.72)),
    radial-gradient(circle at 88% 18%, rgba(232, 215, 84, 0.26), transparent 28%),
    radial-gradient(circle at 12% 88%, rgba(105, 71, 242, 0.16), transparent 32%);
  box-shadow: 0 20px 50px rgba(38, 50, 69, 0.08);
}

.guild-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 28px;
  padding: 28px;
}

.eyebrow {
  color: #6947f2;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.hero-main h2 {
  margin: 10px 0 8px;
  color: #111827;
  font-size: 32px;
}

.hero-main p {
  margin: 0;
  color: #64748b;
}

.hero-editor {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}

.hero-editor label {
  color: #263245;
  font-weight: 700;
}

.name-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.metric-panel {
  padding: 20px;
}

.metric-panel span,
.metric-panel small {
  display: block;
  color: #64748b;
}

.metric-panel strong {
  display: block;
  margin: 8px 0;
  color: #111827;
  font-size: 30px;
  line-height: 1.1;
}

.class-section {
  padding: 24px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-heading h3 {
  margin: 6px 0 0;
  color: #111827;
  font-size: 22px;
}

.total-pill {
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(105, 71, 242, 0.1);
  color: #6947f2;
  font-weight: 700;
}

.class-list {
  display: grid;
  gap: 12px;
}

.class-row {
  padding: 14px;
  border: 1px solid rgba(38, 50, 69, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
}

.class-row-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: #263245;
}

.class-row-title span {
  color: #64748b;
}

.class-chip {
  display: inline-flex;
  align-items: center;
  min-width: 54px;
  justify-content: center;
  padding: 3px 10px;
  border: 1px solid currentColor;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  font-size: 13px;
}

.class-bar {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(38, 50, 69, 0.08);
}

.class-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6947f2, #e8d754, #65d5c8);
}

@media (max-width: 900px) {
  .guild-hero,
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .name-row {
    grid-template-columns: 1fr;
  }
}
</style>
