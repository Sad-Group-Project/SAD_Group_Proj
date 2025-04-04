<template>
  <div class="d-flex justify-content-center align-items-center min-vh-100 login-container">
    <div class="card p-4 shadow-lg login-card">
      <h1 class="text-center mb-4 app-title">Login to Stock Stalker</h1>
      <button class="btn btn-light w-100 d-flex align-items-center justify-content-center" @click="loginWithGoogle">
        <img
          src="https://developers.google.com/identity/images/g-logo.png"
          alt="Google Logo"
          class="me-2"
          style="width: 20px; height: 20px"
        />
        <span>Sign in with Google</span>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    loginWithGoogle() {
      const backendUrl = import.meta.env.VITE_BACKEND_URL;
      window.location.href = `${backendUrl}/api/google/login`;
    }
  }
};
</script>

<style scoped>
.app-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  color: var(--text-color);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}
.login-container {
  background-color: var(--bg-color);
  color: var(--text-color);
  padding: 2rem;
}
.login-card {
  border-radius: 10px;
  max-width: 400px;
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
