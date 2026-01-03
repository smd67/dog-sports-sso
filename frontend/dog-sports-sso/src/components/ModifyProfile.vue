<template>
  <h2>Change Password</h2>
  <form @submit.prevent="updateVenueUserInfo">
      <input type="text" v-model="username" :readonly="true" placeholder="Username" class="form-object" />      
      <select v-model="venue" @change="handleChange">
        <option v-for="item in venues" :key="item" :value="item">
          {{ item }}
        </option>
      </select>
      <input type="text" v-model="venueUsername" placeholder="Venue Username" class="form-object" />
      <input type="password" v-model="venuePassword" placeholder="Venue Password" class="form-object"/>
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
  const username = ref(null);
  const venues = ref([]);
  const venue = ref(null);
  const venueUsername = ref(null);
  const venuePassword = ref(null);
  const userVenues = ref([]);
  const error = ref(null);
  const loading = ref(true);
  const router = useRouter();

  onMounted(async () => {
    console.log('IN onMounted username=' + username.value + '; user_id=' + props.user_id);
    username.value = props.user_id;
    fetchUserVenues();
  });

  const fetchUserVenues = async () => {
    const apiUrl = 'http://127.0.0.1:8001/get-user-venues/';
    const config = {
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    const requestBody = {
        user_id: username.value,
    }
    try {
        const response = await axios.post(apiUrl, requestBody, config);
        userVenues.value = response.data;
        venue.value = userVenues.value[0].venue;
        venueUsername.value = userVenues.value[0].venue_user_id;
        venuePassword.value = userVenues.value[0].venue_password;
        venues.value = userVenues.value.map(row => row.venue);
        console.log("venue=" + venue.value)
        loading.value = false;
    } catch (e) {
        loading.value = false;
        venueUsername.value = null;
        venuePassword.value = null;
    }
  };

  const handleChange = (event) => {
    const newValue = event.target.value;
    console.log('Venue changed to:', newValue + "; event=" + JSON.stringify(event.target));
    const result = userVenues.value.find(item => item.venue == newValue)
    // Perform your desired callback logic here
    venue.value = newValue;
    venuePassword.value = result.venue_password;
    venueUsername.value = result.venue_user_id;
  }

  const updateVenueUserInfo = async () => {
    const apiUrl = 'http://127.0.0.1:8001/update-venue-user-info/';
    const token = localStorage.getItem('access_token');
    const config = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    };
    
    const requestBody = {
        user_id: username.value,
        venue: venue.value,
        venue_user_id: venueUsername.value,
        venue_password: venuePassword.value
    };
    try {
        const response = await axios.post(apiUrl, requestBody, config);
        if(response.data == false) {
          error.value = 'Failed to update user venue info';
        }
        loading.value = false;
        router.push({name: 'dashboard', params: {user_id: username.value}}); // Redirect to a protected route
    } catch (e) {
        loading.value = false;
        error.value = 'Error failed to update user venue info:' + e;
        console.error('Error failed to update user venue info:', e);
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