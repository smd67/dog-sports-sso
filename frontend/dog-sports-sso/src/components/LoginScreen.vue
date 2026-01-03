<template>
  <div>
    <div>
      <CurveText :width="300" :height="80" :r="50" style="padding-right: 50px; color: limegreen; font-family: 'Kranky';font-size: 32px;">
        Dog Sports SSO
      </CurveText>
    </div>
    <img style="padding-left: 80px;" alt="Dog Sports SSO logo" src="../assets/dog-sports-sso-logo.png">
    <form @submit.prevent="login">
        <input type="text" v-model="username" placeholder="Username" class="form-object" />
        <input type="password" v-model="password" placeholder="Password" class="form-object"/>
        <button type="submit">Login</button>
    </form>
    <div class="divider"></div>
    <router-link to="/create-account" style="color: limegreen;">Or Create Account</router-link>
    <p v-if="error">{{ error }}</p>
  </div>
</template>


<script>
import axios from 'axios';
import '@fontsource/kranky';
import { CurveText } from '@inotom/vue-curve-text';

export default {
  components: {
    CurveText
  },
  data() {
    return {
      username: '',
      password: '',
      error: null,
    };
  },
  methods: {
    async login() {
      try {
        const response = await axios.post('http://localhost:8001/token', new URLSearchParams({
          username: this.username,
          password: this.password,
        }), {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
        localStorage.setItem('access_token', response.data.access_token);
        this.$router.push({name: 'dashboard', params: {user_id: this.username}}); // Redirect to a protected route
      } catch (err) {
        this.error = 'Login failed. Please check your credentials.';
        console.error(err);
      }
    },
  },
};
</script>

<style scoped>
  :global(body) {
    background-color: #fff4e6;
  }
  .divider {
    margin-top: 50px; /* Pushes this element and everything after it to the far right */
  }
  .form-object {
    margin-right: 10px; /* Pushes this element and everything after it to the far right */
  }
</style>