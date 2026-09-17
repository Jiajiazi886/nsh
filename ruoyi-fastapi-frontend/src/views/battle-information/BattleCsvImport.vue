<template>
  <Dialog v-model:open="visible">
    <DialogContent class="battle-import-dialog sm:max-w-[640px]" @close-auto-focus="reset">
      <DialogHeader>
        <DialogTitle>上传 CSV 战报</DialogTitle>
        <DialogDescription>文件会直接归属当前约战，不需要再输入战报 ID。</DialogDescription>
      </DialogHeader>

      <div class="battle-import">
        <label
          class="battle-import-drop"
          :class="{ 'is-dragging': dragging }"
          @dragenter.prevent="dragging = true"
          @dragover.prevent
          @dragleave.prevent="dragging = false"
          @drop.prevent="readDroppedFile"
        >
          <input class="battle-import-file-input" type="file" accept=".csv,text/csv" @change="readFileInput">
          <strong>{{ fileName || '拖入 CSV，或点击选择文件' }}</strong>
          <span>{{ fileName ? '点击可重新选择' : '仅支持一个 .csv 文件' }}</span>
        </label>
        <div v-if="fileName" class="battle-import-file-actions">
          <span class="battle-muted">已选择：{{ fileName }}</span>
          <Button variant="ghost" size="sm" type="button" @click="resetFile">移除文件</Button>
        </div>

        <p v-if="parseError" class="battle-error" role="alert">{{ parseError }}</p>
        <template v-if="parsed">
          <div class="battle-import-summary">
            <span><strong>{{ parsed.records.length }}</strong> 名玩家</span>
            <span><strong>{{ parsed.guilds.length }}</strong> 个帮会</span>
            <span v-for="guild in parsed.guilds" :key="guild.name">{{ guild.name }} {{ guild.actualCount }} 人</span>
          </div>
          <p v-for="warning in parsed.warnings" :key="warning" class="battle-import-warning">{{ warning }}</p>

          <FieldGroup class="battle-import-form">
            <Field>
              <FieldLabel for="battle-import-date">比赛日期</FieldLabel>
              <Input id="battle-import-date" v-model="form.battleDate" type="date" />
            </Field>
            <Field>
              <FieldLabel>比赛结果</FieldLabel>
              <Select v-model="resultSelection">
                <SelectTrigger><SelectValue placeholder="可不填写" /></SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="__unset__">不填写</SelectItem>
                    <SelectItem value="胜利">胜利</SelectItem>
                    <SelectItem value="失败">失败</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
            <Field>
              <FieldLabel for="battle-import-guild">我方帮会</FieldLabel>
              <Input id="battle-import-guild" v-model="form.myGuildName" maxlength="64" placeholder="可根据文件名自动填写" />
            </Field>
            <Field>
              <FieldLabel for="battle-import-opponent">对手帮会</FieldLabel>
              <Input id="battle-import-opponent" v-model="form.opponentName" maxlength="50" placeholder="可根据文件名自动填写" />
            </Field>
            <Field class="battle-import-remark">
              <FieldLabel for="battle-import-remark">备注</FieldLabel>
              <Textarea id="battle-import-remark" v-model="form.remark" maxlength="500" placeholder="可选" />
            </Field>
          </FieldGroup>
        </template>
      </div>

      <DialogFooter>
        <Button variant="outline" type="button" @click="visible = false">取消</Button>
        <Button type="button" :disabled="submitting || !parsed || !!parseError" @click="submit">{{ submitting ? '导入中…' : '确认导入' }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { activityApi } from '@/api/activities'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { inferBattleFileInfo, parseBattleCsv } from './battleCsv.mjs'

const props = defineProps({ modelValue: { type: Boolean, default: false }, activity: { type: Object, default: null } })
const emit = defineEmits(['update:modelValue', 'imported'])
const visible = ref(false)
const fileName = ref('')
const parsed = ref(null)
const parseError = ref('')
const submitting = ref(false)
const dragging = ref(false)
const form = reactive({ battleDate: '', battleResult: '', myGuildName: '', opponentName: '', remark: '' })
const resultSelection = computed({
  get: () => form.battleResult || '__unset__',
  set: value => { form.battleResult = value === '__unset__' ? '' : value },
})

watch(() => props.modelValue, value => { visible.value = value })
watch(visible, value => emit('update:modelValue', value))

function activityDate() { return String(props.activity?.startsAt || '').slice(0, 10) }
function resetFile() {
  fileName.value = ''
  parsed.value = null
  parseError.value = ''
}
function reset() {
  dragging.value = false
  resetFile()
  Object.assign(form, { battleDate: activityDate(), battleResult: '', myGuildName: '', opponentName: '', remark: '' })
}

async function readFile(file) {
  resetFile()
  fileName.value = file?.name || ''
  if (!file || !/\.csv$/i.test(fileName.value)) {
    parseError.value = '只支持 .csv 文件'
    return
  }
  try {
    parsed.value = parseBattleCsv(await file.text())
    Object.assign(form, inferBattleFileInfo(fileName.value, activityDate()))
  } catch (error) {
    parseError.value = error?.message || 'CSV 解析失败'
  }
}
function readFileInput(event) {
  const files = Array.from(event.target.files || [])
  event.target.value = ''
  if (files.length > 1) {
    parseError.value = '一次只能选择一个 CSV 文件'
    return
  }
  return readFile(files[0])
}
function readDroppedFile(event) {
  dragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length !== 1) {
    parseError.value = files.length ? '一次只能选择一个 CSV 文件' : '没有读取到文件'
    return
  }
  return readFile(files[0])
}

async function submit() {
  if (!parsed.value || submitting.value) return
  if (!form.battleDate) {
    parseError.value = '请选择比赛日期'
    return
  }
  submitting.value = true
  parseError.value = ''
  try {
    const result = await activityApi.importActivityReport(props.activity.activityId, {
      expectedRevision: props.activity.revision,
      operationKey: crypto.randomUUID(),
      fileName: fileName.value,
      battleDate: form.battleDate,
      battleResult: form.battleResult,
      myGuildName: form.myGuildName,
      opponentName: form.opponentName,
      remark: form.remark,
      records: parsed.value.records,
    })
    visible.value = false
    emit('imported', result)
  } catch (error) {
    parseError.value = error?.message || '导入失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.battle-import-drop{display:flex;min-height:132px;cursor:pointer;flex-direction:column;align-items:center;justify-content:center;gap:6px;border:1px dashed #aeb8c6;border-radius:8px;background:#fafbfc;color:#273142;text-align:center;transition:border-color .15s ease,background .15s ease}.battle-import-drop:hover,.battle-import-drop.is-dragging{border-color:#2563eb;background:#eff6ff}.battle-import-drop span{font-size:12px;color:#687386}.battle-import-file-input{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
.battle-import-file-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:6px}.battle-import-summary{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 8px;padding:10px 12px;background:#f6f7f9;border:1px solid #e0e4ea;border-radius:4px;font-size:13px}.battle-import-summary span{padding-right:10px;border-right:1px solid #dce1e8}.battle-import-summary span:last-child{border-right:0}.battle-import-warning{margin:6px 0;color:#986900;font-size:13px}.battle-import-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 12px;margin-top:12px}.battle-import-remark{grid-column:1/-1}@media(max-width:700px){.battle-import-form{grid-template-columns:1fr}.battle-import-remark{grid-column:auto}}
</style>
