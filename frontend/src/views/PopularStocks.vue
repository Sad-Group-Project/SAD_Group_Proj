<template>
  <div>
    <h1 class="text-center my-4 app-title">🔥 Popular Stocks</h1>

    <div class="search-bar text-center mb-4">
      <input v-model="stockSymbol" class="form-control d-inline-block w-auto me-2" placeholder="Enter stock symbol" />
      <button class="btn btn-primary" @click="addStock">Add Stock</button>
    </div>

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
            <td>{{ stock.symbol }}</td>
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const stockSymbol = ref('');
const stockDataList = ref<any[]>([]);

async function addStock() {
  if (!stockSymbol.value) return;

  const token = localStorage.getItem('token');
  if (!token) {
    console.error('No token found. Redirecting to login.');
    window.location.href = '/#/login';
    return;
  }

  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/stocks?symbol=${stockSymbol.value}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const stockData = await res.json();
    stockDataList.value.push(stockData);

    await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/save_stock`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ symbol: stockSymbol.value }),
    });

    stockSymbol.value = '';
  } catch (error) {
    console.error('Failed to add stock:', error);
  }
}
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
</style>
