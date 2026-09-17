<template><span class="profession-tag" :style="getGuildClassStyle(name)" :title="name || '不限职业'">{{name || '不限职业'}}</span></template>
<script setup>
import {onMounted} from 'vue'
import {getGuildClassStyle,loadGuildClassColors} from '@/utils/guildClassColor'
defineProps({name:{type:String,default:''}})
onMounted(()=>loadGuildClassColors())
</script>
<style scoped>
.profession-tag{display:inline-flex!important;align-items:center;font-size:12px!important;line-height:16px!important;font-weight:500!important;padding:1px 5px!important;margin:0!important;border:1px solid transparent;border-radius:3px;max-width:100%;vertical-align:middle;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;box-sizing:border-box}
</style>
<style>
/* Element Plus labels have z-index -1; isolate them from opaque wrappers without animation. */
.el-select__wrapper:has(.profession-tag){isolation:isolate}
</style>
