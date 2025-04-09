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
      >
        <div class="card h-100">
          <div class="card-body d-flex flex-column justify-content-between">
            <div>
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

            <div class="d-grid mt-3">
              <button
                class="btn btn-sm btn-outline-secondary"
                @click.stop="openConfirmModal(result.symbol)"
              >
                Add Stock
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && !error">
      <p class="text-center">No results found.</p>
    </div>

    <div v-if="showConfirmModal" class="modal-backdrop">
      <div class="modal-content-custom">
        <h5>Add {{ pendingSymbol }} to your saved stocks?</h5>
        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" :disabled="isAdding" @click="closeConfirmModal">Cancel</button>
          <button class="btn btn-primary d-flex align-items-center" :disabled="isAdding" @click="confirmAddStock">
            <span v-if="isAdding" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            <span v-if="!isAdding">Yes, Add</span>
            <span v-else>Adding...</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showSavedModal" class="modal-backdrop">
      <div class="modal-content-custom text-center">
        <h5>✅ {{ savedSymbol }} saved successfully!</h5>
        <button class="btn btn-success mt-3" @click="showSavedModal = false">Close</button>
      </div>
    </div>

    <div v-if="showDuplicateModal" class="modal-backdrop">
      <div class="modal-content-custom text-center">
        <h5>⚠️ {{ pendingSymbol }} is already saved.</h5>
        <button class="btn btn-primary mt-3" @click="showDuplicateModal = false">OK</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const searchQuery = ref(route.query.q || '')
const results = ref([])
const loading = ref(false)
const error = ref('')

const showConfirmModal = ref(false)
const showSavedModal = ref(false)
const showDuplicateModal = ref(false)
const pendingSymbol = ref('')
const savedSymbol = ref('')
const isAdding = ref(false)

function openConfirmModal(symbol) {
  pendingSymbol.value = symbol
  showConfirmModal.value = true
}

function closeConfirmModal() {
  pendingSymbol.value = ''
  showConfirmModal.value = false
}

async function confirmAddStock() {
  if (isAdding.value) return
  isAdding.value = true
  await addStock(pendingSymbol.value)
  isAdding.value = false
}

async function addStock(symbol) {
  const token = localStorage.getItem('token')
  if (!token) {
    console.error('No token found')
    window.location.href = '/#/login'
    return
  }

  try {
    const backendURL = import.meta.env.VITE_BACKEND_URL

    const res = await fetch(`${backendURL}/api/save_stock`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ symbol }),
    })

    if (res.status === 409) {
      showConfirmModal.value = false
      showDuplicateModal.value = true
      return
    }

    if (!res.ok) throw new Error('Failed to save stock')

    savedSymbol.value = symbol
    showConfirmModal.value = false
    showSavedModal.value = true
  } catch (err) {
    console.error('Failed to save stock:', err)
    showConfirmModal.value = false
  }
}

function getChartColor(chartData) {
  if (!chartData || chartData.length < 2) return "#3498db"
  const trend = chartData[chartData.length - 1] - chartData[0]
  return trend >= 0 ? "#00C853" : "#D50000"
}

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
})

async function performSearch() {
  loading.value = true
  error.value = ''
  try {
    const backendURL = import.meta.env.VITE_BACKEND_URL
    const response = await fetch(
      `${backendURL}/api/search_stock?search_stock=${searchQuery.value.toUpperCase()}`
    )
    if (!response.ok) throw new Error('Failed to fetch search results')
    const data = await response.json()
    results.value = data.quotes || []
  } catch (err) {
    error.value = err.message || 'An error occurred'
  } finally {
    loading.value = false
  }
}

function cardColClass(index) {
  const total = results.value.length
  const isOdd = total % 2 !== 0
  const isLast = index === total - 1
  return isOdd && isLast ? 'col-12 col-md-8 mx-auto' : 'col-12 col-md-6'
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
</style>
