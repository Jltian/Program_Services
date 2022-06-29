<template>
  <div>

 <h1> 产品券商账户信息表</h1>
     <el-col :span="2" style="float : right;margin-right: 85px;">
      <el-button
        type="success"
        @click="extract_file"
        icon="el-icon-share"
        size="mini"
        style="margin-left: -45px;"
      >一键导出</el-button>
    </el-col>
    <el-table
      :data="table_data"
      style="width: 100%"
      :header-cell-style="{textAlign:'center'}"
    :cell-style="{textAlign: 'center'}"
      height="520"
      :index="indexMethod"
    >
       <el-table-column label="序 号" type="index"
          width="100" >
      </el-table-column>
      <el-table-column label="产品名称" width="240">
        <template slot-scope="scope">
          <span> {{ scope.row.product}}</span>
        </template>
      </el-table-column>
      <el-table-column label="证券机构" width="240">
        <template slot-scope="scope">
           <span> {{ scope.row.belong }}</span>
        </template>
      </el-table-column>
      <el-table-column label="账户类型" width="240">
        <template slot-scope="scope">
           <span> {{ scope.row.type }}</span>
        </template>
      </el-table-column>
      <el-table-column label="营业部" width="240">
        <template slot-scope="scope">
           <span> {{ scope.row.business_department }}</span>
        </template>
      </el-table-column>
      <el-table-column label="账户号" width="240">
        <template slot-scope="scope">
           <span> {{ scope.row.account }}</span>
        </template>
      </el-table-column>


      <el-table-column label="账户状态" width="240">
        <template slot-scope="scope">
            <span> {{options[scope.row.status]['label']}} </span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="240" >
        <template slot="header" slot-scope="scope">

          <el-input v-model="search"  placeholder="输入关键字搜索" />


        </template>
        <template slot-scope="scope">
          <el-button size="mini" type="primary" @click="handleEdit(scope.$index, tableData)">编辑</el-button>
          <el-button
            size="mini"
            type="info"
            @click.native.prevent="detailmessage(scope.$index, tableData)"
          style="margin-left: 86px" disabled>配置</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
                          @size-change="handleSizeChange"
                          @current-change="handleCurrentChange"
                          :current-page="currentPage"
                           :page-sizes="[5, 10, 15, 20]"
                          :page-size="pagesize"
                           layout="total, sizes, prev, pager, next, jumper"
                          :total=parseInt(tableDate_length)>
    </el-pagination>


    <el-col :span="1">
      <el-button
        type="success"
        @click="addCreate"
        @keydown.enter="adddata"
        icon="el-icon-circle-plus-outline"
        size="mini"
      >新增账户</el-button>
    </el-col>

<el-dialog title="添加产品券商账户信息" :visible.sync="dialogFormVisibles">

  <el-form :model="ruleForm"  :rules="rules"  ref="ruleForm"   label-width="80px" class="demo-ruleForm">
    <el-form-item label="产品名称" prop="product">
      <el-input v-model="ruleForm.product" placeholder="请输入基金产品名称"></el-input>
    </el-form-item>
    <el-form-item label="证券机构" prop="belong">
      <el-input v-model="ruleForm.belong" placeholder="请输入券商机构名称"></el-input>
    </el-form-item>

    <el-form-item label="账户类型" prop="type">
      <el-col :span="6">
      <el-select v-model="ruleForm.type" placeholder="请选择证券账户类型">
          <el-option label="普通账户" value="普通账户"></el-option>
          <el-option label="期权账户" value="期权账户"></el-option>
          <el-option label="期货账户" value="期货账户"></el-option>
          <el-option label="信用账户" value="信用账户"></el-option>
          <el-option label="收益互换" value="收益互换"></el-option>
          <el-option label="场外期权" value="场外期权"></el-option>
      </el-select>
         </el-col>
    </el-form-item>

    <el-form-item label="资金账号">
      <el-input v-model="ruleForm.account" placeholder="请输入账户资金账号" @blur="account_blur"></el-input>
    </el-form-item>

      <el-form-item label="上海卡号" >
      <el-input v-model="ruleForm.card_sh" placeholder="请输入上海卡号"></el-input>
      </el-form-item>
      <el-form-item label="深圳卡号">
      <el-input v-model="ruleForm.card_sz" placeholder="请输入深圳卡号"></el-input>
      </el-form-item>
      <el-form-item label="启用日期" prop="start_date">
      <el-col :span="11">
      <el-date-picker type="date" placeholder="选择日期" v-model="ruleForm.start_date" style="width: 100%;"></el-date-picker>
      </el-col>

      </el-form-item>
        <el-form-item label="营业部" prop="business_department">
        <el-input v-model="ruleForm.business_department" placeholder="请输入营业部全称"></el-input>
      </el-form-item>
      <el-form-item label="联系人" prop="contacts">
        <el-input v-model="ruleForm.contacts" placeholder="请输入联系人姓名" @blur="contact_blur"></el-input>
      </el-form-item>
      <el-form-item label="邮 箱" prop="contact_email">
        <el-input v-model="ruleForm.contact_email" placeholder="请输入联系人邮箱号"></el-input>
      </el-form-item>

      <el-form-item label="手 机" prop="contact_mob">
          <el-input v-model="ruleForm.contact_mob" placeholder="请输入联系人手机号"></el-input>
      </el-form-item>

      <el-form-item label="电 话" >
          <el-input v-model="ruleForm.contact_tel" placeholder="请输入联系人电话"></el-input>
      </el-form-item>

      <el-form-item label="微 信" >
          <el-input v-model="ruleForm.contact_weixin" placeholder="请输入联系人微信"></el-input>
      </el-form-item>

      <el-form-item label="交易员">
          <el-input v-model="ruleForm.trader" placeholder="请输入认领交易员姓名"></el-input>
      </el-form-item>

      <el-form-item label="销售员">
          <el-input v-model="ruleForm.salesman" placeholder="请输入认领销售员姓名"></el-input>
      </el-form-item>

      <el-form-item label="后台员">
          <el-input v-model="ruleForm.backstage_staff" placeholder="请输入认领后台员姓名"></el-input>
      </el-form-item>

      <el-form-item label="备注" >
          <el-input type="textarea" v-model="ruleForm.notes"></el-input>
      </el-form-item>

    </el-form>

    <div slot="footer" class="dialog-footer">
      <el-button @click="dialogFormVisibles = false">取 消</el-button>
      <el-button @click="resetForm('ruleForm')">重置</el-button>
      <el-button type="primary" @click="addCreates('ruleForm')">确 定</el-button>
    </div>

</el-dialog>


    <!-- 模态框 -->
<el-dialog title="编辑产品券商账户信息" :visible.sync="dialogFormVisible">


  <el-form :model="editForm"  :rules="rules"  ref="editForm"   label-width="80px" class="demo-editForm">
    <el-form-item label="产品名称" prop="product">
      <el-input v-model="editForm.product" placeholder="请输入基金产品名称"></el-input>
    </el-form-item>
    <el-form-item label="证券机构" prop="belong">
      <el-input v-model="editForm.belong" placeholder="请输入券商机构名称"></el-input>
    </el-form-item>

    <el-form-item label="账户类型" prop="type">
      <el-col :span="6">
      <el-select v-model="editForm.type" placeholder="请选择证券账户类型">
          <el-option label="普通账户" value="普通账户"></el-option>
          <el-option label="期权账户" value="期权账户"></el-option>
          <el-option label="期货账户" value="期货账户"></el-option>
          <el-option label="信用账户" value="信用账户"></el-option>
          <el-option label="收益互换" value="收益互换"></el-option>
          <el-option label="场外期权" value="场外期权"></el-option>
      </el-select>
         </el-col>
    </el-form-item>

    <el-form-item label="资金账号">
      <el-input v-model="editForm.account" placeholder="请输入账户资金账号"></el-input>
    </el-form-item>

      <el-form-item label="上海卡号" >
      <el-input v-model="editForm.card_sh" placeholder="请输入上海卡号"></el-input>
      </el-form-item>
      <el-form-item label="深圳卡号">
      <el-input v-model="editForm.card_sz" placeholder="请输入深圳卡号"></el-input>
      </el-form-item>
      <el-form-item label="开户日期" >
      <el-col :span="11">
      <el-date-picker type="date" placeholder="选择日期" v-model="editForm.start_date" style="width: 100%;"></el-date-picker>
      </el-col>

      </el-form-item>

       <el-form-item label="销户日期" >
      <el-col :span="11">
      <el-date-picker type="date" placeholder="选择日期" v-model="editForm.end_date" style="width: 100%;"></el-date-picker>
      </el-col>

      </el-form-item>
        <el-form-item label="营业部" prop="business_department">
        <el-input v-model="editForm.business_department" placeholder="请输入营业部全称"></el-input>
      </el-form-item>
      <el-form-item label="联系人" prop="contacts">
        <el-input v-model="editForm.contacts" placeholder="请输入联系人姓名"></el-input>
      </el-form-item>
      <el-form-item label="邮 箱" prop="contact_email">
        <el-input v-model="editForm.contact_email" placeholder="请输入联系人邮箱号"></el-input>
      </el-form-item>

      <el-form-item label="手 机" prop="contact_mob">
          <el-input v-model="editForm.contact_mob" placeholder="请输入联系人手机号"></el-input>
      </el-form-item>

      <el-form-item label="电 话" >
          <el-input v-model="editForm.contact_tel" placeholder="请输入联系人电话"></el-input>
      </el-form-item>

      <el-form-item label="微 信" >
          <el-input v-model="editForm.contact_weixin" placeholder="请输入联系人微信"></el-input>
      </el-form-item>
      <el-form-item label="状 态">
         <el-col :span="6">
      <el-select v-model="editForm.status" >
        <el-option v-for="(item,index) in this.options" :value="item.value"  :label="item.label"  :key="index">{{item.label}}</el-option>
      </el-select>
       </el-col>
      </el-form-item>
      <el-form-item label="交易员">
          <el-input v-model="editForm.trader" placeholder="请输入认领交易员姓名"></el-input>
      </el-form-item>

      <el-form-item label="销售员">
          <el-input v-model="editForm.salesman" placeholder="请输入认领销售员姓名"></el-input>
      </el-form-item>

      <el-form-item label="后台员">
          <el-input v-model="editForm.backstage_staff" placeholder="请输入认领后台员姓名"></el-input>
      </el-form-item>

      <el-form-item label="备注" >
          <el-input type="textarea" v-model="editForm.notes"></el-input>
      </el-form-item>

    </el-form>


      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button type="primary" @click="update('editForm')">确 定</el-button>
      </div>



    </el-dialog>
  </div>

</template>

<script>

import axios from "axios";
import * as XLSX from 'xlsx';
export default {
  name: "AccountInformation",

  data() {
    return {
      currentPage:1, //初始页
      pagesize:10,
      tableData: [],//   数据总量
      tableDate_length:"",
      username: "",
      useraddress: "",
      dialogFormVisible: false,
      dialogFormVisibles: false,
      formLabelWidth:'',
      tableData_back : [],
      tableDate_length_back : '',
      form: {
        product: "",
        belong: "",
        type: "",
        account:"",
        card_sh:"",
        card_sz:"",
        start_date:"",
        end_date:"",
        business_department:"",
        contacts:"",
        contact_email:"",
        contact_mob:"",
        contact_tel:"",
        contact_weixin:"",
        status:"",
        trader:"",
        salesman:"",
        backstage_staff:"",
        notes:"",
      },
      ruleForm: {
        product: "",
        belong: "",
        type: "",
        account:"",
        card_sh:"",
        card_sz:"",
        start_date:"",
        business_department:"",
        contacts:"",
        contact_email:"",
        contact_mob:"",
        contact_tel:"",
        contact_weixin:"",
        status:"",
        trader:"",
        salesman:"",
        backstage_staff:"",
        notes:"",
      },
      editForm: {
        id :"",
        product: "",
        belong: "",
        type: "",
        account:"",
        card_sh:"",
        card_sz:"",
        start_date:"",
        end_date: "",
        business_department:"",
        contacts:"",
        contact_email:"",
        contact_mob:"",
        contact_tel:"",
        contact_weixin:"",
        status:"",
        trader:"",
        salesman:"",
        backstage_staff:"",
        notes:"",
      },

      rules: {
          product: [
            { required: true, message: '请输入产品名称', trigger: 'blur' },
            { min: 3, max: 15, message: '长度在 3 到 15 个字符之间', trigger: 'blur' }
          ],
          belong: [
            { required: true, message: '请输入券商名称', trigger: 'blur' }
          ],
          type: [
            { required: true, message: '请选择账户类型', trigger: ['change','blur'] }
          ],
          start_date:[
            { required: true, message: '请选择日期', trigger: ['change','blur']}
          ],
          business_department:[
            { required: false, message: '请填写营业部全称(如不知全称，请填写未知二字)', trigger: 'blur'},
            {min:2,max:20,message: '长度在 2 到 20 个字符之间',trigger: 'blur'}
          ],
          contacts:[
            { required: false}
          ],
          contact_email:[
            { required: false, message: '请填写符合邮箱格式的字符串', trigger: 'blur'},
            { type: 'email', message: '请输入正确的邮箱号', trigger: ['change','blur']}
          ],
          contact_mob: [
            { required: false,message: '请输入符合手机号码规范的字符串', trigger: 'blur'},
            {min: 11,max:11, message: '请输入正确的手机号格式',trigger: ['change','blur']}
          ]
        },
      options:[
        {
          value : "0",
          label : "销户"
        },{
          value : "1",
          label: "正常"
        },{
          value : "2",
          label: "休眠/冻结"
        },{
          value: "3",
          label: "准备销户"
        }
      ],
      search: "",

    };
  },


  created(){
      this.initTable();
    },
  // mounted() {
  //   const s = document.createElement('script');
  //   s.type = '../../dist/xlsx.core.min.js';
  //   s.src = 'text/javascript';
  //   document.body.appendChild(s);
  // },
  computed:{
    table_data() {
      let search = this.search;
      // 搜索功能且分页
      if (search){
        //{{options[scope.row.status]['label']}}

        let list =this.tableData.filter(data => !search || data.account.toLowerCase().includes(search.toLowerCase()) || data.belong.toLowerCase().includes(search.toLowerCase()) || data.type.toLowerCase().includes(search.toLowerCase()) || data.product.toLowerCase().includes(search.toLowerCase()) || data.business_department.toLowerCase().includes(search.toLowerCase()) || this.options[data.status]['label'].toLowerCase().includes(search.toLowerCase()));

        let fenye = list.slice((this.currentPage-1)*this.pagesize,this.currentPage*this.pagesize);
        // 获取查询的结果，把数组长度赋值给 分页组件中的total
        this.tableDate_length = list.length;
        this.tableData = list;

        return list,fenye
      }
      // 分页功能
     else {
       //所有数据的长度  赋值给分页组件中的total
        console.log('no condition_this.tabledata:');
        console.log(this.tableData);
        this.tableData = this.tableData_back;
        this.tableDate_length = this.tableDate_length_back
        let total = this.tableData;
        let fenye = total.slice((this.currentPage-1)*this.pagesize,this.currentPage*this.pagesize);

        //this.tableDate_length = total.length;
        return total,fenye
      }
  },
    computedSiteType(){
      return function (status){
        return this.options[status]['label']
      }
    },
  },

  methods: {
        // 初始页currentPage、初始每页数据数pagesize和数据data
        handleSizeChange: function (size) {
                this.pagesize = size;
                // axios.get("http://127.0.0.1:8000/save_pagesize?pagesize="+this.pagesize+"&token="+this.token).then(res=>{
                //   if(res.data.code=='200'){
                //     //alert(res.data.message);
                //   }
                //
                // })

        },
        handleCurrentChange: function(currentPage){
                this.currentPage = currentPage;
          //点击第几页
        },

    formatDateTime(inputTime) {
      var date = new Date(inputTime);
      var y = date.getFullYear();
      var m = date.getMonth() + 1;
      m = m < 10 ? "0" + m : m;
      var d = date.getDate();
      d = d < 10 ? "0" + d : d;
      var h = date.getHours();
      h = h < 10 ? "0" + h : h;
      var minute = date.getMinutes();
      var second = date.getSeconds();
      minute = minute < 10 ? "0" + minute : minute;
      second = second < 10 ? "0" + second : second;
      return y + "-" + m + "-" + d;
    },

    handleEdit(index, row) {
      let page = this.currentPage;
      index = index + this.indexMethod(page);
      for(let k in row[index]){
        for(let j in this.editForm){
          if (j === 'status'){
            this.editForm[j] = this.options[row[index][j]]['label']
          }else {
            this.editForm[j] = row[index][j];
          }

        }
      }
      this.dialogFormVisible = true;
    },
    addCreate(index) {
      this.dialogFormVisibles = true;
      this.form.index = index;
    },
    account_blur(){
          let product = this.ruleForm.product;
          let belong = this.ruleForm.belong;
          let type = this.ruleForm.type;
          let account = this.ruleForm.account;
          const params = new URLSearchParams();
          params.append('product',product);
          params.append('belong',belong);
          params.append('type',type);
          params.append('account',account);
          axios.post('http://192.168.1.31:8000/get_duplicated_account',params).then(
            res => {
              if(res.data.account_result !== null){
                this.$refs['ruleForm'].resetFields();
                this.$message.error('该产品券商账户已存在，请核对后再录入');
              }
            }
          )
    },
    contact_blur(){
          let business = this.ruleForm.business_department;
          let contact = this.ruleForm.contacts;
          const params = new URLSearchParams();
          params.append('business',business);
          params.append('contact',contact);
          axios.post('http://192.168.1.31:8000/get_others_info',params).then(
            res => {
              console.log(res.data.message);
              console.log(res.data.contact_result);
              if(res.data.contact_result !== null){
                this.ruleForm.contact_email = res.data.contact_result.contact_email;
                this.ruleForm.contact_mob = res.data.contact_result.contact_mob;
                this.ruleForm.contact_tel = res.data.contact_result.contact_tel;
                this.ruleForm.contact_weixin = res.data.contact_result.contact_weixin;
              }

            }
          )
    },

    indexMethod(index) {
        return (index-1)*this.pagesize;
      },

    update(formName) {

      this.$refs[formName].validate((valid) => {
        if(valid){
          axios.post('http://192.168.1.31:8000/update_account',this.editForm).then(res => {
            this.$message.success("数据修改成功")
            this.dialogFormVisible = false;
            this.initTable();
          }).catch(
            error => {
              console.log('修改异常'+ error);
            }
          )
          this.dialogFormVisible = false;
        }else {
          this.$message.error('表单数据未填写完整，修改失败');
          return false;
        }
        }
      );

    },
    detailmessage(index, tableData) {
        let page = this.currentPage;
        index = index + this.indexMethod(page);
        console.log(tableData);
        console.log(index);
        this.$router.push({name:'AccountDetail',params:{'id':tableData[index].id}});
      //row.splice(index, 1);
    },


    addCreates(formName) {
          //准备把新增数据发往后台
      this.$refs[formName].validate((valid) => {
        if(valid){
          axios.post('http://192.168.1.31:8000/add_account',this.ruleForm).then(res => {
            this.$message.success("数据新增成功");
            this.initTable();
            this.dialogFormVisibles = false;
          }).catch(
            error => {
              console.log('新增异常'+ error);
            }
          )

        }else {
          this.$message.error('表单数据未填写完整，新增失败');
          return false;
        }
        }
      );
    },
    extract_file(){
      let table_data_list =  this.tableData;
      let array_store_row = [];
      let head_row = [];
      let col_row = [];
      for(let row in table_data_list){
           for(let key in table_data_list[row]) {
             head_row.push(key)
           }
           array_store_row.push(head_row);
           break;
           }
      for(let row in table_data_list){
           for(let key in table_data_list[row]) {
             col_row.push(table_data_list[row][key])
           }
           array_store_row.push(col_row);
           col_row = [];
           }
      let work_book = XLSX.utils.book_new();
      let sheet_product_info = XLSX.utils.aoa_to_sheet(array_store_row);
      XLSX.utils.book_append_sheet(work_book,sheet_product_info,'券商账户信息表');
      XLSX.writeFile(work_book,'券商账户信息表.xlsx');

    },

    resetForm(formName){
          this.$refs[formName].resetFields();
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

    initTable(){
        const _this = this;
        //_this.token = JSON.parse(this.$route.query.token);
        axios.get("http://192.168.1.31:8000/get_accounts?token="+'123456').then( res => {
        if(res.data.status_code === '200'){
            _this.tableData = res.data.account_list;
            _this.tableData_back = res.data.account_list;
            _this.tableDate_length = res.data.account_list.length;
            _this.tableDate_length_back = res.data.account_list.length;
          }else {
           _this.$router.push("/");
           alert("请先登录");
         }
        }
          ).catch(error => {
          console.log(error)
        })

    },

  }
};
</script>

<style scoped>
@import url(../../node_modules/element-ui/lib/theme-chalk/index.css);
</style>
