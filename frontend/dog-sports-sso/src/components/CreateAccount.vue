<template>
  <div class="registration-form">
    <h2>Create New Account</h2>
    <form @submit.prevent="handleRegistration">
      <div>
        <label for="username">Username:</label>
        <input id="username" v-model="username" type="text" required />
      </div>
      <div>
        <label for="password">Password:</label>
        <input id="password" v-model="password" type="password" required />
      </div>
      <button type="submit">Sign Up</button>
    </form>
  </div>
  <div class="divider"><p></p></div>
  <div v-if="error" class="error-banner" style="color: red;">
    {{ error }}
  </div>
</template>

<script>
import axios from 'axios';
import '@fontsource/kranky';
export default {
  data() {
    return {
      username: '',
      password: '',
      error: null
    };
  },
  methods: {
    async handleRegistration() {
        // Logic to send data to your backend API or Auth service (e.g., Firebase, Auth0)
        console.log('IN handleRegistration username=' + this.username);
        try {
            const response = await axios.post('http://localhost:8001/create-account', new URLSearchParams({
            username: this.username,
            password: this.password,
            }), {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });
            console.log('OUT handleRegistration results=' + response.data);
            this.$router.push({name: 'login'}); // Redirect to a protected route
        } catch (err) {
            this.error = 'Account creation failed. ' + err;
            console.error(err);
        }
    },
  },
};
</script>

<style scoped>
  .divider {
    margin-top: 50px; /* Pushes this element and everything after it to the far right */
  }
</style>