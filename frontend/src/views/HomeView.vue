<template>
  <div class="container-fluid px-3 px-md-5 pb-5">
    <h1 class="text-center mt-3 mb-4 app-title">STOCK STALKER</h1>

    <div class="chart-section">
      <div class="chart-container mt-4">
        <div v-if="stockDataList.length === 0" class="no-stocks-message">
          <p>No stocks saved yet. Add stocks to your watchlist to see them here.</p>
        </div>
        <canvas v-else ref="chartCanvas"></canvas>
      </div>

      <div v-if="stockDataList.length > 5" class="selection-sidebar">
        <div class="stock-controls">
          <h5 class="mb-3">Chart Display (5 max)</h5>
          
          <div class="stock-selection-panel">
            <div class="mb-3" v-for="(stock, index) in stockDataList" :key="stock.symbol">
              <div class="form-check">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  :id="`stock-${index}`" 
                  :value="stock.symbol" 
                  v-model="selectedStocks"
                  :disabled="selectedStocks.length >= 5 && !selectedStocks.includes(stock.symbol)"
                >
                <label class="form-check-label" :for="`stock-${index}`" :style="{ color: stockColors[index % stockColors.length] }">
                  <strong>{{ stock.symbol }}</strong>
                </label>
              </div>
            </div>
          </div>

          <div class="mt-3 text-muted small">
            <p>Select up to 5 stocks to display in the chart.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="table-wrapper mt-4 mb-5">
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
              <tr v-for="(stock, index) in stockDataList" :key="stock.symbol" 
                 @click="viewStockDetails(stock.symbol)" 
                 class="stock-row">
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
    
    <div class="footer-spacer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';
import { useRouter } from 'vue-router';
import { cacheService } from '../utils/cacheService';

const router = useRouter();
const stockDataList = ref<any[]>([]);
const stockColors = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#9b59b6'];
const selectedStocks = ref<string[]>([]);

const chartCanvas = ref<HTMLCanvasElement | null>(null);
let stockChart: Chart | null = null;

const backendURL = import.meta.env.VITE_BACKEND_URL;

const displayedStocks = computed(() => {
  if (stockDataList.value.length <= 5) {
    return stockDataList.value;
  }
  
  if (selectedStocks.value.length > 0) {
    return stockDataList.value.filter(stock => 
      selectedStocks.value.includes(stock.symbol)
    );
  }
  
  return [];
});

function setupStockChangeListener() {
  window.addEventListener('stock-change', () => {
    const token = localStorage.getItem("token");
    if (token) {
      cacheService.invalidatePattern('user_stocks');
      cacheService.invalidatePattern('profile_stocks');
      fetchStockData();
    }
  });
}

async function fetchStockData() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found!");
      return;
    }

    const cacheKey = `user_stocks_${token.slice(-10)}`;
    
    const data = await cacheService.getOrFetch(
      cacheKey,
      async () => {
        console.log("Cache miss - fetching fresh data from API");
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

        return await response.json();
      },
      { ttl: 15 * 60 * 1000 }
    );

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

    if (stockDataList.value.length > 5) {
      selectedStocks.value = stockDataList.value.slice(0, 5).map(stock => stock.symbol);
    } else {
      selectedStocks.value = stockDataList.value.map(stock => stock.symbol);
    }
  } catch (error) {
    console.error("Error fetching stock data:", error);
  }
}

function updateChart() {
  if (stockChart) stockChart.destroy();
  if (!chartCanvas.value) return;
  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx) return;
  
  const datasets = [];
  let labels = [];
  
  if (displayedStocks.value.length > 0) {
    labels = displayedStocks.value[0].historyDates.map((date: string) => new Date(date));
    
    datasets.push(...displayedStocks.value.map((stock, index) => {
      const stockIndex = stockDataList.value.findIndex(s => s.symbol === stock.symbol);
      const colorIndex = stockIndex !== -1 ? stockIndex : index;
      
      return {
        label: stock.symbol,
        data: stock.history,
        borderColor: stockColors[colorIndex % stockColors.length],
        backgroundColor: stockColors[colorIndex % stockColors.length] + '33',
        fill: true,
      };
    }));
  } else if (stockDataList.value.length > 0) {
    labels = stockDataList.value[0].historyDates.map((date: string) => new Date(date));
  } else {
    const today = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);
      labels.push(date);
    }
  }
  
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
          display: false,
        },
        tooltip: {
          enabled: datasets.length > 0,
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
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.05)',
          },
        },
        y: {
          beginAtZero: false,
          ticks: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.05)',
          },
          suggestedMin: datasets.length === 0 ? 0 : undefined,
          suggestedMax: datasets.length === 0 ? 100 : undefined,
        },
      },
      animation: {
        duration: 600,
      },
    },
  });
  
  if (datasets.length === 0 && stockDataList.value.length > 0) {
    const centerX = ctx.canvas.width / 2;
    const centerY = ctx.canvas.height / 2;
    ctx.font = '16px Arial';
    ctx.fillStyle = '#777';
    ctx.textAlign = 'center';
    ctx.fillText('No stocks selected. Use the panel on the right to select stocks to display.', centerX, centerY);
  }
}

function viewStockDetails(symbol: string) {
  router.push({ name: 'stock-details', params: { symbol } });
}

onMounted(async () => {
  setupStockChangeListener();
  await fetchStockData();
  updateChart();
});

watch(selectedStocks, updateChart);

watch(displayedStocks, updateChart, { deep: true });
</script>

<style scoped>
.app-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  color: var(--text-color);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
  font-size: 2.5rem;
  margin-bottom: 2rem;
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
  font-size: 1.1rem;
  padding: 15px;
}

.custom-table tr:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.chart-section {
  display: flex;
  width: 90%;
  max-width: 1200px;
  margin: 0 auto;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-container {
  flex: 1;
  height: 550px;
  padding: 1.5rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 0;
}

.selection-sidebar {
  width: 250px;
  height: 550px;
  padding: 1.5rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  margin-top: 1.5rem;
}

.stock-controls {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.stock-selection-panel {
  flex: 1;
  overflow-y: auto;
  padding-right: 5px;
  margin-bottom: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.stock-selection-panel::-webkit-scrollbar {
  width: 6px;
}

.stock-selection-panel::-webkit-scrollbar-track {
  background: transparent;
}

.stock-selection-panel::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.no-stocks-message {
  text-align: center;
  color: #777;
  font-size: 1.2rem;
}

canvas {
  width: 100% !important;
  height: 100% !important;
  max-height: 100%;
}

.table-wrapper {
  width: 90%;
  max-width: 1200px;
  margin: 0 auto;
  margin-bottom: 50px;
}

.scrollable-table {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.stock-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.stock-row:hover {
  background-color: rgba(0, 0, 0, 0.08);
}

.form-check-label {
  cursor: pointer;
}

.footer-spacer {
  height: 40px;
  width: 100%;
}

@media (max-width: 768px) {
  .chart-section {
    flex-direction: column;
  }
  
  .selection-sidebar {
    width: 100%;
    height: auto;
    margin-top: 20px;
  }
  
  .chart-container {
    height: 400px;
  }
}
</style>
