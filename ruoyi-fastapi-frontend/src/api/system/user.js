import request from '@/utils/request'
import { parseStrEmpty } from "@/utils/ruoyi";

// 查询用户列表
export function listUser(query) {
  return request({
    url: '/system/user/list',
    method: 'get',
    params: query
  })
}

// 查询用户详细
export function getUser(userId) {
  return request({
    url: '/system/user/' + parseStrEmpty(userId),
    method: 'get'
  })
}

// 新增用户
export function addUser(data) {
  return request({
    url: '/system/user',
    method: 'post',
    data: data
  })
}

// 修改用户
export function updateUser(data) {
  return request({
    url: '/system/user',
    method: 'put',
    data: data
  })
}

// 删除用户
export function delUser(userId) {
  return request({
    url: '/system/user/' + userId,
    method: 'delete'
  })
}

// 用户密码重置
export function resetUserPwd(userId, password) {
  const data = {
    userId,
    password
  }
  return request({
    url: '/system/user/resetPwd',
    method: 'put',
    data: data
  })
}

// 用户状态修改
export function changeUserStatus(userId, status) {
  const data = {
    userId,
    status
  }
  return request({
    url: '/system/user/changeStatus',
    method: 'put',
    data: data
  })
}

// 用户VIP授权修改
export function changeUserVip(userId, isVip, vipExpireTime) {
  const data = {
    userId,
    isVip,
    vipExpireTime
  }
  return request({
    url: '/system/user/changeVip',
    method: 'put',
    data: data
  })
}

// 批量修改用户VIP授权；新VIP识图赠送次数由系统设置决定
export function batchUserVip(userIds, isVip, vipExpireTime) {
  return request({
    url: '/system/user/batchVip',
    method: 'put',
    data: {
      userIds,
      isVip,
      vipExpireTime
    }
  })
}

// 帮会管理赞助状态修改
export function changeUserSponsor(userId, sponsorEnabled) {
  return request({
    url: '/system/user/changeSponsor',
    method: 'put',
    data: {
      userId,
      sponsorEnabled
    }
  })
}

// 用户最大内功数修改
export function changeInternalPowerLimit(userId, maxInternalPowerCount) {
  return request({
    url: '/system/user/changeInternalPowerLimit',
    method: 'put',
    data: {
      userId,
      maxInternalPowerCount
    }
  })
}

// 用户AI识图次数修改
export function changeAiRecognitionCount(userId, aiImageRecognitionCount) {
  return request({
    url: '/system/user/changeAiRecognitionCount',
    method: 'put',
    data: {
      userId,
      aiImageRecognitionCount
    }
  })
}

// 用户VIP AI识图次数修改
export function changeVipAiRecognitionCount(userId, vipAiImageRecognitionCount) {
  return request({
    url: '/system/user/changeVipAiRecognitionCount',
    method: 'put',
    data: {
      userId,
      vipAiImageRecognitionCount
    }
  })
}

// 查询新用户默认普通AI识图次数
export function getDefaultAiRecognitionCount() {
  return request({
    url: '/system/user/default-ai-recognition-count',
    method: 'get'
  })
}

// 修改新用户默认普通AI识图次数并同步老用户
export function updateDefaultAiRecognitionCount(aiImageRecognitionCount) {
  return request({
    url: '/system/user/default-ai-recognition-count',
    method: 'put',
    data: {
      aiImageRecognitionCount
    }
  })
}

// 查询VIP开通时自动赠送的VIP识图次数
export function getVipAiRecognitionGrantCount() {
  return request({
    url: '/system/user/vip-ai-recognition-grant-count',
    method: 'get'
  })
}

// 修改VIP开通时自动赠送的VIP识图次数
export function updateVipAiRecognitionGrantCount(vipAiImageRecognitionGrantCount) {
  return request({
    url: '/system/user/vip-ai-recognition-grant-count',
    method: 'put',
    data: {
      vipAiImageRecognitionGrantCount
    }
  })
}

// 批量修改用户最大内功数
export function batchInternalPowerLimit(userIds, maxInternalPowerCount) {
  return request({
    url: '/system/user/batchInternalPowerLimit',
    method: 'put',
    data: {
      userIds,
      maxInternalPowerCount
    }
  })
}

// 查询用户个人信息
export function getUserProfile() {
  return request({
    url: '/system/user/profile',
    method: 'get'
  })
}

// 修改用户个人信息
export function updateUserProfile(data) {
  return request({
    url: '/system/user/profile',
    method: 'put',
    data: data
  })
}

// 用户密码重置
export function updateUserPwd(oldPassword, newPassword) {
  const data = {
    oldPassword,
    newPassword
  }
  return request({
    url: '/system/user/profile/updatePwd',
    method: 'put',
    data: data
  })
}

// 用户头像上传
export function uploadAvatar(data) {
  return request({
    url: '/system/user/profile/avatar',
    method: 'post',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    data: data
  })
}

// 查询授权角色
export function getAuthRole(userId) {
  return request({
    url: '/system/user/authRole/' + userId,
    method: 'get'
  })
}

// 保存授权角色
export function updateAuthRole(data) {
  return request({
    url: '/system/user/authRole',
    method: 'put',
    params: data
  })
}

// 查询注册用户清理规则
export function getRegisterCleanupRule() {
  return request({
    url: '/system/user/register-cleanup-rule',
    method: 'get'
  })
}

// 修改注册用户清理规则
export function updateRegisterCleanupRule(data) {
  return request({
    url: '/system/user/register-cleanup-rule',
    method: 'put',
    data: data
  })
}
