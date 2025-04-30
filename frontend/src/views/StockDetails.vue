<template>
  <div class="container mt-4">
    <div class="card mb-4 stock-header" v-if="symbol">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <h1 class="mb-1">
              <span v-if="!loading && stockData.company_info.name">{{ stockData.company_info.name }} ({{ symbol }})</span>
              <span v-else>{{ symbol }}</span>
              <div v-if="loading && !stockData.company_info.name" class="skeleton-text w-50"></div>
            </h1>
            <p class="text-muted mb-2" v-if="!loading && stockData.company_info.exchange">
              {{ stockData.company_info.exchange }} | {{ stockData.company_info.sector }}
            </p>
            <div v-else class="skeleton-text w-25 mb-2"></div>
            
            <h2 class="mb-0" v-if="loadingState.priceLoaded">
              ${{ formatPrice(stockData.price_data.current_price) }}
            </h2>
            <div v-else class="skeleton-text w-25"></div>
            
            <div class="d-flex align-items-center mt-1" v-if="loadingState.priceLoaded">
              <span 
                :class="stockData.price_data.day_change >= 0 ? 'text-success' : 'text-danger'"
                class="h5 mb-0"
              >
                {{ stockData.price_data.day_change >= 0 ? '+' : '' }}{{ formatPrice(stockData.price_data.day_change) }} 
                ({{ formatPrice(stockData.price_data.day_change_percent) }}%)
              </span>
              <span class="text-muted ms-2">Today</span>
            </div>
            <div v-else class="skeleton-text w-25"></div>
          </div>
          <div class="text-end">
            <div v-if="loadingState.financialsLoaded" class="recommendation-badge" :class="getRecommendationClass()">
              {{ formatRecommendation(stockData.financial_metrics.recommendation) }}
            </div>
            <div v-else class="skeleton-badge"></div>
            <div class="mt-2">
              <button class="btn btn-sm btn-outline-primary me-1" @click="saveStock" :disabled="loading">
                Save to Watchlist
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h3 class="card-title mb-0">Price History</h3>
          <div class="btn-group time-filter">
            <button 
              v-for="period in timePeriods" 
              :key="period.value"
              @click="changeTimePeriod(period.value)"
              :class="['btn', 'btn-sm', currentPeriod === period.value ? 'btn-primary' : 'btn-outline-primary']"
              :disabled="!loadingState.chartDataLoaded"
            >
              {{ period.label }}
            </button>
          </div>
        </div>
        <div class="chart-container">
          <div v-if="!loadingState.chartDataLoaded" class="chart-loading-indicator">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading price history...</p>
          </div>
          <canvas ref="chartCanvas" :class="{'d-none': !loadingState.chartDataLoaded}"></canvas>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6 mb-4">
        <div class="card h-100">
          <div class="card-header">
            <h4 class="card-title mb-0">Key Statistics</h4>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-6 mb-3" v-for="(stat, index) in keyStatsList" :key="index">
                <div class="stat-label">{{ stat.label }}</div>
                <div class="stat-value" v-if="loadingState.statsLoaded">
                  {{ formatStatValue(stat.value, stat.formatter) }}
                </div>
                <div v-else class="skeleton-text"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 mb-4">
        <div class="card h-100">
          <div class="card-header">
            <h4 class="card-title mb-0">Financial Metrics</h4>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-6 mb-3" v-for="(metric, index) in financialMetricsList" :key="index">
                <div class="stat-label">{{ metric.label }}</div>
                <div class="stat-value" v-if="loadingState.financialsLoaded">
                  {{ formatStatValue(metric.value, metric.formatter) }}
                </div>
                <div v-else class="skeleton-text"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-4" v-if="loadingState.companyInfoLoaded">
      <div class="card-header">
        <h4 class="card-title mb-0">About {{ stockData.company_info.name }}</h4>
      </div>
      <div class="card-body">
        <p>{{ stockData.company_info.description }}</p>
        <div class="row mt-3">
          <div class="col-md-6">
            <div class="d-flex mb-2">
              <div class="fw-bold me-2">Industry:</div>
              <div>{{ stockData.company_info.industry }}</div>
            </div>
            <div class="d-flex">
              <div class="fw-bold me-2">Employees:</div>
              <div>{{ stockData.company_info.employees ? formatNumber(stockData.company_info.employees) : 'N/A' }}</div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="d-flex mb-2">
              <div class="fw-bold me-2">Website:</div>
              <a :href="stockData.company_info.website" target="_blank">{{ stockData.company_info.website }}</a>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="card mb-4">
      <div class="card-header">
        <h4 class="card-title mb-0">About</h4>
      </div>
      <div class="card-body">
        <div class="skeleton-text"></div>
        <div class="skeleton-text"></div>
        <div class="skeleton-text w-75"></div>
      </div>
    </div>

    <div v-if="showConfirmModal" class="modal-backdrop">
      <div class="modal-content-custom">
        <h5>Add {{ symbol }} to your saved stocks?</h5>
        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" :disabled="isSaving" @click="showConfirmModal = false">Cancel</button>
          <button class="btn btn-primary d-flex align-items-center" :disabled="isSaving" @click="confirmSaveStock">
            <span v-if="isSaving" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            <span v-if="!isSaving">Yes, Add</span>
            <span v-else>Adding...</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showSaveModal" class="modal-backdrop">
      <div class="modal-content-custom text-center">
        <h5>✅ {{ stockData.symbol }} saved successfully!</h5>
        <button class="btn btn-success mt-3" @click="showSaveModal = false">Close</button>
      </div>
    </div>

    <div v-if="showErrorModal" class="modal-backdrop">
      <div class="modal-content-custom text-center">
        <h5>⚠️ {{ errorMessage }}</h5>
        <button class="btn btn-primary mt-3" @click="showErrorModal = false">OK</button>
      </div>
    </div>
    
    <div v-if="error" class="alert alert-danger mt-3" role="alert">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';
import { cacheService } from '../utils/cacheService';

Chart.register(...registerables);

const route = useRoute();
const router = useRouter();
const symbol = computed(() => route.params.symbol?.toUpperCase());

const loadingState = reactive({
  priceLoaded: false,
  chartDataLoaded: false,
  statsLoaded: false,
  financialsLoaded: false,
  companyInfoLoaded: false
});

const loading = ref(true);
const error = ref('');
const stockData = ref({
  symbol: '',
  company_info: {},
  price_data: {},
  financial_metrics: {},
  historical_data: {}
});

const keyStatsList = computed(() => [
  { label: 'Previous Close', value: stockData.value.price_data.previous_close, formatter: 'price' },
  { label: 'Open', value: stockData.value.price_data.open, formatter: 'price' },
  { label: 'Day High', value: stockData.value.price_data.day_high, formatter: 'price' },
  { label: 'Day Low', value: stockData.value.price_data.day_low, formatter: 'price' },
  { label: '52-Week High', value: stockData.value.price_data["52wk_high"], formatter: 'price' },
  { label: '52-Week Low', value: stockData.value.price_data["52wk_low"], formatter: 'price' },
  { label: 'Volume', value: stockData.value.price_data.volume, formatter: 'volume' },
  { label: 'Market Cap', value: stockData.value.company_info.market_cap, formatter: 'marketCap' }
]);

const financialMetricsList = computed(() => [
  { label: 'P/E Ratio', value: stockData.value.financial_metrics.pe_ratio, formatter: 'pe' },
  { label: 'EPS', value: stockData.value.financial_metrics.eps, formatter: 'eps' },
  { label: 'Dividend Yield', value: stockData.value.financial_metrics.dividend_yield, formatter: 'dividend' },
  { label: 'Dividend Rate', value: stockData.value.financial_metrics.dividend_rate, formatter: 'dividendRate' },
  { label: 'Profit Margin', value: stockData.value.financial_metrics.profit_margin, formatter: 'profitMargin' },
  { label: 'Beta', value: stockData.value.financial_metrics.beta, formatter: 'beta' },
  { label: 'Target Price', value: stockData.value.financial_metrics.target_price, formatter: 'targetPrice' }
]);

const chartCanvas = ref(null);
let chartInstance = null;

const timePeriods = [
  { label: '1D', value: '1d' },
  { label: '1M', value: '1mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' }
];
const currentPeriod = ref('1mo');

const showConfirmModal = ref(false);
const showSaveModal = ref(false);
const showErrorModal = ref(false);
const errorMessage = ref('');
const isSaving = ref(false);

function formatPrice(value) {
  if (value === null || value === undefined) return 'N/A';
  return Number(value).toFixed(2);
}

function formatVolume(value) {
  if (!value) return 'N/A';
  return Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'short' }).format(value);
}

function formatMarketCap(value) {
  if (!value) return 'N/A';
  return Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'short' }).format(value);
}

function formatNumber(value) {
  if (!value) return 'N/A';
  return Intl.NumberFormat('en-US').format(value);
}

function formatRecommendation(rec) {
  if (!rec) return 'N/A';
  const formatted = rec.charAt(0).toUpperCase() + rec.slice(1).toLowerCase();
  return formatted;
}

function formatStatValue(value, formatter) {
  if (value === null || value === undefined) return 'N/A';
  
  switch(formatter) {
    case 'price':
      return '$' + formatPrice(value);
    case 'volume':
      return formatVolume(value);
    case 'marketCap':
      return formatMarketCap(value);
    case 'pe':
      return formatPrice(value);
    case 'eps':
      return '$' + formatPrice(value);
    case 'dividend':
      return formatPrice(value) + '%';
    case 'dividendRate':
      return value ? '$' + formatPrice(value) : 'N/A';
    case 'profitMargin':
      return value ? (value * 100).toFixed(2) + '%' : 'N/A';
    case 'beta':
      return formatPrice(value);
    case 'targetPrice':
      return value ? '$' + formatPrice(value) : 'N/A';
    default:
      return value;
  }
}

function getRecommendationClass() {
  if (!stockData.value.financial_metrics.recommendation) return 'neutral';
  
  const rec = stockData.value.financial_metrics.recommendation.toLowerCase();
  if (rec.includes('buy') || rec === 'strong_buy') return 'positive';
  if (rec.includes('sell') || rec === 'strong_sell') return 'negative';
  return 'neutral';
}

async function fetchStockDetails() {
  if (!symbol.value) {
    error.value = 'Invalid stock symbol.';
    loading.value = false;
    return;
  }
  
  Object.keys(loadingState).forEach(key => {
    loadingState[key] = false;
  });
  
  loading.value = true;
  error.value = '';
  
  try {
    const backendURL = import.meta.env.VITE_BACKEND_URL;
    
    const cacheKey = `stock_details_${symbol.value}`;
    const data = await cacheService.getOrFetch(
      cacheKey,
      async () => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);
        
        const response = await fetch(`${backendURL}/api/stock_details/${symbol.value}`, {
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`Error fetching stock data: ${response.status}`);
        }
        
        const responseData = await response.json();
        
        if (!responseData.success) {
          throw new Error(responseData.error || 'Failed to fetch stock details');
        }
        
        return responseData;
      },
      { ttl: 10 * 60 * 1000 }
    );
    
    stockData.value = data;
    
    const hasPriceData = data.price_data && 
                        (data.price_data.current_price !== undefined && 
                          data.price_data.current_price !== null);
                          
    const hasChartData = data.historical_data && 
                        Object.values(data.historical_data).some(period => 
                          period.data && period.data.length > 0);
                          
    const hasStats = data.price_data && 
                    Object.keys(data.price_data).length > 0;
                    
    const hasFinancials = data.financial_metrics && 
                          Object.keys(data.financial_metrics).length > 0;
                          
    const hasCompanyInfo = data.company_info && 
                          data.company_info.name;
        
    loadingState.priceLoaded = hasPriceData;
    
    setTimeout(() => {
      loadingState.chartDataLoaded = hasChartData;
      if (hasChartData) {
        updateChart();
      }
    }, 100);
    
    setTimeout(() => {
      loadingState.statsLoaded = hasStats;
      loadingState.financialsLoaded = hasFinancials;
    }, 200);
    
    setTimeout(() => {
      loadingState.companyInfoLoaded = hasCompanyInfo;
      loading.value = false;
    }, 300);
    
  } catch (err) {
    console.error('Error:', err);
    error.value = err.message || 'An error occurred loading stock data.';
    loading.value = false;
  }
}

function updateChart() {
  if (!chartCanvas.value || !loadingState.chartDataLoaded) {
    console.warn('Chart canvas not ready');
    return;
  }
  
  if (!stockData.value.historical_data) {
    console.warn('Historical data not available');
    return;
  }

  if (chartInstance) {
    chartInstance.destroy();
  }

  const period = currentPeriod.value;
  
  const historicalData = stockData.value.historical_data[period]?.data || [];

  if (!historicalData || !Array.isArray(historicalData) || historicalData.length < 2) {
    console.warn(`Insufficient data for period: ${period}, points: ${historicalData?.length || 0}`);
    
    let foundAlternate = false;
    for (const p of timePeriods.map(t => t.value)) {
      const altData = stockData.value.historical_data[p]?.data || [];
      if (p !== period && Array.isArray(altData) && altData.length >= 2) {
        currentPeriod.value = p;
        updateChart();
        foundAlternate = true;
        break;
      }
    }
    
    if (!foundAlternate) {
      if (historicalData && historicalData.length === 1) {
        historicalData.push({...historicalData[0], date: new Date().toISOString()});
      } else {
        const ctx = chartCanvas.value.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, chartCanvas.value.width, chartCanvas.value.height);
          ctx.fillStyle = '#666';
          ctx.font = '14px Arial';
          ctx.textAlign = 'center';
          ctx.fillText('No historical data available for this stock', 
                      chartCanvas.value.width / 2, chartCanvas.value.height / 2);
        }
        return;
      }
    }
  }

  const validData = historicalData
    .filter(item => item && item.date && !isNaN(item.close))
    .map(item => ({
      x: new Date(item.date),
      y: Number(item.close)
    }))
    .filter(item => !isNaN(item.x.getTime()) && !isNaN(item.y));
  
  if (validData.length < 2) {
    console.warn('Not enough valid data points after filtering');
    return;
  }

  validData.sort((a, b) => a.x - b.x);
  
  const startPrice = validData[0]?.y;
  const endPrice = validData[validData.length - 1]?.y;
  
  if (!validData || validData.length < 2) {
    console.warn('Not enough data points to render chart');
    return;
  }
  
  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx) {
    console.error('Could not get chart context');
    return;
  }

  const trendColor = startPrice < endPrice ? 'rgba(46, 204, 113, 1)' : 
                    startPrice > endPrice ? 'rgba(231, 76, 60, 1)' : 
                    'rgba(52, 152, 219, 1)';
                    
  const trendColorLight = startPrice < endPrice ? 'rgba(46, 204, 113, 0.2)' : 
                          startPrice > endPrice ? 'rgba(231, 76, 60, 0.2)' : 
                          'rgba(52, 152, 219, 0.2)';

  try {
    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: stockData.value.symbol,
          data: validData,
          borderColor: trendColor,
          backgroundColor: trendColorLight,
          fill: true,
          tension: 0.1,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
        }]
      },
      options: {
        animation: {
          duration: validData.length > 50 ? 0 : 500
        },
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                return `$${context.parsed.y.toFixed(2)}`;
              }
            }
          },
          legend: {
            display: false,
          },
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: period === '1d' ? 'hour' : period === '1mo' ? 'day' : period === '1y' ? 'month' : 'year',
              displayFormats: {
                hour: 'HH:mm',
                day: 'MMM d',
                month: 'MMM yyyy',
                year: 'yyyy'
              }
            },
            ticks: {
              maxRotation: 0,
              autoSkip: true,
              maxTicksLimit: 8,
            }
          },
          y: {
            position: 'right',
            beginAtZero: false,
          },
        }
      }
    });
  } catch (err) {
    console.error('Error creating chart:', err);
    if (ctx) {
      ctx.clearRect(0, 0, chartCanvas.value.width, chartCanvas.value.height);
      ctx.fillStyle = '#666';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Could not render chart: ' + err.message, 
                  chartCanvas.value.width / 2, chartCanvas.value.height / 2);
    }
  }
}

function changeTimePeriod(period) {
  currentPeriod.value = period;
  updateChart();
}

function saveStock() {
  showConfirmModal.value = true;
}

async function confirmSaveStock() {
  if (isSaving.value) return;
  isSaving.value = true;
  
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    const backendURL = import.meta.env.VITE_BACKEND_URL;
    const response = await fetch(`${backendURL}/api/save_stock`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ symbol: symbol.value })
    });

    if (response.status === 409) {
      errorMessage.value = `${symbol.value} is already in your watchlist`;
      showConfirmModal.value = false;
      showErrorModal.value = true;
      return;
    }

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Failed to save stock');
    }

    cacheService.invalidatePattern('user_stocks');
    cacheService.invalidatePattern('profile_stocks');
    
    window.dispatchEvent(new Event('stock-change'));
    
    showConfirmModal.value = false;
    showSaveModal.value = true;
  } catch (err) {
    errorMessage.value = err.message || 'An error occurred';
    showConfirmModal.value = false;
    showErrorModal.value = true;
  } finally {
    isSaving.value = false;
  }
}

watch(() => route.params.symbol, (newSymbol, oldSymbol) => {
  if (newSymbol && newSymbol !== oldSymbol) {
    fetchStockDetails();
  }
}, { immediate: true });

onMounted(() => {
});
</script>

<style scoped>
.stock-header {
  border-left: 4px solid #3498db;
}

.chart-container {
  width: 100%;
  height: 400px;
  position: relative;
}

.chart-loading-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.05);
}

.stat-label {
  color: #777;
  font-size: 0.9rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 500;
}

.recommendation-badge {
  font-weight: 600;
  font-size: 1.2rem;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  display: inline-block;
}

.recommendation-badge.positive {
  background-color: rgba(46, 204, 113, 0.15);
  color: #27ae60;
}

.recommendation-badge.negative {
  background-color: rgba(231, 76, 60, 0.15);
  color: #c0392b;
}

.recommendation-badge.neutral {
  background-color: rgba(241, 196, 15, 0.15);
  color: #f39c12;
}

.time-filter .btn {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.45);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content-custom {
  background: #ffffff;
  color: #000000;
  padding: 20px;
  border-radius: 12px;
  min-width: 300px;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.skeleton-text {
  height: 1rem;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  width: 100%;
}

.skeleton-text.w-75 {
  width: 75%;
}

.skeleton-text.w-50 {
  width: 50%;
}

.skeleton-text.w-25 {
  width: 25%;
}

.skeleton-badge {
  width: 80px;
  height: 40px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>