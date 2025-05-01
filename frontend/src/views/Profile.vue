<template>
  <div class="container py-4">
    <h1 class="text-center mb-4 app-title">👤 Profile</h1>

    <div class="mb-4 text-center">
      <button class="btn btn-warning" @click="toggleTheme">Switch Theme</button>
    </div>

    <div class="d-flex flex-wrap gap-4 justify-content-center">
      <div class="input-box">
        <h5>Discord Stock Alert</h5>
        <label>Stock Symbol</label>
        <input v-model="inputStockSymbol" class="form-control mb-2" placeholder="e.g., TSLA" />
        <label>Discord Username</label>
        <input v-model="discordUsername" class="form-control mb-2" placeholder="e.g., user#1234" />
        <label>Price Bought</label>
        <input v-model="priceBought" class="form-control mb-2" type="number" />
        <label>Selling Price</label>
        <input v-model="sellingPrice" class="form-control mb-2" type="number" />
        <label>Share Amount</label>
        <input v-model="shareAmount" class="form-control mb-2" type="number" />
        <button class="btn btn-success mt-2" @click="sendDataToBackend">Send</button>
      </div>

      <div class="profile-box text-center">
        <img
          v-if="userProfile.profile_picture"
          :src="userProfile.profile_picture"
          alt="Profile Picture"
          class="profile-img mb-3"
        />
        <h5>{{ userProfile.username }}</h5>
        <p>{{ userProfile.email }}</p>
        <p><small>Joined: {{ formattedDate }}</small></p>
      </div>

      <div class="stocks-box">
        <h5 class="text-center mb-3">📊 Saved Stocks</h5>
        <div v-if="userStocks.length" class="stocks-list-card">
          <div v-for="stock in userStocks" :key="stock.symbol" class="stock-card">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="mb-1">
                  {{ stock.symbol }}
                  <small class="text-muted">({{ stock.company_name }})</small>
                </h6>
                <p class="mb-1 text-muted">
                  Saved at <strong>${{ stock.price_at_save.toFixed(2) }}</strong><br />
                  on {{ new Date(stock.date_saved).toLocaleDateString() }}
                </p>
                <p v-if="stock.current_info?.price" class="mb-1 text-muted">
                  Current Price: <strong>${{ stock.current_info.price.toFixed(2) }}</strong>
                </p>
              </div>
              <button class="btn btn-outline-danger btn-sm" @click="confirmDelete(stock.symbol)">
                <font-awesome-icon icon="fa-solid fa-trash" />
              </button>
            </div>
          </div>
        </div>
        <div v-else class="text-center mt-3">
          <p>No stocks saved yet!</p>
          <button class="btn btn-outline-primary" @click="goToPopular">📈 Add Stocks!</button>
        </div>
      </div>
    </div>

    <div v-if="showConfirmModal" class="modal-backdrop">
      <div class="modal-content-custom">
        <h5>Are you sure you want to delete {{ stockToDelete }}?</h5>
        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" :disabled="isDeleting" @click="showConfirmModal = false">Cancel</button>
          <button class="btn btn-danger d-flex align-items-center" :disabled="isDeleting" @click="deleteStock">
            <span v-if="isDeleting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            <span v-if="!isDeleting">Yes, Delete</span>
            <span v-else>Deleting...</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showSuccessModal" class="modal-backdrop">
      <div class="modal-content-custom text-center">
        <h5>✅ {{ stockToDelete }} was successfully deleted!</h5>
        <button class="btn btn-success mt-3" @click="showSuccessModal = false">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { cacheService } from '../utils/cacheService';

const router = useRouter();

const inputStockSymbol = ref('');
const discordUsername = ref('');
const priceBought = ref(0);
const sellingPrice = ref(0);
const shareAmount = ref(0);

const userProfile = ref({
  username: '',
  email: '',
  profile_picture: '',
  created_at: ''
});

const userStocks = ref<Array<any>>([]);

const stockToDelete = ref('');
const showConfirmModal = ref(false);
const showSuccessModal = ref(false);
const isDeleting = ref(false);

const backendURL = import.meta.env.VITE_BACKEND_URL;

function confirmDelete(symbol: string) {
  stockToDelete.value = symbol;
  showConfirmModal.value = true;
}

async function deleteStock() {
  const token = localStorage.getItem('token');
  if (!token || !stockToDelete.value) return;

  isDeleting.value = true;

  try {
    const res = await fetch(`${backendURL}/api/delete_stock?symbol=${stockToDelete.value}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await res.json();
    if (res.ok) {
      cacheService.invalidatePattern('user_stocks');
      cacheService.invalidatePattern('profile_stocks');
      
      userStocks.value = userStocks.value.filter(stock => stock.symbol !== stockToDelete.value);
      
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('stock-change', { 
          detail: { action: 'delete', symbol: stockToDelete.value } 
        }));
      }, 100);
      
      showConfirmModal.value = false;
      showSuccessModal.value = true;
    } else {
      console.error('Delete failed:', data.error || await res.text());
    }
  } catch (err) {
    console.error('Error deleting stock:', err);
  } finally {
    isDeleting.value = false;
  }
}

async function fetchUserProfile() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const cacheKey = `user_profile_${token.slice(-10)}`;
    
    const data = await cacheService.getOrFetch(
      cacheKey,
      async () => {
        const res = await fetch(`${backendURL}/api/user_profile`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error('Failed to fetch profile data');
        }
        
        return await res.json();
      },
      { ttl: 15 * 60 * 1000 }
    );
    
    userProfile.value = data;
  } catch (err) {
    console.error('Error fetching profile:', err);
  }
}

async function fetchUserStocks() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const cacheKey = `profile_stocks_${token.slice(-10)}`;
    
    const data = await cacheService.getOrFetch(
      cacheKey,
      async () => {
        const res = await fetch(`${backendURL}/api/user_stocks`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error('Failed to fetch stocks data');
        }
        
        return await res.json();
      },
      { ttl: 10 * 60 * 1000 }
    );
    
    if (data.success) {
      userStocks.value = data.saved_stocks;
    } else {
      console.error('Failed to fetch stocks:', data.error);
    }
  } catch (err) {
    console.error('Error fetching stocks:', err);
  }
}

function sendDataToBackend() {
  alert(`Discord alert set for ${inputStockSymbol.value} at $${sellingPrice.value}`);
  console.log({
    symbol: inputStockSymbol.value,
    discord: discordUsername.value,
    boughtAt: priceBought.value,
    sellAt: sellingPrice.value,
    shares: shareAmount.value,
  });
}

function goToPopular() {
  router.push('/popular');
}

const formattedDate = computed(() => {
  return userProfile.value.created_at
    ? new Date(userProfile.value.created_at).toLocaleDateString()
    : '';
});

const themes = {
  'light': { bg: '#ffffff', text: '#000000' },
  'dark': { bg: '#1e1e1e', text: '#f5f5f5' },
  'high-contrast': { bg: '#000000', text: '#ffff00' },
  'blue': { bg: '#d0e7ff', text: '#003366' },
  'green': { bg: '#e8f5e9', text: '#1b5e20' },
  'warm': { bg: '#fff3e0', text: '#bf360c' },
};

const themeKeys = Object.keys(themes) as Array<keyof typeof themes>;
const currentThemeIndex = ref(0);

function applyThemeStyles() {
  const theme = themes[themeKeys[currentThemeIndex.value]];
  document.documentElement.style.setProperty('--bg-color', theme.bg);
  document.documentElement.style.setProperty('--text-color', theme.text);
  document.body.style.backgroundColor = theme.bg;
  document.body.style.color = theme.text;
}

function toggleTheme() {
  currentThemeIndex.value = (currentThemeIndex.value + 1) % themeKeys.length;
  applyThemeStyles();
}

onMounted(() => {
  applyThemeStyles();
  fetchUserProfile();
  fetchUserStocks();
});
</script>

<style scoped>
.app-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  color: var(--text-color);
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.input-box, .profile-box, .stocks-box {
  min-width: 250px;
  max-width: 300px;
  background: var(--bg-color);
  color: var(--text-color);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.06);
}

.profile-img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 50%;
}

.stocks-list-card {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stock-card {
  background: #ffffff;
  color: #000000;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: 0.2s ease;
}

.stock-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content-custom {
  background: #ffffff;
  color: #000000;
  padding: 20px;
  border-radius: 12px;
  min-width: 300px;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
</style>
