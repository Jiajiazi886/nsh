<template>
  <Dialog v-model:open="visible">
    <DialogContent class="battle-report-dialog sm:max-w-[85vw]">
      <DialogHeader>
        <DialogTitle>战报数据</DialogTitle>
        <DialogDescription>按职业查看本场约战已经导入的 CSV 数据。</DialogDescription>
      </DialogHeader>

      <div class="battle-report-dialog-body">
        <p v-if="loading" class="battle-muted" role="status">正在读取战报…</p>
        <p v-if="error" class="battle-error" role="alert">{{ error }} <Button variant="outline" size="sm" @click="load">重试</Button></p>
        <template v-if="report">
          <div class="battle-report-heading">
            <h3>{{ report.name }}</h3>
            <p>{{ report.battleDate }} · {{ report.association }}</p>
          </div>
          <p v-if="!report.players.length" class="battle-empty-note">暂无战报数据</p>
          <details v-for="folder in folders" :key="folder.profession" class="battle-report-folder">
            <summary><ProfessionTag :name="folder.profession" /> · {{ folder.players.length }} 人</summary>
            <div class="battle-report-table-wrap">
              <table class="battle-report-table">
                <thead>
                  <tr>
                    <th>玩家</th>
                    <th>帮会</th>
                    <th v-for="metric in metrics" :key="metric[0]">{{ metric[1] }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="player in folder.players" :key="player.playerId || player.name">
                    <td>{{ player.name }}</td>
                    <td>{{ player.guildName }}</td>
                    <td v-for="metric in metrics" :key="metric[0]">{{ player.metrics?.[metric[0]] ?? 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </template>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="visible = false">关闭</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { activityApi } from '@/api/activities'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { loadGuildClassColors } from '@/utils/guildClassColor'
import { professionFolders } from './model.mjs'

const visible = ref(false)
const loading = ref(false)
const error = ref('')
const report = ref(null)
const id = ref('')
const folders = computed(() => professionFolders(report.value?.players || []))
const metrics = [['kills', '击败'], ['assists', '助攻'], ['resources', '资源'], ['dmg_to_players', '对玩家伤害'], ['healing', '治疗值'], ['dmg_taken', '承受伤害'], ['deaths', '重伤']]

async function load() {
  loadGuildClassColors(true)
  loading.value = true
  error.value = ''
  report.value = null
  try {
    report.value = await activityApi.activityReport(id.value)
  } catch (loadError) {
    error.value = loadError.message
  } finally {
    loading.value = false
  }
}
function open(reportId) {
  id.value = reportId
  visible.value = true
  load()
}

defineExpose({ open })
</script>

<style scoped>
.battle-report-dialog-body{max-height:70vh;overflow:auto}.battle-report-heading h3{margin:0}.battle-report-heading p{margin:4px 0 12px;color:#687386}.battle-report-folder{margin-top:10px;border:1px solid #dfe4eb;border-radius:7px;background:#fff}.battle-report-folder summary{cursor:pointer;padding:10px 12px;font-weight:600}.battle-report-table-wrap{overflow:auto;border-top:1px solid #e4e8ee}.battle-report-table{width:100%;min-width:900px;border-collapse:collapse;font-size:13px}.battle-report-table th,.battle-report-table td{padding:8px 10px;border-bottom:1px solid #edf0f4;text-align:left;white-space:nowrap}.battle-report-table th{background:#f7f8fa;color:#4b5565;font-weight:600}.battle-report-table tbody tr:last-child td{border-bottom:0}
</style>
