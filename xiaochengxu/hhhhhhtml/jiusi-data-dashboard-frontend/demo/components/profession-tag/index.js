const styles=require('../../utils/profession-styles')
Component({properties:{name:{type:String,value:'',observer:'update'}},data:{inline:'background:#e5e7eb;color:#374151;'},
lifetimes:{attached(){this._alive=true;this.update()},detached(){this._alive=false}},
pageLifetimes:{show(){this.update()}},
methods:{async update(){this.setData({inline:styles.inline(this.properties.name)});await styles.refresh();if(this._alive)this.setData({inline:styles.inline(this.properties.name)})}}})
