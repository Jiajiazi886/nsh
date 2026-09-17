const pad = (value) => String(value).padStart(2, '0')

function formatLocalValue(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function parseLocalValue(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(value || '')
  if (!match) throw new Error('请选择约战时间')
  const parts = match.slice(1).map(Number)
  const date = new Date(parts[0], parts[1] - 1, parts[2], parts[3], parts[4], parts[5] || 0, 0)
  if (
    date.getFullYear() !== parts[0] || date.getMonth() !== parts[1] - 1 || date.getDate() !== parts[2] ||
    date.getHours() !== parts[3] || date.getMinutes() !== parts[4]
  ) throw new Error('约战时间格式不正确')
  return date
}

export function defaultBattleTime(now = new Date()) {
  const current = new Date(now)
  if (Number.isNaN(current.getTime())) throw new Error('当前时间无效')
  for (let offset = 0; offset <= 7; offset += 1) {
    const candidate = new Date(
      current.getFullYear(), current.getMonth(), current.getDate() + offset, 20, 30, 0, 0
    )
    if ((candidate.getDay() === 2 || candidate.getDay() === 4) && candidate >= current) {
      return formatLocalValue(candidate)
    }
  }
  throw new Error('无法计算默认约战时间')
}

export function toLegacyActivityTimes(battleAt) {
  const start = parseLocalValue(battleAt)
  const end = new Date(start.getTime() + 2 * 60 * 60 * 1000)
  return { startsAt: formatLocalValue(start), endsAt: formatLocalValue(end) }
}

export function formatBattleTime(value) {
  if (!value) return '时间未设置'
  return String(value).replace('T', ' ').slice(0, 16)
}
