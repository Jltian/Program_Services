
<template>
  <div>
    <h1> 产品券商账户对应文件名信息 </h1>
    <el-col :span="1" style="float : right;margin-right: 181px;">
      <el-button
        type="success"
        @click="addFile"
        icon="el-icon-circle-plus-outline"
        size="mini"
      >新增文件</el-button>
    </el-col>
<el-table
    :data="tableData"
    style="width: 100% "
    :header-cell-style="{textAlign:'center'}"
    :cell-style="{textAlign: 'center'}"
>
    <el-table-column
      label="产品"
      width="330">
      <template slot-scope="scope">
        <span style="margin-left: 10px">{{ scope.row.product}}</span>
      </template>
    </el-table-column>
      <el-table-column
      label="券商"
      width="330">
      <template slot-scope="scope">
        <span >{{ scope.row.belong}}</span>
      </template>
    </el-table-column>
    <el-table-column
      label="文件名"
      width="330">
      <template slot-scope="scope">
        <span >{{ scope.row.account_number}}</span>
      </template>
    </el-table-column>
    <el-table-column
      label="是否有效"
      width="330">
      <template slot-scope="scope">
         <div slot="reference" class="name-wrapper">
              <el-tag size="medium">{{options[scope.row.valid_status]['label']}} </el-tag>
            </div>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="330">
      <template slot-scope="scope">
        <el-button
          size="mini"
           type="primary"
          @click="handleEdit(scope.$index, scope.row)">编辑</el-button>
      </template>
    </el-table-column>
</el-table>

  <el-dialog title="新增产品券商账户对应文件名信息" :visible.sync="dialogFormVisibles">
    <el-form :model="addForm" ref="addForm"  label-width="80px">
      <el-form-item label="账户ID" >
      <el-input v-model="addForm.account_id" :disabled="true"></el-input>
     </el-form-item>
      <el-form-item label="文件名">
      <el-input v-model="addForm.account_number" placeholder="请输入新增券商账户对应的对账单文件名"></el-input>
     </el-form-item>
    </el-form>
    <div slot="footer" class="dialog-footer">
      <el-button @click="dialogFormVisibles = false">取 消</el-button>
      <el-button type="primary" @click="addCreates()">确 定</el-button>
    </div>

  </el-dialog>

  <el-dialog title="编辑产品券商账户对应文件名信息" :visible.sync="dialogFormVisible">
    <el-form :model="editForm" ref="editForm"   label-width="80px" class="demo-editForm">
      <el-form-item label="文件名">
          <el-input v-model="editForm.file_name" placeholder="请输入要修改的文件名"></el-input>
      </el-form-item>
      <el-form-item label="有效状态" >
       <el-col :span="6">
      <el-select v-model="editForm.valid_status" placeholder="请选择有效状态">
        <el-option label="有效" value="1"></el-option>
        <el-option label="无效" value="0"></el-option>
      </el-select>
       </el-col>
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

export default {
name: "AccountDetail",
  data(){
  return {
    id : this.$route.params.id,
    file_id : '',
    tableData:[
    ],
    dialogFormVisible: false,
    dialogFormVisibles: false,
    editForm:{
      file_name : '',
      valid_status: ''
    },
    addForm:{
      account_id : '',
      account_number : '',
      valid_status : ''
    },
    options:[
        {
          value : "0",
          label : "无效"
        },{
          value : "1",
          label: "有效"
        }
      ],
  }
  },
  created() {
  const params = new URLSearchParams()
  params.append('account_id',this.id);
  axios.post('http://192.168.1.31:8000/get_react_files',params).then(
    res =>{
      this.tableData = res.data.file_list;
    })
  },
  methods:{
  handleEdit(index, row) {
    this.editForm.file_name = row['account_number'];
    this.editForm.valid_status = this.options[row['valid_status']]['label'];
    this.file_id = row['id'];
    this.dialogFormVisible = true;
  },
    fresh_table(){
    const params = new URLSearchParams()
    params.append('account_id',this.id);
      axios.post('http://192.168.1.31:8000/get_react_files',params).then(
    res =>{
      this.tableData = res.data.file_list;
    })
    },
    update(formName){
    this.editForm['file_id'] = this.file_id;
    this.$refs[formName].validate((valid) => {
      if(valid){
        axios.post('http://192.168.1.31:8000/update_file_content',this.editForm).then(
      res => {
        this.$message.success("文件配置修改成功");
        this.fresh_table();
        this.dialogFormVisible = false;
      }
    )
      }
    })

    },
  addFile(){
    this.addForm.account_id = this.id;
    this.dialogFormVisibles=true;
  },
  addCreates(){
    this.addForm.valid_status = 1;
    if(this.addForm.account_number === '' || this.addForm.account_number === null){
      this.$message.error('文件名信息不能为空');
      return false;
    }
    this.addForm.account_id = this.id;
    const params = new URLSearchParams();
    params.append('account_id',this.addForm.account_id);
    params.append('account_number',this.addForm.account_number);
    params.append('valid_status',this.addForm.valid_status);
    axios.post('http://192.168.1.31:8000/addFile',params).then(
      res =>{
        this.$message.success("新增关联对账单文件成功");
        this.fresh_table();
        this.dialogFormVisibles = false;
      }
    )
  }
  }
}
</script>

<style scoped>

</style>
