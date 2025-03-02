<template>
  <div class="container mt-3">
    <div class="mb-3">
      <input
        type="text"
        class="form-control"
        placeholder="Search Stocks..."
        v-model="searchQuery"
      />
    </div>

    <div class="row">
      <div class="col-md-6">
        <h2>Popular Stocks</h2>
        <div class="row row-cols-1 row-cols-md-2 g-3 mt-3 align-items-stretch">
          <div
            class="col"
            v-for="(stock, index) in popularStocks"
            :key="index"
          >
            <div class="card h-100">
              <div class="card-body d-flex flex-column justify-content-between">
                <h5 class="card-title">{{ stock.name }}</h5>
                <div class="chart-container">
                  <canvas :id="'popularChart' + index"></canvas>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <h2>Tracked Stocks</h2>

        <template v-if="trackedStocks && trackedStocks.length">
          <div class="row row-cols-1 row-cols-md-2 g-3 mt-3 align-items-stretch">
            <div
              class="col"
              v-for="(stock, index) in trackedStocks"
              :key="index"
            >
              <div class="card h-100">
                <div class="card-body d-flex flex-column justify-content-between">
                  <h5 class="card-title">{{ stock.name }}</h5>
                  <div class="chart-container">
                    <canvas :id="'trackedChart' + index"></canvas>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <div
            class="d-flex flex-column align-items-center justify-content-center mt-3"
            style="min-height: 300px;"
          >
            <p class="text-muted text-center mb-2">
              You haven't added any stocks yet.
            </p>
            <button class="btn btn-primary">
              Add some Now!
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Trending Stock News -->
    <div class="mt-4">
      <h2>Trending Stock News</h2>
      <div class="card my-3">
        <div class="card-body">
          <p class="text-muted mb-0">News Placeholder</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const searchQuery = ref('')
const popularStocks = ref([])
const trackedStocks = ref([
  { name: 'Microsoft Corporation (MSFT)' },
  { name: 'Netflix, Inc. (NFLX)' },
  { name: 'Meta Platforms, Inc. (META)' },
  { name: 'NVIDIA Corporation (NVDA)' }
])

let popularCharts = []
let trackedCharts = []

onMounted(async () => {
  try {
    const backendURL = import.meta.env.VITE_BACKEND_URL
    const popularResponse = await fetch(`${backendURL}/api/popular_stocks`)
    popularStocks.value = await popularResponse.json()

    // const trackedResponse = await fetch(`${backendURL}/api/tracked_stocks`)
    // trackedStocks.value = await trackedResponse.json()

    await nextTick()
    createPopularCharts()
    createTrackedCharts()
  } catch (error) {
    console.error('Error fetching data:', error)
  }
})

function createPopularCharts() {
  if (!popularStocks.value.length) return
  popularStocks.value.forEach((stock, index) => {
    const ctx = document.getElementById(`popularChart${index}`)
    if (!ctx) return

    const data = {
      labels: stock.chartData.labels,
      datasets: [
        {
          label: stock.name,
          data: stock.chartData.values,
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
          fill: true
        }
      ]
    }

    const config = {
      type: 'line',
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true }
        }
      }
    }

    if (popularCharts[index]) {
      popularCharts[index].destroy()
    }
    popularCharts[index] = new Chart(ctx, config)
  })
}

function createTrackedCharts() {
  trackedStocks.value.forEach((stock, index) => {
    const ctx = document.getElementById(`trackedChart${index}`)
    if (!ctx) return

    const data = {
      labels: ['2025-02-24', '2025-02-25', '2025-02-26', '2025-02-27', '2025-02-28'],
      datasets: [
        {
          label: stock.name,
          data: [100, 110, 115, 120, 130],
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1,
          fill: true
        }
      ]
    }

    const config = {
      type: 'line',
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true }
        }
      }
    }

    if (trackedCharts[index]) {
      trackedCharts[index].destroy()
    }
    trackedCharts[index] = new Chart(ctx, config)
  })
}
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 250px;
  position: relative;
}

.row.align-items-stretch > .col > .card {
  height: 100%;
}

.card-body.d-flex {
  align-items: flex-start;
}
</style>
