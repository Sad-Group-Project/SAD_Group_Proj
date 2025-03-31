<template>
  <div>
    <div class="header-controls">
      <router-link to="/profile" class="btn btn-primary m-1">Profile</router-link>
      <router-link to="/popular" class="btn btn-secondary m-1">Popular Stocks</router-link>
    </div>

    <h1 class="text-center my-4 app-title">STOCK STALKER</h1>

    <div class="table-responsive mt-4">
      <table class="table table-bordered custom-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Price</th>
            <th>Change (%)</th>
            <th>Recommendation</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(stock, index) in stockDataList" :key="stock.symbol">
            <td :style="{ color: stockColors[index % stockColors.length] }">{{ stock.symbol }}</td>
            <td :class="{ positive: stock.change > 0, negative: stock.change < 0 }">
              ${{ stock.price.toFixed(2) }}
            </td>
            <td :class="{ positive: stock.change > 0, negative: stock.change < 0 }">
              {{ stock.change.toFixed(2) }}%
            </td>
            <td :style="{ color: stock.recommendation === 'Buy' ? 'green' : 'red' }">
              {{ stock.recommendation }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="chart-container mt-4">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import Chart from 'chart.js/auto';

const stockDataList = ref<any[]>([]);
const stockColors = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#9b59b6'];

const chartCanvas = ref<HTMLCanvasElement | null>(null);
let stockChart: Chart | null = null;

function updateChart() {
  if (stockChart) stockChart.destroy();
  if (!chartCanvas.value) return;
  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx) return;

  const datasets = stockDataList.value.map((stock, index) => ({
    label: stock.symbol,
    data: stock.history,
    borderColor: stockColors[index % stockColors.length],
    backgroundColor: stockColors[index % stockColors.length] + '33',
    fill: true,
  }));

  stockChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: stockDataList.value[0]?.historyDates || [],
      datasets,
    },
    options: {
      plugins: {
        legend: {
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
          },
        },
      },
      scales: {
        x: { ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color') } },
        y: { ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-color') } },
      },
    },
  });
}

onMounted(() => updateChart());
watch(stockDataList, updateChart, { deep: true });
</script>

<style scoped>
.app-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  color: var(--text-color);
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}
.positive { color: #27ae60; }
.negative { color: #c0392b; }
.custom-table th, .custom-table td {
  vertical-align: middle;
  font-size: 0.95rem;
  padding: 12px;
}
.custom-table tr:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
.chart-container {
  width: 100%;
  max-width: 800px;
  margin: auto;
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
</style>
