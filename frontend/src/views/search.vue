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
  
      <h2>Search Results for "{{ searchQuery }}"</h2>
  
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
            <div class="card-body d-flex flex-column justify-content-between">
              <h5 class="card-title">
                {{ result.longname || result.shortname }}
              </h5>
              <p class="card-subtitle text-muted mb-2">Symbol: {{ result.symbol }}</p>
              <p class="card-text">
                Industry: {{ result.industry }} <br />
                Exchange: {{ result.exchDisp }}
              </p>
            </div>
          </div>
        </div>
      </div>
  
      <div v-else-if="!loading && !error">
        <p>No results found.</p>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  
  const route = useRoute()
  const searchQuery = ref(route.query.query || '')
  const results = ref([])
  const loading = ref(false)
  const error = ref('')
  
  async function performSearch() {
    loading.value = true
    error.value = ''
    try {
      const backendURL = import.meta.env.VITE_BACKEND_URL
      const response = await fetch(
        `${backendURL}/api/search_stock?search_stock=${encodeURIComponent(searchQuery.value)}`
      )
      if (!response.ok) {
        throw new Error('Failed to fetch search results')
      }
      const data = await response.json()
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
      return 'col-12'
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
  </style>
  
  
  
  