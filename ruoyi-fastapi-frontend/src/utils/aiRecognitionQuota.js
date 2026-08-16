function nonNegativeNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? Math.max(0, number) : null
}

export function applyAiRecognitionQuota(userStore, response = {}, consumedCount = 0) {
  const payload = response?.data || response || {}
  const remainingNormal = nonNegativeNumber(
    payload.remainingCount ?? payload.remainingAiImageRecognitionCount
  )
  const remainingVip = nonNegativeNumber(payload.remainingVipAiImageRecognitionCount)

  if (remainingNormal !== null) userStore.aiImageRecognitionCount = remainingNormal
  if (remainingVip !== null) userStore.vipAiImageRecognitionCount = remainingVip
  if (remainingNormal !== null || remainingVip !== null) return

  let remainingConsumption = Math.max(0, Number(consumedCount || 0))
  const currentNormal = Math.max(0, Number(userStore.aiImageRecognitionCount || 0))
  const normalConsumption = Math.min(currentNormal, remainingConsumption)
  userStore.aiImageRecognitionCount = currentNormal - normalConsumption
  remainingConsumption -= normalConsumption
  userStore.vipAiImageRecognitionCount = Math.max(
    0,
    Number(userStore.vipAiImageRecognitionCount || 0) - remainingConsumption
  )
}
