import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

import login from '@/views/login.vue'
import home from '@/views/home.vue'
import LeaveData from '@/components/LeaveData.vue'
import LeaveDataCalendar from '@/components/LeaveDataCalendar.vue'
import AddLeave from '@/components/AddLeave.vue'
import Manager from '@/views/manager.vue'
import ManagerList from '@/components/ManagerList.vue'
import ManagerCalendar from '@/components/ManagerCalendar.vue'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      name: 'login',
      component: login
    },
    {
      path: '/home',
      name: 'home',
      component: home,
      children: [
        {
          path: 'list',
          component: LeaveData
        },
        {
          path: 'calendar',
          component: LeaveDataCalendar
        },
        {
          path: 'add',
          
          component: AddLeave
        },
      ]
    },
    {
      path: '/home/manager',
      name: 'manager',
      component: Manager,
      children: [
        {
          path: 'list',
          component: ManagerList
        },
        {
          path: 'calendar',
          component: ManagerCalendar
        }
      ]
    }
  ],
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.path === '/') {
    return next()
  }

  if (!userStore.isLoggedIn) {
    return next('/')
  }

  if (to.path.startsWith('/home/manager') && !userStore.isManager) {
    return next('/home/list')
  }

  next()
})

export default router
