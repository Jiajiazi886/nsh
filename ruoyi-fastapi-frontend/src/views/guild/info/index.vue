<template>
  <div class="app-container flex flex-col gap-4">
    <p v-if="loading" class="text-sm text-muted-foreground" role="status">正在读取帮会信息…</p>
    <p v-if="error" class="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">{{ error }}</p>
    <p v-if="success" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" role="status">{{ success }}</p>
    <Card>
      <CardHeader class="md:grid md:grid-cols-[minmax(0,1fr)_minmax(320px,520px)] md:items-center md:gap-6">
        <div class="flex min-w-0 flex-col gap-1">
          <CardTitle class="truncate text-xl">{{ info.guild_name || '未命名帮会' }}</CardTitle>
          <CardDescription>帮会基本信息和当前成员职业构成</CardDescription>
        </div>
        <div class="mt-4 flex gap-2 md:mt-0">
          <Input
            v-model="form.guildName"
            maxlength="30"
            placeholder="请输入帮会名称"
            :disabled="saving"
            @keyup.enter="saveGuildName"
          />
          <Button
            v-hasPermi="['guild:member:edit']"
            :disabled="saving"
            @click="saveGuildName"
          >
            {{ saving ? '保存中…' : '保存' }}
          </Button>
        </div>
      </CardHeader>
    </Card>

    <Card>
      <CardHeader class="flex-row items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <CardTitle class="text-base">帮会成员</CardTitle>
          <CardDescription>当前已审核通过且有效的成员</CardDescription>
        </div>
        <strong class="text-3xl tabular-nums text-foreground">{{ info.member_count || 0 }}</strong>
      </CardHeader>
    </Card>

    <Card>
      <CardHeader class="flex-row items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <CardTitle class="text-base">职业人数</CardTitle>
          <CardDescription>按成员主职业统计，点击职业可查看玩家名单</CardDescription>
        </div>
        <Badge variant="secondary">共 {{ info.member_count || 0 }} 人</Badge>
      </CardHeader>
      <CardContent>
        <Accordion v-if="classStats.length" type="single" collapsible class="rounded-lg border">
          <AccordionItem
            v-for="item in classStats"
            :key="item.class_name"
            :value="item.class_name"
            class="px-3 last:border-b-0"
          >
            <AccordionTrigger class="py-3 hover:no-underline">
              <span class="flex flex-1 items-center justify-between gap-3 pr-3">
                <ProfessionTag :name="item.class_name" />
                <strong class="text-sm tabular-nums">{{ item.count }} 人</strong>
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <div v-if="item.players?.length" class="flex flex-wrap gap-2">
                <Badge v-for="player in item.players" :key="player.member_id" variant="outline">
                  {{ player.player_name }}
                </Badge>
              </div>
              <span v-else class="text-sm text-muted-foreground">暂无玩家明细</span>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        <div v-else class="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          当前帮会还没有可统计的成员
        </div>
        <p v-if="info.unmatched_count" class="mt-3 text-sm text-muted-foreground">
          {{ info.unmatched_count }} 名成员的主职未匹配当前职业字典，未纳入职业统计。
        </p>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { getGuildInfo, updateGuildName } from '@/api/guild/member'
import { loadGuildClassColors } from '@/utils/guildClassColor'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const info = ref({ guild_name: '', member_count: 0, class_stats: [] })
const form = reactive({ guildName: '' })
const classStats = computed(() => info.value.class_stats || [])

async function fetchGuildInfo() {
  loading.value = true
  error.value = ''
  try {
    const res = await getGuildInfo()
    info.value = res.data || {}
    form.guildName = info.value.guild_name || ''
  } catch (loadError) {
    error.value = loadError.message || '读取帮会信息失败'
  } finally {
    loading.value = false
  }
}

async function saveGuildName() {
  const name = form.guildName.trim()
  error.value = ''
  success.value = ''
  if (!name) {
    error.value = '请输入帮会名称'
    return
  }
  saving.value = true
  try {
    await updateGuildName(name)
    success.value = '帮会名称已保存。'
    await fetchGuildInfo()
  } catch (saveError) {
    error.value = saveError.message || '保存帮会名称失败'
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
