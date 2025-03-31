<template>
  <div class="container py-4">
    <h1 class="text-center mb-4 app-title">👤 Profile</h1>

    <div class="mb-4 text-center">
      <button class="btn btn-warning" @click="toggleTheme">Switch Theme</button>
    </div>

    <div class="input-box">
      <h5>Discord Stock Alert</h5>
      <label>Stock Symbol</label>
      <input v-model="inputStockSymbol" class="form-control mb-2" placeholder="e.g., TSLA" />
      <label>Discord Username</label>
      <input v-model="discordUsername" class="form-control mb-2" placeholder="e.g., user#1234" />
      <label>Price Bought</label>
      <input v-model="priceBought" class="form-control mb-2" type="number" />
      <label>Selling Price</label>
      <input v-model="sellingPrice" class="form-control mb-2" type="number" />
      <label>Share Amount</label>
      <input v-model="shareAmount" class="form-control mb-2" type="number" />
      <button class="btn btn-success mt-2" @click="sendDataToBackend">Send</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';

const inputStockSymbol = ref('');
const discordUsername = ref('');
const priceBought = ref(0);
const sellingPrice = ref(0);
const shareAmount = ref(0);

function sendDataToBackend() {
  alert(`Discord alert set for ${inputStockSymbol.value} at $${sellingPrice.value}`);
  console.log({
    symbol: inputStockSymbol.value,
    discord: discordUsername.value,
    boughtAt: priceBought.value,
    sellAt: sellingPrice.value,
    shares: shareAmount.value,
  });
}

const themes = {
  'light': { bg: '#ffffff', text: '#000000' },
  'dark': { bg: '#1e1e1e', text: '#f5f5f5' },
  'high-contrast': { bg: '#000000', text: '#ffff00' },
  'blue': { bg: '#d0e7ff', text: '#003366' },
  'green': { bg: '#e8f5e9', text: '#1b5e20' },
  'warm': { bg: '#fff3e0', text: '#bf360c' },
};

const themeKeys = Object.keys(themes);
const currentThemeIndex = ref(0);

function applyThemeStyles() {
  const theme = themes[themeKeys[currentThemeIndex.value]];
  document.documentElement.style.setProperty('--bg-color', theme.bg);
  document.documentElement.style.setProperty('--text-color', theme.text);
  document.body.style.backgroundColor = theme.bg;
  document.body.style.color = theme.text;
}

function toggleTheme() {
  currentThemeIndex.value = (currentThemeIndex.value + 1) % themeKeys.length;
  applyThemeStyles();
}

onMounted(() => applyThemeStyles());
</script>

<style scoped>
.app-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  color: var(--text-color);
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}
.input-box {
  max-width: 500px;
  margin: auto;
  background: rgba(255, 255, 255, 0.03);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
</style>
