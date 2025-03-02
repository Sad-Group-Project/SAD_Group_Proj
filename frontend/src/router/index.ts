import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import HomePageView from '../views/HomePage.vue'
import SearchPageView from '../views/search.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/test',
    name: 'homepage',
    component: HomePageView
  },
  {
    path: '/search',
    name: 'searchpage',
    component: SearchPageView
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
