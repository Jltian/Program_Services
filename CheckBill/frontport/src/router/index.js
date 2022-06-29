import Vue from 'vue'
import Router from 'vue-router'
import index from '@/components/index'
import Login from '@/components/Login'
import DataManageCenter from "../components/DataManageCenter";
import Bills from "../components/Bills";
import AccountInformation from "../components/AccountInformation";
import IntegratedManage from "../components/IntegratedManage";
import AccountDetail from "../components/AccountDetail";

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Login',
      component: Login,
       meta: {
        title: '登录界面'
      }
    },
    {
      path:'/Index',
      name:'Index',
      component:index,
      meta: {
        title: '导航'
      }
    },
    {
      path: '/DataManageCenter',
      name:'DataManageCenter',
      component: DataManageCenter,
      meta: {
        title: '数据管理中心'
      }

    },
    {
      path: '/Bills',
      name:'Bills',
      component: Bills,
      meta: {
        title: '未到对账单管理'
      }
    }, {
      path: '/AccountInformation',
      name:'AccountInformation',
      component: AccountInformation,
      meta: {
        title: '券商信息维护'
      }},
     {
      path: '/AccountDetail',
      name:'AccountDetail',
      component: AccountDetail,
      meta: {
        title: '券商信息维护'
      }},
    {
      path: '/IntegratedManage',
      name:'IntegratedManage',
      component: IntegratedManage,
      meta: {
        title: '综合管理'
      }


    },
  ],
    mode:'history',
})
