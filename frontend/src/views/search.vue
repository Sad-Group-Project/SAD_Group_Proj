<template>
  <div class="container mt-3">
    <div class="mb-3">
      <input
        type="text"
        class="form-control"
        placeholder="Search Stocks..."
        v-model="searchQuery"
        @keyup.enter="performSearch"
      />
    </div>

    <h2 class="text-center">Search Results for "{{ searchQuery }}"</h2>

    <div v-if="loading" class="text-center my-4">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div class="row g-3 align-items-stretch mt-3" v-if="results.length">
      <div
        v-for="(result, index) in results"
        :key="index"
        :class="cardColClass(index)"
        @click="handleClick(result)"
      >
        <div class="card h-100">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between">
              <div class="fw-bold fs-5">
                {{ result.shortName || result.longName }}
              </div>

              <div class="sparkline-container mx-2">
                <ApexChart
                  v-if="result.chartData && result.chartData.length > 1"
                  :key="result.symbol"
                  type="line"
                  :options="chartOptions(result.chartData)"
                  :series="[{ data: result.chartData }]"
                  width="80"
                  height="40"
                />
              </div>

              <div
                class="fs-6"
                :class="{
                  'text-success': result.regularMarketChangePercent >= 0,
                  'text-danger': result.regularMarketChangePercent < 0
                }"
              >
                {{ (result.regularMarketChangePercent || 0).toFixed(2) }}%
              </div>
            </div>

            <div class="d-flex align-items-center justify-content-between mt-2">
              <div class="text-muted">
                {{ result.symbol }}
              </div>
              <div class="fw-bold">
                {{ (result.regularMarketPrice || 0).toFixed(2) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No results from endpoint -->
    <div v-else-if="!loading && !error">
      <p class="text-center">No results found.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ApexChart from 'vue3-apexcharts'

const route = useRoute()
const searchQuery = ref(route.query.q || '')
const results = ref([])
const loading = ref(false)
const error = ref('')

const getChartColor = (chartData) => {
  if (!chartData || chartData.length < 2) return "#3498db";

  const trend = chartData[chartData.length - 1] - chartData[0];
  return trend >= 0 ? "#00C853" : "#D50000";
};

const chartOptions = (chartData) => ({
  chart: {
    type: 'line',
    sparkline: { enabled: true }
  },
  stroke: {
    curve: 'smooth',
    width: 3.5,
    colors: [getChartColor(chartData)]
  },
  fill: {
    type: "gradient",
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.8,
      opacityTo: 0.3,
      stops: [0, 100]
    }
  },
  tooltip: { enabled: false },
  xaxis: { labels: { show: false }, type: 'numeric' },
  yaxis: { labels: { show: false } },
  colors: [getChartColor(chartData)]
});


async function performSearch() {
  loading.value = true
  error.value = ''
  try {
    const backendURL = import.meta.env.VITE_BACKEND_URL
    const response = await fetch(
      `${backendURL}/api/search_stock?search_stock=${searchQuery.value}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch search results')
    }
    const data = await response.json()
    console.log("API RESPONSE", data)
    results.value = data.quotes || []
  } catch (err) {
    error.value = err.message || 'An error occurred'
  } finally {
    loading.value = false
  }
}

function handleClick(result) {
  console.log('Clicked stock:', result.symbol)
}

function cardColClass(index) {
  const total = results.value.length
  const isOdd = total % 2 !== 0
  const isLast = index === total - 1

  if (isOdd && isLast) {
    return 'col-12 col-md-8 mx-auto'
  } else {
    return 'col-12 col-md-6'
  }
}

onMounted(() => {
  if (searchQuery.value) {
    performSearch()
  }
})
</script>

<style scoped>
.card {
  cursor: pointer;
  transition: background-color 0.3s ease, box-shadow 0.3s ease, filter 0.3s ease;
}

.card:hover {
  background-color: #f8f9fa;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  filter: brightness(0.95);
}

.sparkline-container {
  width: 60px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
