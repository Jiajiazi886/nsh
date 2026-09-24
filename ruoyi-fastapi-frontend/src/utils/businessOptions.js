export const NORMAL_DISABLE_OPTIONS = Object.freeze([
  { label: '正常', value: '0', elTagType: 'success' },
  { label: '停用', value: '1', elTagType: 'danger' }
])

export const SHOW_HIDE_OPTIONS = Object.freeze([
  { label: '显示', value: '0', elTagType: 'success' },
  { label: '隐藏', value: '1', elTagType: 'danger' }
])

export const JOB_STATUS_OPTIONS = Object.freeze([
  { label: '正常', value: '0', elTagType: 'success' },
  { label: '暂停', value: '1', elTagType: 'danger' }
])

export const JOB_GROUP_OPTIONS = Object.freeze([
  { label: '默认', value: 'default', elTagType: 'info' },
  { label: '数据库', value: 'sqlalchemy', elTagType: 'primary' },
  { label: 'Redis', value: 'redis', elTagType: 'warning' }
])

export const JOB_EXECUTOR_OPTIONS = Object.freeze([
  { label: '默认', value: 'default', elTagType: 'info' },
  { label: '进程池', value: 'processpool', elTagType: 'primary' }
])

export const NOTICE_TYPE_OPTIONS = Object.freeze([
  { label: '通知', value: '1', elTagType: 'warning' },
  { label: '公告', value: '2', elTagType: 'success' }
])

export const NOTICE_STATUS_OPTIONS = Object.freeze([
  { label: '正常', value: '0', elTagType: 'success' },
  { label: '关闭', value: '1', elTagType: 'danger' }
])

export const COMMON_STATUS_OPTIONS = Object.freeze([
  { label: '成功', value: '0', elTagType: 'success' },
  { label: '失败', value: '1', elTagType: 'danger' }
])

export function findBusinessOption(options, value) {
  return options.find(item => String(item.value) === String(value))
}

export function businessOptionLabel(options, value) {
  return findBusinessOption(options, value)?.label || String(value ?? '')
}

export function businessOptionType(options, value) {
  return findBusinessOption(options, value)?.elTagType || 'info'
}
