<template>
  <h2>Change Password</h2>
  <form @submit.prevent="handleChangePassword">
      <input type="text" v-model="username" placeholder="Username" class="form-object" />
      <input type="password" v-model="password" placeholder="New Password" class="form-object"/>
      <input type="password" v-model="confirmPassword" placeholder="Confirm Password" class="form-object"/>
      <button type="submit">Submit</button>
  </form>
  <div class="divider"><p></p></div>
  <div v-if="error" class="error-banner" style="color: red;">
    {{ error }}
  </div>
</template>

<script setup>
  import { ref, onMounted, defineProps } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';
  import '@fontsource/kranky';

  const props = defineProps({
      user_id: {
          type: String,
          default: "",
      },
  });
  const router = useRouter();
  const username = ref(null);
  const password = ref(null);
  const confirmPassword = ref(null);
  const error = ref(null);

  onMounted(async () => {
    console.log('IN mounted username=' + username.value + '; user_id=' + props.user_id);
    username.value = props.user_id;
  });

  const handleChangePassword = async () => {
    console.log('IN handleChangePassword username=' + username.value);
    if(password.value != confirmPassword.value){
      error.value = 'Passwords must match';
    } else {
      // Logic to send data to your backend API or Auth service (e.g., Firebase, Auth0)
      try {
        const response = await axios.post('http://localhost:8001/change-password', new URLSearchParams(
          {
            username: username.value,
            password: password.value,
          }), {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          });
          console.log('OUT handleChangePassword results=' + response.data);
          localStorage.setItem('access_token', null);
          router.push({name: 'login'}); // Redirect to a protected route
        } catch (err) {
            error.value = 'Password change failed. ' + err;
            console.error(err);
        }
      }
  };
</script>

<style scoped>
.divider {
  margin-top: 50px; /* Pushes this element and everything after it to the far right */
}
.form-object {
    margin-right: 10px; /* Pushes this element and everything after it to the far right */
  }

</style>