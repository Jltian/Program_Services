<template>


  <div style="text-align: center">


    <div class="img1">
      <img src="../assets/logo.png" style="margin-top: -46px">
    </div>


    <el-form :model="ruleForm" status-icon :rules="rules" ref="ruleForm" label-width="100px" class="demo-ruleForm" style="width: 30%;display: inline-block;margin-left: -97px">


      <el-form-item label="" prop="username">
        <el-input v-model="ruleForm.username" placeholder="请输入用户名"></el-input>
      </el-form-item>

      <el-form-item label="" prop="password">
        <el-input type="password" v-model="ruleForm.password" autocomplete="off" placeholder="请输入密码" @keyup.enter.native="submitForm('ruleForm')"></el-input>
      </el-form-item>


      <el-form-item>
        <el-button type="primary" @click="submitForm('ruleForm')">登录</el-button>
        <el-button @click="resetForm('ruleForm')">重置</el-button>
      </el-form-item>
    </el-form>

  </div>

</template>
<style>
  .img1{


  }
  .demo-ruleForm{

  }
</style>
<script>
  import axios from 'axios';
  import Qs from 'qs';
  export default {
    data() {
      return {
        ruleForm: {
          username: '',
          password: '',
        },
        rules: {
          username:[
            // 当组件离开焦点的时候进行验证
            {required:true, message:'请输入用户名',trigger:'blur'}
          ],
          password:[
            {required:true, message:'请输入密码',trigger:'blur'}
          ]
        }
      };
    },
    methods: {
      submitForm(formName) {
        this.$refs[formName].validate((valid) =>{
          if (valid){
            const _this = this
            var data = Qs.stringify({"username":this.ruleForm.username,"password":this.ruleForm.password})
            console.log("data:",data)
            axios.post("http://192.168.1.31:8000",data).then(
              function (resp) {
                //alert(resp.status);
                console.log("resp:");
                console.log(resp);
               // _this.$router.push("/DataManageCenter")
                const flag = resp.data.request['flag']
                const token = resp.data.request['token']
                console.log(resp.data.request)
                const login_name =JSON.parse(resp.data.user_obj)['loginname']
                const user_id = JSON.parse(resp.data.user_obj)['user_id']

                if (flag == 'yes'){
                  _this.$router.push({name:"DataManageCenter",params:{login_name:login_name,user_id:user_id,token:token}})
                }else {
                  alert("请输入正确的用户名和密码")
                }
              },function (error) {
                  console.log(error)
              }

            )
            // 开始用的 axios 发送请求
            // console.log(this.ruleForm)
          }else {
            alert("验证未通过")
          }
        })
      },
      resetForm(formName) {
        this.$refs[formName].resetFields();
      }
    }
  }
</script>

