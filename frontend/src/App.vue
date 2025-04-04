<template>
  <div class="page-container">
    <nav v-if="!isLoginPage" class="navbar navbar-expand-lg navbar-custom">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">📈 Stock Stalker</router-link>

        <button 
          class="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav" 
          aria-controls="navbarNav" 
          aria-expanded="false" 
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <!-- <li class="nav-item">
              <router-link class="nav-link" to="/saved-stocks">💾 Saved Stocks</router-link>
            </li> -->
            <li class="nav-item">
              <router-link class="nav-link" to="/popular">🔥 Popular Stocks</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/profile">👤 Profile</router-link>
            </li>
          </ul>

          <button class="btn btn-custom" @click="signOut">🚪 Sign Out</button>
        </div>
      </div>
    </nav>

    <div class="content">
      <router-view/>
    </div>

    <footer v-if="!isLoginPage" class="footer">
      <p>STOCK STALKER © 2025</p>
    </footer>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

export default{
  setup(){
    
    const loginRouter = useRouter();
    const router = useRoute();
    const signOut = async () => {
      try {
        const backendUrl = import.meta.env.VITE_BACKEND_URL;
        const respone = await fetch(`${backendUrl}/api/google/logout`, 
        {
          method: "POST",
          credentials: "include",
        });
        if(respone.ok){
          localStorage.removeItem("token");
          loginRouter.push("/login");
          window.location.reload();
        }
        else{
          console.error("Logout failed");
        }
      }
      catch(error){
        console.error("Error logging out!", error)
      }
    };

    const isLoginPage = computed(() => router.path === "/login");

    return{
      signOut,
      isLoginPage,
    }
  },
}
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content {
  flex: 1;
}

.navbar-custom {
  background-color: #2c3e50;
  padding: 10px 20px;
  border-bottom: 3px solid #e74c3c;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  color: #ecf0f1 !important;
  font-weight: bold;
  font-size: 24px;
}

.navbar-toggler {
  border-color: #ecf0f1;
}

.navbar-toggler-icon {
  filter: invert(1);
}

.navbar-nav .nav-link {
  color: #ecf0f1 !important;
  font-size: 18px;
  margin-right: 15px;
  transition: color 0.3s;
}

.navbar-nav .nav-link:hover {
  color: #e74c3c !important;
}

.btn-custom {
  background-color: transparent;
  border: 2px solid #ecf0f1;
  color: #ecf0f1;
  padding: 6px 20px;
  font-size: 16px;
  border-radius: 20px;
  transition: background-color 0.3s, color 0.3s;
}

.btn-custom:hover {
  background-color: #ecf0f1;
  color: #2c3e50;
}

.footer {
  background-color: #2c3e50;
  color: #ecf0f1;
  text-align: center;
  padding: 5px 0;
  width: 100%;
  margin-top: auto;
  border-top: 2px solid #e74c3c;
}
</style>