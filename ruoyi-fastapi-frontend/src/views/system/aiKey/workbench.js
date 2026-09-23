export const emptyConnectionForm = () => ({
  name: '',
  provider: '',
  baseUrl: '',
  protocol: 'chat_completions',
  model: '',
  apiKey: '',
  maxTokens: 2048,
  temperature: null,
  supportImages: true,
  remark: ''
})

export function connectionToForm(connection) {
  return {
    ...emptyConnectionForm(),
    name: connection?.name || '',
    provider: connection?.provider || '',
    baseUrl: connection?.baseUrl || '',
    protocol: connection?.protocol || 'chat_completions',
    model: connection?.model || '',
    maxTokens: connection?.maxTokens || 2048,
    temperature: connection?.temperature ?? null,
    supportImages: connection?.supportImages !== false,
    remark: connection?.remark || ''
  }
}

export function buildProbePayload(connectionId, form) {
  const payload = {
    baseUrl: String(form.baseUrl || '').trim().replace(/\/$/, ''),
    apiKey: String(form.apiKey || '').trim() || undefined
  }
  if (connectionId) payload.connectionId = connectionId
  return payload
}

export function buildTestPayload(connectionId, form, messages) {
  return {
    ...buildProbePayload(connectionId, form),
    protocol: form.protocol,
    model: String(form.model || '').trim(),
    maxTokens: Number(form.maxTokens) || 2048,
    temperature: form.temperature === '' || form.temperature == null ? undefined : Number(form.temperature),
    messages
  }
}

export function validateImageFile(file, maxBytes = 5 * 1024 * 1024) {
  const allowed = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
  if (!allowed.includes(file?.type)) return '仅支持 PNG、JPEG、WebP 或 GIF 图片'
  if (file.size > maxBytes) return '单张图片不能超过 5 MB'
  return ''
}

export function formatTokenCount(value) {
  if (value === null || value === undefined || value === '') return '未上报'
  const count = Number(value)
  if (!Number.isFinite(count)) return '未上报'
  return `${(count / 10000).toFixed(2)}万（${Math.trunc(count).toLocaleString('en-US')}）`
}
