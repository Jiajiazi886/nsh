<template>
  <div ref="pageRef" class="app-container guild-info-page">
    <section class="guild-hero" v-loading="loading" data-guild-motion="hero">
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
      <div class="metric-panel" data-guild-reveal>
        <span>帮会成员</span>
        <strong>{{ info.member_count || 0 }}</strong>
        <small>当前已审核通过且有效的成员</small>
      </div>
      <div class="metric-panel" data-guild-reveal>
        <span>职业数量</span>
        <strong>{{ info.class_count || 0 }}</strong>
        <small>按主职业统计</small>
      </div>
      <div class="metric-panel" data-guild-reveal>
        <span>人数最多职业</span>
        <strong>{{ topClassLabel }}</strong>
        <small>{{ topClassCountLabel }}</small>
      </div>
    </section>

    <section class="class-section" v-loading="loading" data-guild-reveal>
      <div class="section-heading">
        <div>
          <span class="eyebrow">Class Distribution</span>
          <h3>职业人数</h3>
        </div>
        <span class="total-pill">共 {{ info.member_count || 0 }} 人</span>
      </div>

      <div v-if="classStats.length" class="class-card-grid">
        <el-popover
          v-for="item in classStats"
          :key="item.class_name"
          placement="top"
          trigger="hover"
          :width="260"
          popper-class="guild-player-popover"
        >
          <template #reference>
            <article class="class-card">
              <div class="class-card-top">
                <span class="class-chip" :style="getGuildClassStyle(item.class_name)">{{ item.class_name }}</span>
                <small>{{ getClassPercent(item.count) }}%</small>
              </div>
              <strong>{{ item.count }} 人</strong>
              <div class="class-bar">
                <i :style="{ width: getClassPercent(item.count) + '%', ...getGuildClassBarStyle(item.class_name) }"></i>
              </div>
            </article>
          </template>
          <div class="player-popover">
            <div class="popover-title">{{ item.class_name }} · {{ item.count }} 人</div>
            <div v-if="item.players?.length" class="player-list">
              <span v-for="player in item.players" :key="player.member_id">{{ player.player_name }}</span>
            </div>
            <span v-else class="muted-text">暂无玩家明细</span>
          </div>
        </el-popover>
      </div>
      <p v-if="info.unmatched_count" class="data-note">
        {{ info.unmatched_count }} 名成员的主职未匹配当前职业字典，未纳入职业卡片。
      </p>
      <el-empty v-if="!classStats.length" description="当前帮会还没有可统计的成员" />
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getGuildInfo, updateGuildName } from '@/api/guild/member'
import { useGuildClassColors } from '@/utils/guildClassColor'
import { useGuildPageMotion } from '@/composables/useGuildPageMotion'

const loading = ref(false)
const saving = ref(false)
const pageRef = ref(null)
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

useGuildPageMotion(pageRef)

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
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 20px 50px rgba(38, 50, 69, 0.08);
}

.guild-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 28px;
  padding: 28px;
}

.eyebrow {
  color: #2f6f63;
  font-size: 12px;
  font-weight: 900;
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
  background: #e4f5ee;
  color: #23765e;
  font-weight: 700;
}

.class-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.class-card {
  min-height: 126px;
  padding: 16px;
  border: 1px solid rgba(38, 50, 69, 0.08);
  border-radius: 12px;
  background: #fbfcfd;
  cursor: default;
  transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.class-card:hover {
  border-color: rgba(47, 111, 99, 0.28);
  box-shadow: 0 14px 28px rgba(38, 50, 69, 0.09);
  transform: translate3d(0, -2px, 0);
}

.class-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #263245;
}

.class-card-top small {
  color: #64748b;
  font-weight: 800;
}

.class-card > strong {
  display: block;
  margin-top: 18px;
  color: #111827;
  font-size: 26px;
  line-height: 1;
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
  margin-top: 16px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(38, 50, 69, 0.08);
}

.class-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2f6f63, #7bb99f);
}

.player-popover {
  display: grid;
  gap: 10px;
}

.popover-title {
  color: #111827;
  font-weight: 800;
}

.player-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.player-list span {
  padding: 4px 8px;
  border-radius: 999px;
  background: #f2f5f7;
  color: #334155;
  font-size: 12px;
}

.muted-text {
  color: #64748b;
  font-size: 13px;
}

.data-note {
  margin: 14px 0 0;
  color: #64748b;
  font-size: 13px;
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
