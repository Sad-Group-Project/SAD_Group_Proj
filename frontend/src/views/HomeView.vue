<template>
  <div>
    <h1 class="text-center my-4 app-title">STOCK STALKER</h1>

    <div class="chart-container mt-4">
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div class="table-wrapper mt-4">
      <div class="scrollable-table">
        <div class="table-responsive">
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
                <td :style="{ color: stockColors[index % stockColors.length] }">
                  <strong>{{ stock.symbol }}</strong><br />
                  <small>{{ stock.company_name }}</small>
                </td>
                <td :class="{ positive: stock.change > 0, negative: stock.change < 0 }">
                  ${{ stock.price.toFixed(2) }}
                </td>
                <td :class="{ positive: stock.change > 0, negative: stock.change < 0 }">
                  {{ stock.change.toFixed(2) }}%
                </td>
                <td :style="{ color: stock.recommendation === 'buy' ? 'green' : stock.recommendation === 'sell' ? 'red' : 'orange' }">
                  {{ stock.recommendation.toUpperCase() }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';

const stockDataList = ref<any[]>([]);
const stockColors = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#9b59b6'];

const chartCanvas = ref<HTMLCanvasElement | null>(null);
let stockChart: Chart | null = null;

const backendURL = import.meta.env.VITE_BACKEND_URL;

async function fetchStockData() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found!");
      return;
    }

    const response = await fetch(`${backendURL}/api/user_stocks`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch saved stocks.");
    }

    const data = await response.json();

    stockDataList.value = data.saved_stocks.map((stock: any) => {
      return {
        symbol: stock.symbol,
        company_name: stock.company_name,
        price: stock.current_info.price,
        change: stock.current_info.change,
        recommendation: stock.current_info.recommendation,
        history: stock.current_info.history.map((point: any) => point.price),
        historyDates: stock.current_info.history.map((point: any) => point.date),
      };
    });
  } catch (error) {
    console.error("Error fetching stock data:", error);
  }
}

function updateChart() {
  if (stockChart) stockChart.destroy();
  if (!chartCanvas.value) return;
  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx || stockDataList.value.length === 0) return;

  const labels = stockDataList.value[0].historyDates.map((date: string) => new Date(date));

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
      labels,
      datasets,
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'day',
            tooltipFormat: 'MMM dd',
            displayFormats: {
              day: 'MMM dd',
            }
          },
          ticks: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
            maxRotation: 30,
            minRotation: 30,
          }
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

onMounted(async () => {
  await fetchStockData();
  updateChart();
});

watch(stockDataList, updateChart, { deep: true });
</script>

<style scoped>
.app-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  color: var(--text-color);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

.positive {
  color: #27ae60;
}

.negative {
  color: #c0392b;
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

.chart-container {
  width: 100%;
  max-width: 800px;
  margin: auto;
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.table-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.scrollable-table {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 6px;
}

</style>
