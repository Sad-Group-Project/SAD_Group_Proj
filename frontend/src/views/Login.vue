<template>
  <div class="d-flex justify-content-center align-items-center min-vh-100">
    <div class="card p-4 shadow" style="max-width: 400px; width: 100%;">
      <h1 class="text-center mb-4">Login to Stock Stalker</h1>
      <button
        @click="loginWithGoogle"
        class="btn btn-light w-100 d-flex align-items-center justify-content-center"
        style="border: 1px solid #dadce0;"
      >
        <img
          src="https://developers.google.com/identity/images/g-logo.png"
          alt="Google Logo"
          style="width: 20px; height: 20px;"
          class="me-2"
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