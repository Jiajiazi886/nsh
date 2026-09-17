import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const schedule = fs.readFileSync(new URL('./ScheduleEntry.vue', import.meta.url), 'utf8')
const list = fs.readFileSync(new URL('./ListView.vue', import.meta.url), 'utf8')
const detail = fs.readFileSync(new URL('./detail.vue', import.meta.url), 'utf8')
const csvImport = fs.readFileSync(new URL('./BattleCsvImport.vue', import.meta.url), 'utf8')
const reportDialog = fs.readFileSync(new URL('./ReportDialog.vue', import.meta.url), 'utf8')
const lineupEditor = fs.readFileSync(new URL('./LineupEditor.vue', import.meta.url), 'utf8')
const playerCenter = fs.readFileSync(new URL('../personal/profileEdit/index.vue', import.meta.url), 'utf8')
const guildInfo = fs.readFileSync(new URL('../guild/info/index.vue', import.meta.url), 'utf8')
const passwordForm = fs.readFileSync(new URL('../../components/AccountPasswordForm/index.vue', import.meta.url), 'utf8')
const analysis = fs.readFileSync(new URL('../guild/analysis/index.vue', import.meta.url), 'utf8')

test('schedule entry uses shadcn-vue for ordinary controls and accessible composition', () => {
  for (const marker of [
    '@/components/ui/button',
    '@/components/ui/card',
    '@/components/ui/dialog',
    '@/components/ui/field',
    '@/components/ui/input',
    '@/components/ui/select',
    '@/components/ui/textarea',
    '<DialogTitle>',
    '<SelectGroup>',
    '<FieldGroup',
  ]) assert.match(schedule, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(schedule, /<el-/)
  assert.match(schedule, /type="datetime-local"/)
})

test('battle lists use shadcn-vue filters and button pagination', () => {
  for (const marker of [
    '@/components/ui/select',
    '@/components/ui/switch',
    '<SelectGroup>',
    '<Switch',
    '上一页',
    '下一页',
  ]) assert.match(list, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(list, /<el-(select|option|checkbox|pagination)/)
  assert.doesNotMatch(list, /v-loading=/)
})

test('battle detail uses shadcn-vue controls and an in-page confirmation dialog', () => {
  for (const marker of [
    '@/components/ui/button',
    '@/components/ui/select',
    '@/components/ui/alert-dialog',
    '<AlertDialogTitle>',
    '<SelectGroup>',
  ]) assert.match(detail, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(detail, /<el-(button|select|option|empty)/)
  assert.doesNotMatch(detail, /v-loading=/)
  assert.doesNotMatch(detail, /ElMessageBox/)
})

test('CSV import uses a shadcn dialog and fields around the native file input', () => {
  for (const marker of [
    '@/components/ui/dialog',
    '@/components/ui/field',
    '@/components/ui/input',
    '@/components/ui/select',
    '@/components/ui/textarea',
    'type="file"',
    '<DialogTitle>',
    '<FieldGroup',
  ]) assert.match(csvImport, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(csvImport, /<el-/)
  assert.doesNotMatch(csvImport, /ElMessage|@element-plus/)
})

test('report viewer uses a shadcn dialog and a semantic table', () => {
  for (const marker of [
    '@/components/ui/dialog',
    '@/components/ui/button',
    '<DialogTitle>',
    '<table',
    '<thead>',
    '<tbody>',
  ]) assert.match(reportDialog, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(reportDialog, /<el-/)
  assert.doesNotMatch(reportDialog, /v-loading=/)
})

test('player center uses shadcn fields, switches and dialogs', () => {
  for (const marker of [
    '@/components/ui/field',
    '@/components/ui/input',
    '@/components/ui/select',
    '@/components/ui/switch',
    '@/components/ui/textarea',
    '@/components/ui/dialog',
    '@/components/ui/alert-dialog',
    '<FieldGroup',
    '<AlertDialogTitle>',
  ]) assert.match(playerCenter, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(playerCenter, /<el-/)
  assert.doesNotMatch(playerCenter, /ElMessage|v-loading=/)
})

test('guild information uses inline shadcn status without Element loading or messages', () => {
  assert.match(guildInfo, /role="status"/)
  assert.match(guildInfo, /role="alert"/)
  assert.doesNotMatch(guildInfo, /ElMessage|v-loading=/)
})

test('lineup editor uses shadcn controls and local dialogs without Element Plus', () => {
  for (const marker of [
    '@/components/ui/button',
    '@/components/ui/dialog',
    '@/components/ui/alert-dialog',
    '@/components/ui/input',
    '@/components/ui/select',
    '<DialogTitle>',
    '<AlertDialogTitle>',
    '<SelectGroup>',
  ]) assert.match(lineupEditor, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))

  assert.doesNotMatch(lineupEditor, /<el-/)
  assert.doesNotMatch(lineupEditor, /ElMessage|ElMessageBox|v-loading=/)
})

test('account password form uses shadcn fields and inline feedback', () => {
  for (const marker of ['@/components/ui/button', '@/components/ui/field', '@/components/ui/input', '<FieldGroup', 'role="alert"', 'role="status"']) {
    assert.match(passwordForm, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))
  }
  assert.doesNotMatch(passwordForm, /<el-|\$modal|getCurrentInstance/)
})

test('analysis box selectors use shadcn select composition', () => {
  assert.match(analysis, /@\/components\/ui\/select/)
  assert.match(analysis, /<SelectGroup>/)
  assert.doesNotMatch(analysis, /<select|<option/)
})
