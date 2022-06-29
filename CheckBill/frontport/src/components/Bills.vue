<template>

  <div class="deit">
    <div class="crumbs">
      <el-breadcrumb separator="/" style="margin-top: -60px;
    border: initial;
    line-height: 3;
    color: black;
">
    <el-breadcrumb-item style="font-size: larger; font-weight: bold"><i class="el-icon-date"></i> <span style="color: #42b983">数据管理</span></el-breadcrumb-item>
    <el-breadcrumb-item style="font-size: larger;  font-weight: bold"><span style="color: cornflowerblue;">未到对账单账户信息（默认显示T-2）</span></el-breadcrumb-item>
</el-breadcrumb>
<el-row :gutter="20">
<el-col :span="4"><div class="grid-content bg-purple">
   <el-input v-model="product_name" prefix-icon="ei-icon-star-off" placeholder="可输入产品名称筛选"></el-input>
</div></el-col>

  <el-col :span="4" ><div class="grid-content bg-purple">
       <el-select v-model="belongForm.status" multiple placeholder="选择券商名称筛选" @change="styleChange" style="width:300px">
      <el-option v-for="item in option32" :key="item.label" :label="item.label" :value="item.value"/>
    </el-select>
  </div></el-col>

  <el-col :span="4" ><div class="grid-content bg-purple">
    <el-select v-model="typeForm.status" multiple placeholder="选择账户类型筛选" @change="styleChange" style="width:301px;">
     <el-option v-for="item in optionA5" :key="item.value" :label="item.label" :value="item.value"/>
    </el-select>
  </div></el-col>

<el-col :span="4" ><div class="grid-content bg-purple">
 <el-input v-model="department_name" prefix-icon="ei-icon-star-off" placeholder="可输入营业部名称筛选"></el-input>
  </div></el-col>





<el-col :span="3.5"><div class="grid-content bg-purple" style="padding-left: 0px;
    padding-right: 0px;">
    <div class="block">
    <el-date-picker
      v-model="value2"
      type="date"
      placeholder="查询日期"
      :picker-options="pickerOptions">
    </el-date-picker>
  </div>
</div></el-col>

<el-col :span="2">
  <div class="grid-content bg-purple" style="margin-right: 71px;
    margin-left: 62px;" >
    <el-button type="primary" style="
    margin-left: 1px;"  @click.native="search()" >搜索</el-button>

</div></el-col>
   <el-col :span="2"  style="padding-left: 51px;
    padding-right: 10px;"><div class="grid-content bg-purple">
       <el-button type="primary" style="
    margin-left: 1px;"  @click.native="extract()" >一键导出</el-button>
  </div></el-col>


</el-row>

    <div class="cantainer" header-cell-style="color:red">
          <el-table style="width: 100%;"
                    :data="billList.slice((currentPage-1)*pagesize,currentPage*pagesize)" >
                        <el-table-column type="index" width="50">
                        </el-table-column>
                        <el-table-column label="产品名称" prop="product" >
                        </el-table-column>
                        <el-table-column label="券商" prop="belong" >
                        </el-table-column>
                        <el-table-column label="账户类型" prop="type" >
                        </el-table-column>
                        <el-table-column label="账户号" prop="account" >
                        </el-table-column>
                         <el-table-column label="上海卡号" prop="card_sh" >
                        </el-table-column>
                         <el-table-column label="深圳卡号" prop="card_sz" >
                                    </el-table-column>
                         <el-table-column label="启户日期" prop="start_date" >
                                    </el-table-column>
                         <el-table-column label="所属营业部" width="150" prop="business_department" >
                                    </el-table-column>
                         <el-table-column label="联系人" prop="contacts" >
                                    </el-table-column>
                         <el-table-column label="邮箱" prop="contact_email" >
                                    </el-table-column>
                         <el-table-column label="手机" prop="contact_mob" >
                                    </el-table-column>
                         <el-table-column label="电话" prop="contact_tel" >
                                    </el-table-column>
                         <el-table-column label="微信" prop="contact_weixin" >
                                    </el-table-column>
                      </el-table>
                    <el-pagination
                            @size-change="handleSizeChange"
                            @current-change="handleCurrentChange"
                            :current-page="currentPage"
                            :page-sizes="[5, 10, 15, 20]"
                            :page-size="pagesize"
                            layout="total, sizes, prev, pager, next, jumper"
                            :total="billList.length">
                    </el-pagination>
        </div>
    </div>
  </div>


</template>



<script>
 import axios from 'axios';

 import Qs from 'qs';

    export default {
      name: "Bills",
    data() {
     return {
          currentPage:1, //初始页
          pagesize:10,    //    每页的数据
          billList: [],
          value2: '',
          token: '',
          product_name:'',
          department_name:'',
          optionA5: [],
       typeForm: {
          status: [],
        },

       belongForm:{
            status: [],
       },
       option32:[],

          pickerOptions: {
          // disabledDate(time) {
          //   return time.getTime() > Date.now();
          // },
            shortcuts: [{
            text: 'Today',
            onClick(picker) {
              picker.$emit('pick', new Date());
            }
          }, {
            text: 'Yesterday',
            onClick(picker) {
              const date = new Date();
              date.setTime(date.getTime() - 3600 * 1000 * 24);
              picker.$emit('pick', date);
            }
          }, {
            text: 'A week ago',
            onClick(picker) {
              const date = new Date();
              date.setTime(date.getTime() - 3600 * 1000 * 24 * 7);
              picker.$emit('pick', date);
            }
          }]
        },

      }

  },

    created() {
        this.handleAccountList();
        this.handleComboBox();
    },
    methods: {
        checkDict(list, key) {
　　　　　　　　// list--字典列表   key --字典值
　　　　　　　　var obj = list.find(item => {return item.value == key})
                if (!obj) {
                    return key
                } else {
                    return obj.label
                }
            },

        // 初始页currentPage、初始每页数据数pagesize和数据data
        handleSizeChange: function (size) {
                this.pagesize = size;
                axios.get("http://192.168.1.31:8000/save_pagesize?pagesize="+this.pagesize+"&token="+this.token).then(res=>{
                  if(res.data.code=='200'){
                    //alert(res.data.message);
                  }

                })
                console.log(this.pagesize)  //每页下拉显示数据
        },
        handleCurrentChange: function(currentPage){
                this.currentPage = currentPage;
                console.log(this.currentPage)  //点击第几页
        },
        handleAccountList() {
           const _this = this;
           //_this.token = _this.$route.params.token;
          _this.token = JSON.parse(this.$route.query.token);
            axios.get("http://192.168.1.31:8000/get_bills?account_type="+""+"&end_time="+""+"&product_name="+""+"&belong_name="+""+"&department_name="+""+"&token="+_this.token).then(res => {
              //这是从本地请求的数据接口
                if(res.data.status_code === '200'){

                  this.value2 = res.data.t2_day;
                  this.billList = res.data.bill_list;
                  this.pagesize = res.data.page_size;

                }else {
                  _this.$router.push("/");
                  alert("请先登录")
                }
            }).catch(err =>{
              console.log(err)
            })
        },
       handleComboBox(){
            axios.get("http://192.168.1.31:8000/get_boxs").then(res=>{
                //从券商下拉列表回的数据
                this.option32 = res.data.belong;
                this.optionA5 = res.data.type_list;
            }).catch(err =>{
              console.log(err)
            })
       },
        search(){
          let end_time = this.handleTime(this.value2,"yyyy-MM-dd");
          let account_type = this.typeForm.status;
          let belong_name = this.belongForm.status;
          let str_account_type = '';
          for(let i = 0; i < account_type.length; i ++){
            if(i !== account_type.length - 1){
            str_account_type = str_account_type +account_type[i]+"_";
            } else{
              str_account_type = str_account_type +account_type[i];
            }

          }
          let str_belong_name = '';
          for(let j = 0; j < belong_name.length; j ++){
            if(j !== belong_name.length - 1){
              str_belong_name = str_belong_name + belong_name[j] + "_";
            }else {
              str_belong_name = str_belong_name + belong_name[j];
            }
          }

          console.log(str_account_type);
          console.log(str_belong_name)
          let product_name = this.product_name;
          let department_name = this.department_name;

          axios.get("http://192.168.1.31:8000/get_bills?account_type="+str_account_type+"&end_time="+end_time+"&product_name="+product_name+"&belong_name="+str_belong_name+"&department_name="+department_name+"&token="+this.token).then(res => {
            this.billList = res.data.bill_list
          })
          return true;
      },
     extract(){
          let print_list = this.billList
          let choice_time = this.handleTime(this.value2,"yyyy-MM-dd");

            axios.post("http://192.168.1.31:8000/get_print_bills?choice_time="+choice_time,print_list).then(res=>{
            let m_url = res.data.url;
            window.location.href=m_url;
          }).catch(error=>{

          })
      },
     styleChange(val) {
          console.log(this.belongForm.status);
    if(val == 0){
      console.log(this.typeForm.status)

    }else if(val == 1){
      console.log(this.typeForm.status)
    }

},


      handleTime(time, format) {
    if (time == null || time == undefined || time == "") {
        return "";
    }
    var t = new Date(time);
    var tf = function (i) {
        return (i < 10 ? '0' : '') + i
    };
    return format.replace(/yyyy|MM|dd|HH|mm|ss/g, function (a) {
        switch (a) {
            case 'yyyy':
                return tf(t.getFullYear());
                break;
            case 'MM':
                return tf(t.getMonth() + 1);
                break;
            case 'mm':
                return tf(t.getMinutes());
                break;
            case 'dd':
                return tf(t.getDate());
                break;
            case 'HH':
                return tf(t.getHours());
                break;
            case 'ss':
                return tf(t.getSeconds());
                break;
        }
    })
}


      },

};
</script>

<style scoped>
.el-row {
    margin-bottom: 20px;
    &:last-child {
      margin-bottom: 0;
    }
  }
  .el-col {
    border-radius: 4px;
  }
  .bg-purple-dark {
    background: #99a9bf;
  }
  .bg-purple {
    background: #d3dce6;
  }
  .bg-purple-light {
    background: coral;
  }
  .grid-content {
    border-radius: 4px;
    min-height: 36px;
  }
  .row-bg {
    padding: 10px 0;
    background-color: #f9fafc;
  }
</style>
