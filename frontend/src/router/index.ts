import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PopularStocks from '@/views/PopularStocks.vue'
import Profile from '@/views/Profile.vue'
import Login from '@/views/Login.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/popular',
    name: 'popular',
    component: PopularStocks
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile
  },
  {
    path: '/login',
    name: 'login',
    component: Login
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');

  if(token){
    next();
  }
  else if(to.path !== '/login'){
    next('/login');
  }
  else{
    next();
  }
});

if(window.location.search.includes("token=")){
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    sessionStorage.setItem("token", token);
    window.history.replaceState({}, document.title, "/");
    window.location.reload();
  }

}

export default router
