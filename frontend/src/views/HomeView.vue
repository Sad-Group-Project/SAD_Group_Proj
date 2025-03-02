<template>
  <div :data-theme="theme" class="min-vh-100 d-flex flex-column">
    <header class="py-3 border-bottom">
      <div class="container">
        <div class="d-flex justify-content-end mb-2">
          <button class="btn btn-outline-primary me-2" @click="openLoginModal">Login</button>
          <button class="btn btn-outline-secondary" @click="toggleTheme">Switch Theme</button>
        </div>
        <div class="text-center">
          <h1 class="my-0">STOCK STALKER</h1>
        </div>
      </div>
    </header>

    <main class="container flex-grow-1 my-4">
      <div class="row mb-4">
        <div class="col-12">
          <div class="input-group">
            <input
              type="text"
              v-model="stockSymbol"
              class="form-control"
              placeholder="Search for a stock symbol (e.g., AAPL, TSLA)..."
            />
            <button class="btn btn-success" @click="addStock">Add Stock</button>
          </div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-4 mb-3 mb-md-0">
          <div class="card">
            <div class="card-body">
              <div class="mb-3">
                <input
                  type="text"
                  v-model="discordUsername"
                  class="form-control"
                  placeholder="Enter Discord username"
                />
              </div>
              <div class="mb-3">
                <input
                  type="text"
                  v-model="inputStockSymbol"
                  class="form-control"
                  placeholder="Enter stock symbol"
                />
              </div>
              <div class="mb-3">
                <input
                  type="number"
                  v-model="priceBought"
                  class="form-control"
                  placeholder="Enter price bought"
                />
              </div>
              <div class="mb-3">
                <input
                  type="number"
                  v-model="sellingPrice"
                  class="form-control"
                  placeholder="Enter selling price"
                />
              </div>
              <div class="mb-3">
                <input
                  type="number"
                  v-model="shareAmount"
                  class="form-control"
                  placeholder="Enter shares amount"
                />
              </div>
              <button class="btn btn-primary w-100" @click="sendDataToBackend">
                Send
              </button>
            </div>
          </div>
        </div>
        <div class="col-md-8">
          <div class="card">
            <div class="card-header">
              Stock Dashboard
            </div>
            <div class="card-body p-0">
              <table class="table table-striped mb-0">
                <thead class="table-light">
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
                    <td :class="{'text-success': stock.change > 0, 'text-danger': stock.change < 0}">
                      {{ stock.change.toFixed(2) }}%
                    </td>
                    <td :style="{ color: stock.recommendation === 'Buy' ? 'green' : 'red' }">
                      {{ stock.recommendation }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <canvas ref="chartCanvas" class="w-100"></canvas>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="bg-light py-3">
      <div class="container text-center">
        <p class="mb-0">STOCK STALKER © 2025</p>
      </div>
    </footer>
  </div>
</template>


<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import Chart from 'chart.js/auto';

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