/* Shared pure resolver and per-session cache. Never persists private profile data. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.NshProfessionStyles=api})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const defaults=[{"class_name":"九灵","bg_color":"#ff0000","text_color":"#ffffff"},{"class_name":"沧澜","bg_color":"#002fff","text_color":"#000000"},{"class_name":"潮光","bg_color":"#0073ff","text_color":"#000000"},{"class_name":"玄机","bg_color":"#ddff00","text_color":"#000000"},{"class_name":"碎梦","bg_color":"#00ffe5","text_color":"#000000"},{"class_name":"神相","bg_color":"#002fff","text_color":"#000000"},{"class_name":"素问","bg_color":"#ea00ff","text_color":"#000000"},{"class_name":"血河","bg_color":"#ff0000","text_color":"#000000"},{"class_name":"铁衣","bg_color":"#ff8c00","text_color":"#000000"},{"class_name":"鸿音","bg_color":"#ff7b00","text_color":"#000000"},{"class_name":"龙吟","bg_color":"#00f846","text_color":"#000000"},{"class_name":"刺客","bg_color":"#FFFFFF","text_color":"#000000"}];
const neutral={backgroundColor:'#e5e7eb',color:'#374151'};
function normalize(rows){
 const map={};
 for(const r of rows||[]){const name=r.profession||r.class_name||r.className,bg=r.backgroundColor||r.bg_color||r.bgColor,fg=r.textColor||r.text_color;
  if(name&&/^#[0-9a-f]{6}$/i.test(bg||'')&&/^#[0-9a-f]{6}$/i.test(fg||''))map[name]={backgroundColor:bg,color:fg};
 }
 return map;
}
function createStyleCache({getIdentity,load}){
 const fallback=normalize(defaults);let identity=null,map={...fallback},pending=null,revision=0;
 function ensure(){const next=getIdentity()||'';if(next!==identity){identity=next;map={...fallback};pending=null;revision++}return identity}
 function style(name){ensure();return map[name]||neutral}
 function set(rows){ensure();map={...fallback,...normalize(rows)};revision++;return map}
 async function refresh(){const key=ensure();if(!key)return map;if(pending)return pending;const version=revision;
  const task=Promise.resolve().then(load).then(rows=>{if(ensure()===key&&revision===version){map={...fallback,...normalize(rows)}}return map}).catch(()=>map).finally(()=>{if(pending===task)pending=null});pending=task;return task;
 }
 function clear(){identity=null;map={...fallback};pending=null;revision++}
 return {style,set,refresh,clear};
}
return {defaults,normalize,neutral,createStyleCache};
});
