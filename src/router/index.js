import { createRouter, createWebHistory } from 'vue-router'
import login from '@/views/login.vue'
import home from '@/views/home.vue'
import LeaveData from '@/components/LeaveData.vue'
import LeaveDataCalendar from '@/components/LeaveDataCalendar.vue'
import AddLeave from '@/components/AddLeave.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
          path: '/home/list',
          component: LeaveData
        },
        {
          path: '/home/calendar',
          component: LeaveDataCalendar
        },
        {
          path: '/home/add',
          component: AddLeave
        },
      ]
    }
  ],
})

export default router
