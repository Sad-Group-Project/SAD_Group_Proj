<template>
  <div class="container mt-3">
    <div class="text-center mb-4">
      <input
        v-model="stockSymbol"
        @keyup.enter="goToSearchPage"
        class="form-control d-inline-block w-auto me-2"
        placeholder="Search stock symbol"
      />
      <button class="btn btn-primary" @click="goToSearchPage">Search</button>
    </div>

    <h2 class="text-center">🔥 Popular Stocks (Chart)</h2>
    <div class="chart-container my-4">
      <canvas ref="chartCanvas"></canvas>
    </div>

    <h2 class="text-center">📊 Stock Summary</h2>
    <div class="table-wrapper mt-4">
      <div class="table-responsive">
        <table class="table table-bordered custom-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Company</th>
              <th>Price</th>
              <th>Change</th>
              <th>% Change</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in popularStocks" :key="stock.symbol">
              <td><strong>{{ stock.symbol }}</strong></td>
              <td>{{ stock.company_name }}</td>
              <td>${{ stock.current_price?.toFixed(2) }}</td>
              <td :class="{ positive: stock.change > 0, negative: stock.change < 0 }">
                {{ stock.change?.toFixed(2) }}
              </td>
              <td :class="{ positive: stock.percent_change > 0, negative: stock.percent_change < 0 }">
                {{ stock.percent_change?.toFixed(2) }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-5">
      <h2 class="text-center">📰 Trending Stock News</h2>
      <div class="card my-3">
        <div class="card-body">
          <p class="text-muted mb-0">Trending stock news will appear here soon...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';

Chart.register(...registerables);

const stockSymbol = ref('');
const popularStocks = ref([]);
const chartCanvas = ref(null);
let chartInstance = null;

const router = useRouter();

function goToSearchPage() {
  if (stockSymbol.value.trim()) {
    router.push({ name: 'search', query: { q: stockSymbol.value.trim() } });
    stockSymbol.value = '';
  }
}

async function fetchPopularStocks() {
  try {
    const backendURL = import.meta.env.VITE_BACKEND_URL;
    const res = await fetch(`${backendURL}/api/popular_stocks`);
    popularStocks.value = await res.json();
    drawChart();
  } catch (err) {
    console.error('Error fetching popular stocks:', err);
  }
}

function drawChart() {
  if (!chartCanvas.value || !popularStocks.value.length) return;

  if (chartInstance) {
    chartInstance.destroy();
  }

  const ctx = chartCanvas.value.getContext('2d');

  const datasets = popularStocks.value.map((stock, index) => ({
    label: stock.symbol,
    data: stock.mini_chart_data.timestamps.map((timestamp, i) => ({
      x: new Date(timestamp),
      y: stock.mini_chart_data.prices[i]
    })),
    borderColor: getColor(index),
    backgroundColor: getColor(index) + '33',
    fill: true,
    tension: 0.4,
  }));

  const labels = popularStocks.value[0].mini_chart_data.timestamps.map(ts => new Date(ts));

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      parsing: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color')
          }
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'hour',
            tooltipFormat: 'hh:mm a',
            displayFormats: {
              hour: 'hh:mm a',
            },
          },
          ticks: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
            autoSkip: true,
            maxRotation: 0,
            minRotation: 0,
          },
        },
        y: {
          ticks: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
          },
        },
      },
    },
  });
}

function getColor(index) {
  const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f'];
  return colors[index % colors.length];
}

onMounted(() => {
  fetchPopularStocks();
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  max-width: 900px;
  height: 300px;
  margin: auto;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 1rem;
}

.table-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.custom-table th,
.custom-table td {
  vertical-align: middle;
  font-size: 0.95rem;
  padding: 12px;
}

.custom-table tr:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.positive {
  color: #27ae60;
}

.negative {
  color: #c0392b;
}
</style>
