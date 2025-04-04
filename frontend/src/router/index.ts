/// <reference types="vite/client" />
import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PopularStocks from '@/views/PopularStocks.vue'
import Profile from '@/views/Profile.vue'
import Login from '@/views/Login.vue'
import Search from '@/views/Search.vue'

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
  {
    path: '/search',
    name: 'search',
    component: Search
  },
]

import axios from "axios";

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token');

  if (token) {
    const backendUrl = import.meta.env.VITE_BACKEND_URL;
    try {
      await axios.get(`${backendUrl}/api/auth/verify`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      next();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.log("Token invalid or expired:", error.response?.data?.message);
      } else {
        console.log("An unexpected error occurred:", error);
      }
      localStorage.removeItem("token");
      next("/login");
    }
  } else if (to.path !== "/login") {
    next("/login");
  } else {
    next();
  }
});

if(window.location.search.includes("token=")){
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    localStorage.setItem("token", token);
    window.history.replaceState({}, document.title, "/");
    window.location.href = "/";
  }

}

export default router
