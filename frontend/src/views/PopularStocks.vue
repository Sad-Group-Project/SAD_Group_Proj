<template>
    <h1>Welcome to popular stocks page</h1>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const popularStocks = ref([]);

onMounted(async () => {
  popularStocks.value = await fetchPopularStocks();
});
</script>

<style scoped>
ul {
  list-style-type: none;
  padding: 0;
}
li {
  padding: 8px 0;
}
</style>
