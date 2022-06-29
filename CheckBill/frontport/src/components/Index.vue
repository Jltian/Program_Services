<template>
  <div id="index">
<h1>欢迎登录首界面</h1>
  <p>{{msg}}
  </p>
    <hr>
    <block v-if="status">
      正确的话，你能看到我
    </block>
    <hr>
    <ol>
      <li v-for="(item,index) in list" :key="index">
        {{item.text}}
      </li>
    </ol>
  </div>
</template>

<script>
    export default {
        name: "index",
        data(){
          return{
            msg:"Hello world",
            status:true,
            list:[
              {text:'学习javascript'},
              {text:'学习vue'},
              {text:'学习项目'}
            ]


          }
        },
        mounted() {
          alert("wolegequ");
        },
        methods(){

        }
    }
</script>

<style scoped>

</style>
