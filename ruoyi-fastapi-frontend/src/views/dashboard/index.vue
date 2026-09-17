<template>
  <div class="app-container home-page">
    <section class="home-heading">
      <div>
        <Badge variant="outline">联赛与约战</Badge>
        <h1>{{ displayName }}，欢迎回来</h1>
        <p>首页只保留新版功能入口。创建约战、排表、请假、公开报名与历史数据均使用统一后端。</p>
      </div>
      <Button variant="outline" @click="go('/personal/profile-edit')">个人中心</Button>
    </section>

    <div class="home-sections">
      <Card>
        <CardHeader>
          <CardTitle>帮会管理</CardTitle>
          <CardDescription>管理员与助手使用。约战只能在“约战排表”中创建。</CardDescription>
        </CardHeader>
        <CardContent class="home-actions">
          <Button variant="outline" @click="go('/guild/info')">帮会信息</Button>
          <Button variant="outline" @click="go('/guild/member')">成员管理</Button>
          <Button @click="go('/guild/schedule')">约战排表</Button>
          <Button variant="outline" @click="go('/guild/analysis')">数据分析</Button>
          <Button variant="outline" @click="go('/guild/classColor')">职业颜色设置</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>个人管理</CardTitle>
          <CardDescription>只查看本人参加的帮会及俱乐部活动，并管理自己的资料。</CardDescription>
        </CardHeader>
        <CardContent class="home-actions">
          <Button @click="go('/personal/battle-information/mine')">我的约战</Button>
          <Button variant="outline" @click="go('/personal/battle-information/public')">找约战</Button>
          <Button variant="outline" @click="go('/personal/battle-information/history')">历史约战</Button>
          <Button variant="outline" @click="go('/personal/profile-edit')">个人中心</Button>
          <Button variant="outline" @click="go('/personal/skill')">内功管理</Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import useUserStore from '@/store/modules/user'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const router=useRouter(),user=useUserStore()
const displayName=computed(()=>user.nickName||user.name||'你好')
function go(path){router.push(path)}
</script>

<style scoped>
.home-page{display:grid;gap:18px;color:#172033}.home-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding:4px}.home-heading h1{margin:12px 0 6px;font-size:26px}.home-heading p{max-width:720px;margin:0;color:#667085;line-height:1.7}.home-sections{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.home-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.home-actions>*{width:100%}@media(max-width:800px){.home-heading{display:grid}.home-sections{grid-template-columns:1fr}.home-actions{grid-template-columns:1fr}}
</style>
