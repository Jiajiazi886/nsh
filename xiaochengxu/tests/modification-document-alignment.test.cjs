const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const root = path.resolve(__dirname, '..')
const variants = [
  {
    name: '主小程序',
    list: path.join(root, 'pages/activities/index.wxml'),
    ui: path.join(root, 'utils/activity-ui.js'),
  },
  {
    name: '联赛分析小程序',
    list: path.join(root, 'hhhhhhtml/jiusi-data-dashboard-frontend/demo/pages/activities/activities.wxml'),
    ui: path.join(root, 'hhhhhhtml/jiusi-data-dashboard-frontend/demo/utils/activity-ui.js'),
  },
]

for (const variant of variants) {
  test(`${variant.name}按修改文档显示历史约战且不混入独立战报列表`, () => {
    const list = fs.readFileSync(variant.list, 'utf8')
    const ui = fs.readFileSync(variant.ui, 'utf8')

    assert.match(list, /历史约战/)
    assert.doesNotMatch(list, /历史战报|战报记录|已有战报|暂无战报数据/)
    assert.doesNotMatch(list, /<text>缺 \{\{tag\.count\}\}/)
    assert.match(list, /<profession-tag name="\{\{tag\.profession\}\}"\/><text>\{\{tag\.count\}\}<\/text>/)
    assert.doesNotMatch(ui, /activityReports\(/)
    assert.doesNotMatch(ui, /reportError|reports:/)
    assert.match(ui, /participatingOnly:this\.data\.kind==='mine'/)
    assert.match(ui, /只显示本人已经参加的帮会和俱乐部约战/)
  })
}
