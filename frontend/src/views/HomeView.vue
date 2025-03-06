<template>
  <div :data-theme="theme" class="full-screen offset-top">
    <header style="display: flex; flex-direction: column; align-items: center; padding: 10px; gap: 10px;">
      <div style="display: flex; gap: 10px; align-items: center; justify-content: flex-start;">
        <button class="login-button" @click="openLoginModal">Login</button>
        
      <button class="theme-toggle" @click="toggleTheme">Switch Theme</button>
      <RouterLink to="/profile">
        <button>Route to Profile</button>
      </RouterLink>
      <RouterLink to="/popular">
        <button>Route to Popular Stocks</button>
      </RouterLink>
      </div>
      <h1 style="text-align: center; width: 100%; margin-top: 10px;">STOCK STALKER</h1>
    </header>

    

    <div class="container full-screen reduced-size">
      <div class="search-wrapper" style="display: flex; flex-direction: column; align-items: center; gap: 15px;">
        <div class="input-box" style="display: flex; flex-direction: column; align-items: center; margin-top: 10px;">
          <input type="text" v-model="inputStockSymbol" placeholder="Enter stock symbol" />
          <input type="text" v-model="discordUsername" placeholder="Enter Discord username" />
          
          <input type="number" v-model="priceBought" placeholder="Enter price bought" />
          
          <input type="number" v-model="sellingPrice" placeholder="Enter selling price" />
          
          <input type="number" v-model="shareAmount" placeholder="Enter shares amount" />
        <button @click="sendDataToBackend">Send</button>
        </div>
        <div class="search-bar centered">
          <input
            type="text"
            v-model="stockSymbol"
            placeholder="Search for a stock symbol (e.g., AAPL, TSLA)..."
          />
          <button @click="addStock">Add Stock</button>
        </div>
      </div>

      <div class="content-wrapper">
        <div class="dashboard">
          <h2>Stock Dashboard</h2>
          <table>
            <thead>
              <tr>
                <th :style="{ color: themes[theme].text }">Symbol</th>
                <th :style="{ color: themes[theme].text }">Price</th>
                <th :style="{ color: themes[theme].text }">Change (%)</th>
                <th :style="{ color: themes[theme].text }">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(stock, index) in stockDataList" :key="stock.symbol">
                <td :style="{ color: stockColors[index % stockColors.length] }">{{ stock.symbol }}</td>
                <td :style="{ color: stock.change > 0 ? 'green' : 'red' }">
                  ${{ stock.price.toFixed(2) }}
                </td>
                <td :class="{'positive': stock.change > 0, 'negative': stock.change < 0}">
                  {{ stock.change.toFixed(2) }}%
                </td>
                <td :style="{ color: stock.recommendation === 'Buy' ? 'green' : 'red' }">
                  {{ stock.recommendation }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="chart-container">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import Chart from 'chart.js/auto';
import { faker } from '@faker-js/faker';

const themes = {
  light: { bg: '#ffffff', text: '#000000' },
  dark: { bg: '#1e1e1e', text: '#f4f4f4' },
  'high-contrast': { bg: '#000000', text: '#ffff00' },
  blue: { bg: '#e3f2fd', text: '#0d47a1' },
  green: { bg: '#e8f5e9', text: '#1b5e20' },
  warm: { bg: '#fff3e0', text: '#6d4c41' }
};

const themeKeys = Object.keys(themes);
const themeIndex = ref(2);
const theme = ref('high-contrast');

const stockColors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];
const stockSymbol = ref('');
const stockDataList = ref([]);
const chartCanvas = ref(null);
let stockChart = null;

const toggleTheme = async () => {
  themeIndex.value = (themeIndex.value + 1) % themeKeys.length;
  theme.value = themeKeys[themeIndex.value];
  applyThemeStyles();
};

const applyThemeStyles = () => {
  const selectedTheme = themes[theme.value];
  document.documentElement.style.setProperty('--bg-color', selectedTheme.bg);
  document.documentElement.style.setProperty('--text-color', selectedTheme.text);
  document.body.style.backgroundColor = selectedTheme.bg;
  document.body.style.color = selectedTheme.text;
  updateChart();
};

const openLoginModal = () => {
  alert("Login functionality is not implemented yet.");
};

const generateStockHistory = () => {
  return Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    price: parseFloat(faker.finance.amount(50, 200, 2))
  }));
};

const addStock = async () => {
  const backendURL = import.meta.env.VITE_BACKEND_URL

  if (!stockSymbol.value) return;

  try {
    const response = await fetch(`${backendURL}/api/stocks?symbol=${stockSymbol.value.toUpperCase()}`);
    const stockData = await response.json();

    stockDataList.value.push({
      symbol: stockData.symbol,
      price: stockData.price,
      change: stockData.change,
      recommendation: stockData.recommendation,
      history: stockData.history
    });
  } catch (error) {
    console.error('Error fetching stock data:', error);
  }

  stockSymbol.value = '';
  updateChart();
};

const updateChart = () => {
  if (!chartCanvas.value) return;
  if (stockChart) stockChart.destroy();

  stockChart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels: stockDataList.value[0]?.history.map(entry => entry.date) || [],
      datasets: stockDataList.value.map((stock, index) => ({
        label: stock.symbol,
        data: stock.history.map(entry => entry.price),
        borderColor: stockColors[index % stockColors.length],
        backgroundColor: stockColors[index % stockColors.length] + '55',
        fill: true,
      }))
    },
    options: {
      plugins: {
        legend: { labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color') } }
      },
      scales: {
        x: { type: 'category', ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color') } },
        y: { ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color') } }
      }
    }
  });
};

onMounted(() => {
  applyThemeStyles();
  updateChart();
});

watch([stockDataList, theme], () => {
  updateChart();
  applyThemeStyles();
}, { deep: true });
const sendDataToBackend = () => {
  const requestData = {
    discordUsername: discordUsername.value,
    stockSymbol: inputStockSymbol.value,
    priceBought: priceBought.value,
    sellingPrice: sellingPrice.value,
    shareAmount: shareAmount.value
  };
  console.log('Sending data to fake backend:', requestData);
  alert('Your request has been received. A Discord bot will notify you when the desired selling price is reached.');
};

</script>

<style>
.positive { color: green; }
.negative { color: red; }
</style>