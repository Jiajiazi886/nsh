<template>
  <form class="account-password-form" @submit.prevent="submit">
    <FieldGroup>
      <Field :data-invalid="!!errors.oldPassword">
        <FieldLabel for="old-password">旧密码</FieldLabel>
        <Input id="old-password" v-model="user.oldPassword" type="password" autocomplete="current-password" placeholder="请输入旧密码" :aria-invalid="!!errors.oldPassword" @input="errors.oldPassword = ''" />
        <FieldError :errors="[errors.oldPassword]" />
      </Field>
      <Field :data-invalid="!!errors.newPassword">
        <FieldLabel for="new-password">新密码</FieldLabel>
        <Input id="new-password" v-model="user.newPassword" type="password" autocomplete="new-password" placeholder="请输入新密码" :aria-invalid="!!errors.newPassword" @input="errors.newPassword = ''" />
        <FieldDescription>长度 6–20 个字符，不能包含 &lt; &gt; &quot; ' \ |。</FieldDescription>
        <FieldError :errors="[errors.newPassword]" />
      </Field>
      <Field :data-invalid="!!errors.confirmPassword">
        <FieldLabel for="confirm-password">确认密码</FieldLabel>
        <Input id="confirm-password" v-model="user.confirmPassword" type="password" autocomplete="new-password" placeholder="请再次输入新密码" :aria-invalid="!!errors.confirmPassword" @input="errors.confirmPassword = ''" />
        <FieldError :errors="[errors.confirmPassword]" />
      </Field>
    </FieldGroup>

    <p v-if="error" class="account-password-error" role="alert">{{ error }}</p>
    <p v-if="success" class="account-password-success" role="status">{{ success }}</p>
    <div class="account-password-actions">
      <Button type="submit" :disabled="submitting">{{ submitting ? '保存中…' : '保存密码' }}</Button>
      <Button type="button" variant="outline" :disabled="submitting" @click="close">关闭</Button>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { updateUserPwd } from '@/api/system/user'
import { Button } from '@/components/ui/button'
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'

const emit = defineEmits(['close'])
const user = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const errors = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const error = ref('')
const success = ref('')
const submitting = ref(false)

function validate() {
  errors.oldPassword = ''
  errors.newPassword = ''
  errors.confirmPassword = ''
  if (!user.oldPassword) errors.oldPassword = '旧密码不能为空'
  if (!user.newPassword) errors.newPassword = '新密码不能为空'
  else if (user.newPassword.length < 6 || user.newPassword.length > 20) errors.newPassword = '新密码长度必须为 6–20 个字符'
  else if (/[<>"'|\\]/.test(user.newPassword)) errors.newPassword = '新密码包含不允许的字符'
  if (!user.confirmPassword) errors.confirmPassword = '确认密码不能为空'
  else if (user.confirmPassword !== user.newPassword) errors.confirmPassword = '两次输入的密码不一致'
  return !Object.values(errors).some(Boolean)
}

async function submit() {
  if (submitting.value || !validate()) return
  submitting.value = true
  error.value = ''
  success.value = ''
  try {
    await updateUserPwd(user.oldPassword, user.newPassword)
    success.value = '密码修改成功。'
    user.oldPassword = ''
    user.newPassword = ''
    user.confirmPassword = ''
  } catch (submitError) {
    error.value = submitError.message || '密码修改失败，请重试'
  } finally {
    submitting.value = false
  }
}
function close() { emit('close') }
</script>

<style scoped>
.account-password-form{display:grid;gap:16px}.account-password-actions{display:flex;justify-content:flex-end;gap:8px}.account-password-error,.account-password-success{margin:0;padding:9px 11px;border:1px solid;border-radius:6px;font-size:13px}.account-password-error{border-color:#efc3bd;background:#fff1ef;color:#a32626}.account-password-success{border-color:#b9dec7;background:#effaf3;color:#246b3b}
</style>
