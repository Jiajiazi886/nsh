<template>
  <div class="battle-page" :class="{ 'battle-public-page': kind === 'public' }">
    <header class="battle-list-heading">
      <div>
        <h2>{{ title }}</h2>
        <p class="battle-muted">{{ pageDescription }}</p>
      </div>
      <Badge v-if="kind === 'public'" variant="secondary">{{ total }} 场可报名约战</Badge>
      <Button v-else variant="outline" size="sm" :disabled="loading" @click="load">
        {{ loading ? '刷新中…' : '刷新' }}
      </Button>
    </header>

    <Card v-if="kind === 'public'" class="battle-public-toolbar">
      <CardHeader class="battle-public-filter-copy">
        <CardTitle class="text-sm">筛选公开约战</CardTitle>
        <CardDescription>按你的职业和活动空位快速查找</CardDescription>
      </CardHeader>
      <CardContent class="battle-public-filter-controls">
        <Select :model-value="profession || '__all__'" @update:model-value="selectProfession">
          <SelectTrigger class="w-full sm:w-[156px]">
            <SelectValue placeholder="全部职业" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="__all__">全部职业</SelectItem>
              <SelectItem v-for="name in professions" :key="name" :value="name">
                <ProfessionTag :name="name" />
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Field orientation="horizontal" class="w-auto">
          <Switch id="vacant-only" :model-value="vacantOnly" @update:model-value="toggleVacant" />
          <FieldLabel for="vacant-only">仅看有空位</FieldLabel>
        </Field>
        <Button variant="outline" size="sm" :disabled="!profession && !vacantOnly" @click="resetPublicFilters">清除筛选</Button>
        <Button variant="outline" size="sm" :disabled="loading" @click="load">{{ loading ? '刷新中…' : '刷新' }}</Button>
      </CardContent>
    </Card>

    <div v-if="error" class="battle-error" role="alert">
      {{ error }}
      <Button variant="outline" size="sm" @click="load">重试</Button>
    </div>

    <p v-if="loading" class="battle-muted" role="status">正在读取约战…</p>
    <div :class="kind === 'mine' ? 'battle-columns' : ''">
      <section v-for="section in sections" :key="section.key" class="battle-panel" :class="{ 'battle-public-panel': kind === 'public' }">
        <h3 v-if="kind !== 'public'">{{ section.title }}</h3>

        <div v-if="kind === 'public'" class="battle-public-grid">
          <Card v-for="activity in section.items" :key="activity.activityId" class="battle-public-card">
            <CardHeader class="battle-public-card-top">
              <div class="flex items-center gap-2">
                <Badge>公开报名</Badge>
                <Badge variant="secondary">{{ activity.orgType === 'guild' ? '帮会' : '俱乐部' }}</Badge>
              </div>
              <strong class="battle-public-vacancy" :class="{ 'is-full': !activity.emptySeats }">
                {{ activity.emptySeats ? `空 ${activity.emptySeats} 席` : '已满员' }}
              </strong>
            </CardHeader>
            <CardContent class="flex flex-1 flex-col gap-3">
              <div class="battle-public-card-title">
                <h3>{{ activity.name }}</h3>
                <p>{{ activity.orgName }}</p>
              </div>
              <div class="battle-public-time">
                <span>约战时间</span><strong>{{ formatBattleTime(activity.startsAt) }}</strong>
              </div>
              <div class="battle-public-stats">
                <div><span>已安排</span><strong>{{ filledSeats(activity) }} 人</strong></div>
                <div><span>总席位</span><strong>{{ activity.totalSeats || '待配置' }}</strong></div>
                <div><span>空缺</span><strong>{{ activity.emptySeats }} 人</strong></div>
              </div>
              <div class="battle-public-shortages">
                <div class="battle-public-shortage-title">
                  <span>职业缺口</span><small>{{ shortageTotal(activity) ? `共缺 ${shortageTotal(activity)} 人` : '暂无缺口' }}</small>
                </div>
                <div v-if="shortageEntries(activity).length" class="battle-public-shortage-tags">
                  <span v-for="([name, count]) in shortageEntries(activity)" :key="name"><ProfessionTag :name="name" />{{ count }}</span>
                </div>
                <p v-else class="battle-muted">当前没有指定职业空位</p>
              </div>
            </CardContent>
            <CardFooter class="battle-public-card-footer">
              <span>{{ activity.emptySeats ? '符合职业要求即可报名' : '当前阵容已满' }}</span>
              <Button size="sm" @click="open(activity)">查看并报名</Button>
            </CardFooter>
          </Card>
        </div>

        <div v-else class="battle-compact-list">
          <Card v-for="activity in section.items" :key="activity.activityId" class="battle-compact-card">
            <CardHeader class="battle-compact-card-head">
              <div class="min-w-0">
                <CardTitle class="truncate text-base">{{ activity.name }}</CardTitle>
                <CardDescription>{{ activity.orgName }} · {{ activity.orgType === 'guild' ? '帮会' : '俱乐部' }} · {{ activity.state === 'ended' ? '已结束' : activity.isPublic ? '公开报名' : '组织内部' }}</CardDescription>
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <Button v-if="kind === 'history' && activity.canManage" variant="outline" size="xs" @click="openImport(activity)">上传 CSV</Button>
                <Button variant="link" size="xs" @click="open(activity)">查看详情</Button>
              </div>
            </CardHeader>
            <CardContent class="battle-compact-card-content">
              <span class="battle-compact-time">{{ formatBattleTime(activity.startsAt) }}</span>
              <Badge variant="outline">{{ filledSeats(activity) }} / {{ activity.totalSeats || 0 }} 人</Badge>
              <span v-for="([name, count]) in shortageEntries(activity)" :key="name" class="battle-shortage-inline">
                <ProfessionTag :name="name" /><strong>{{ count }}</strong>
              </span>
              <span v-if="!activity.totalSeats" class="battle-muted">管理员尚未保存阵容</span>
            </CardContent>
          </Card>
        </div>

        <div v-if="!loading && !error && !section.items.length" class="battle-empty-state">暂无{{ section.title }}</div>
      </section>
    </div>

    <nav v-if="total > pageSize" class="battle-pagination" aria-label="约战分页">
      <Button variant="outline" size="sm" :disabled="loading || page <= 1" @click="previousPage">上一页</Button>
      <span class="battle-muted">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 场</span>
      <Button variant="outline" size="sm" :disabled="loading || page >= totalPages" @click="nextPage">下一页</Button>
    </nav>
    <BattleCsvImport v-model="importVisible" :activity="importActivity" @imported="load" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activityApi } from '@/api/activities'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { loadGuildClassColors } from '@/utils/guildClassColor'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldLabel } from '@/components/ui/field'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { formatBattleTime } from './activityTime.mjs'
import BattleCsvImport from './BattleCsvImport.vue'
import './activity.css'

const props = defineProps({ kind: { type: String, default: 'mine' } })
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref('')
const items = ref([])
const page = ref(1)
const total = ref(0)
const pageSize = 20
const profession = ref('')
const vacantOnly = ref(false)
const importVisible = ref(false)
const importActivity = ref(null)
const isPersonalMine = computed(() => props.kind === 'mine' && route.path.startsWith('/personal/'))
const title = computed(() => ({ mine: '我的约战', public: '找约战', history: '历史约战' })[props.kind])
const pageDescription = computed(() => {
  if (props.kind === 'mine') return isPersonalMine.value ? '只显示本人已经参加的帮会和俱乐部约战。' : '查看所属组织已经保存的活动阵容。'
  if (props.kind === 'public') return '查看公开活动，按职业缺口选择适合你的报名位置。'
  return '查看已经到期的约战；有管理权限时可直接上传对应 CSV。'
})
const professions = ['铁衣', '素问', '血河', '神相', '九灵', '碎梦', '龙吟', '玄机', '潮光', '沧澜', '荒羽', '鸿音']
const sections = computed(() => props.kind === 'mine'
  ? [
      { key: 'guild', title: '帮会活动', items: items.value.filter(activity => activity.orgType === 'guild') },
      { key: 'club', title: '俱乐部活动', items: items.value.filter(activity => activity.orgType === 'club') },
    ]
  : [{ key: props.kind, title: title.value, items: items.value }])
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
let generation = 0

async function load() {
  loadGuildClassColors(true)
  const current = ++generation
  loading.value = true
  error.value = ''
  items.value = []
  try {
    const result = await activityApi.activities({
      kind: props.kind,
      page: page.value,
      pageSize,
      profession: profession.value,
      vacantOnly: vacantOnly.value,
      participatingOnly: isPersonalMine.value,
    })
    if (current !== generation) return
    items.value = result.items
    total.value = result.total
  } catch (loadError) {
    if (current === generation) error.value = loadError.message
  } finally {
    if (current === generation) loading.value = false
  }
}

function search() { page.value = 1; load() }
function selectProfession(value) { profession.value = value === '__all__' ? '' : value; search() }
function toggleVacant(value) { vacantOnly.value = !!value; search() }
function resetPublicFilters() { profession.value = ''; vacantOnly.value = false; search() }
function previousPage() { if (page.value > 1) { page.value--; load() } }
function nextPage() { if (page.value < totalPages.value) { page.value++; load() } }
function open(activity) { router.push(`/battle-information/detail/${encodeURIComponent(activity.activityId)}`) }
function openImport(activity) { importActivity.value = activity; importVisible.value = true }
function filledSeats(activity) { return Math.max(0, (activity.totalSeats || 0) - (activity.emptySeats || 0)) }
function shortageEntries(activity) { return Object.entries(activity.shortages || {}).filter(([, count]) => Number(count) > 0) }
function shortageTotal(activity) { return shortageEntries(activity).reduce((sum, [, count]) => sum + Number(count || 0), 0) }

onMounted(load)
</script>
