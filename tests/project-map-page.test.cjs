const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')

class Element {
  constructor() { this.children=[]; this.style={}; this.className=''; this.innerHTML=''; this.textContent=''; this.value='' }
  appendChild(child) { this.children.push(child); return child }
  addEventListener() {}
  select() {}
  remove() {}
}

test('项目说明页能生成可点击目录树和详情', () => {
  const html=fs.readFileSync('E:/nsh/nshls/html/index.html','utf8')
  const script=html.match(/<script>([\s\S]*)<\/script>/)[1]
  const elements=new Map(['#tree','#detail','#search','#expandBtn','#collapseBtn','#copyPath'].map(key=>[key,new Element()]))
  const document={
    querySelector(selector){return elements.get(selector)||null},
    createElement(){return new Element()},
    body:new Element(),
    execCommand(){return true}
  }
  vm.runInNewContext(script,{document,navigator:{},location:{protocol:'file:'},setTimeout(){}})
  assert.ok(elements.get('#tree').children.length>=3,'目录树必须包含三个顶层项目')
  assert.match(elements.get('#detail').innerHTML,/当前网页与后端的独立开发副本/)
  const descendants=[]
  const visit=(element)=>{descendants.push(element);element.children.forEach(visit)}
  visit(elements.get('#tree'))
  const deploy=descendants.find(element=>element.title==='E:\\nsh\\nshls\\RuoYi-Vue3-FastAPI-miniapp-backend\\deploy')
  assert.ok(deploy,'deploy 目录必须存在')
  assert.match(deploy.innerHTML,/▸|▾/,'有子文件的 deploy 必须可以展开')
  const virtualEnv=descendants.find(element=>element.title==='E:\\nsh\\nshls\\RuoYi-Vue3-FastAPI-miniapp-backend\\ruoyi-fastapi-backend\\.venv')
  assert.ok(virtualEnv,'虚拟环境目录必须存在')
  assert.doesNotMatch(virtualEnv.innerHTML,/▸|▾/,'未列出子项的目录不得显示假展开箭头')
})
