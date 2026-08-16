import assert from 'node:assert/strict'
import { applyAiRecognitionQuota } from './aiRecognitionQuota.js'

const normalFirstStore = { aiImageRecognitionCount: 3, vipAiImageRecognitionCount: 2 }
applyAiRecognitionQuota(normalFirstStore, {}, 2)
assert.deepEqual(normalFirstStore, { aiImageRecognitionCount: 1, vipAiImageRecognitionCount: 2 })

const vipFallbackStore = { aiImageRecognitionCount: 1, vipAiImageRecognitionCount: 3 }
applyAiRecognitionQuota(vipFallbackStore, {}, 2)
assert.deepEqual(vipFallbackStore, { aiImageRecognitionCount: 0, vipAiImageRecognitionCount: 2 })

const responseStore = { aiImageRecognitionCount: 8, vipAiImageRecognitionCount: 5 }
applyAiRecognitionQuota(responseStore, {
  remainingAiImageRecognitionCount: 4,
  remainingVipAiImageRecognitionCount: 3
}, 9)
assert.deepEqual(responseStore, { aiImageRecognitionCount: 4, vipAiImageRecognitionCount: 3 })

console.log('aiRecognitionQuota tests passed')
