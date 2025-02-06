<template>
  <div class="home">
    <img alt="Vue logo" src="../assets/logo.png">
    <HelloWorld msg="Welcome to Your Vue.js + TypeScript App"/>
  </div>
</template>

<script lang="ts">
declare global {
  interface ImportMetaEnv {
    VITE_BACKEND_URL: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

import { defineComponent, onMounted } from 'vue';
import axios from 'axios';
import HelloWorld from '@/components/HelloWorld.vue';

export default defineComponent({
  name: 'HomeView',
  components: {
    HelloWorld,
  },

  setup() {
    const backendUrl =  "http://127.0.0.1:5000";
    console.log("Backend URL:", backendUrl);

    const fetchStocks = async () => {
      try {
        const response = await axios.get(`${backendUrl}/api/stocks`);
        console.log("API Response:", response.data);
      } catch (error) {
        console.error("Error fetching data from /api/stocks:", error);
      }
    };

    onMounted(fetchStocks);

    return {};
  },
});
</script>
