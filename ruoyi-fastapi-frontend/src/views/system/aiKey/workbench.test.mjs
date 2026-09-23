import assert from 'node:assert/strict'
import { buildProbePayload, buildTestPayload, connectionToForm, formatTokenCount, validateImageFile } from './workbench.js'

const form = connectionToForm({
  name: '主连接',
  baseUrl: 'https://api.example.com/v1',
  model: 'demo',
  maxTokens: 4096,
  supportImages: false
})
assert.equal(form.apiKey, '')
assert.equal(form.supportImages, false)

assert.deepEqual(buildProbePayload(7, { baseUrl: 'https://api.example.com/v1/', apiKey: '' }), {
  connectionId: 7,
  baseUrl: 'https://api.example.com/v1',
  apiKey: undefined
})

const payload = buildTestPayload(7, { ...form, temperature: 0 }, [{ role: 'user', content: '你好', images: [] }])
assert.equal(payload.temperature, 0)
assert.equal(payload.connectionId, 7)
assert.equal(payload.messages.length, 1)

assert.match(validateImageFile({ type: 'text/plain', size: 10 }), /仅支持/)
assert.match(validateImageFile({ type: 'image/png', size: 6 * 1024 * 1024 }), /5 MB/)
assert.equal(validateImageFile({ type: 'image/png', size: 10 }), '')
assert.equal(formatTokenCount(823), '0.08万（823）')
assert.equal(formatTokenCount(12345), '1.23万（12,345）')
assert.equal(formatTokenCount(null), '未上报')

console.log('AI connection workbench utilities passed')
