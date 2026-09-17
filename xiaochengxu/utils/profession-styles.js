const {createStyleCache}=require('./profession-styles-core')
const identity=()=>typeof wx==='undefined'?'':require('./storage').getToken()
const cache=createStyleCache({getIdentity:identity,load:()=>require('../services/activities').getClient().professionStyles()})
const style=p=>cache.style(p)
const inline=p=>{const s=style(p);return 'background:'+s.backgroundColor+';color:'+s.color+';'}
module.exports={style,inline,refresh:cache.refresh,clear:cache.clear}
