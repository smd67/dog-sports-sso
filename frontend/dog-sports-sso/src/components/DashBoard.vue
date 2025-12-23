<template>
    <div class="settings-menu-container">
      <div class="settings-menu-right">
        <button @click="toggleMenu" class="settings-button" aria-label="Settings menu">
          <img src="../assets/settings.jpg" alt="Description of action" class="button-image" />
            <!-- You can use a settings icon here, e.g., a gear symbol (⚙) or an SVG -->
            <!-- ⚙ Settings -->
        </button>

        <div v-if="isOpen" class="settings-dropdown">
            <ul>
            <li @click="selectOption('Profile')">Profile</li>
            <li @click="selectOption('Account')">Account</li>
            <li @click="selectOption('Logout')">Logout</li>
            </ul>
        </div>
      </div>
    </div>
    <h1 style="color: limegreen; font-family: 'Kranky';font-size: 28px;"><b>Dog Sports SSO Dashboard</b></h1>
    <div class="my-division">
      <div class="container">
        <img src="../assets/cpe_venue.png" alt="Description" class="inline-img" />
      </div>
      <div class="spinner" v-if="loading"></div>
      <div v-else-if="!error">
        <table>
            <thead>
            <tr>
                <th>Handler</th>
                <th>Member ID</th>
                <th>Phone #</th>
                <th>Email</th>
                <th>Address</th>
                <!-- Add more table headers as needed -->
            </tr>
            </thead>
            <tbody>
            <tr>
                <td>{{ tableData.handler }}</td>
                <td>{{ tableData.handler_member_id }}</td>
                <td>{{ tableData.phone }}</td>
                <td>{{ tableData.email }}</td>
                <td>{{ tableData.address }}</td>
            </tr>
            </tbody>
        </table>
        <p></p>
        <table>
            <thead>
            <tr>
                <th>Call Name</th>
                <th>Dog Member ID</th>
                <th>Breed</th>
                <th>Jump Height</th>
                <th>Date of Birth</th>
                <!-- Add more table headers as needed -->
            </tr>
            </thead>
            <tbody>
            <tr v-for="item in tableData.dog_info" :key="item.dog_member_id">
                 <td>{{ item.call_name }}</td>
                 <td>{{ item.dog_member_id }}</td>
                 <td>{{ item.breed }}</td>
                 <td>{{ item.jump_height }}</td>
                 <td>{{ item.dob }}</td>
            </tr>
            </tbody>
        </table>
      </div>
      <div v-else class="error-banner" style="color: red;">
          {{ error }}
      </div>
    </div>
  </template>

<script setup>
    import axios from 'axios';
    import { ref, onMounted, onUnmounted, defineProps } from 'vue';
    import { useRouter } from 'vue-router';
    import '@fontsource/kranky';
    const router = useRouter();
    const tableData = ref(null);
    const loading = ref(true);
    const error = ref(null);
    const isOpen = ref(false);
    const props = defineProps({
    user_id: {
        type: String,
        default: "",
    },
    });
    console.log("props user_id=" + props.user_id);

    const toggleMenu = () => {
        isOpen.value = !isOpen.value;
    };

    const selectOption = (option) => {
        console.log('Selected:' + option + '; user_id=' + props.user_id);
        isOpen.value = false; // Close menu after selection
        // Emit event to parent component if needed, e.g., emit('select', option)

        if(option === "Logout"){
          localStorage.setItem('access_token', null);
          router.push({name: 'login'}); 
        } else if (option === "Account") {
          router.push({name: 'modify-account', params: {user_id: props.user_id}}); 
        } else if (option === "Profile") {
          router.push({name: 'modify-profile', params: {user_id: props.user_id}}); 
        }
    };

    // Close the menu when clicking outside
    const handleClickOutside = (event) => {
        if (!event.target.closest('.settings-menu-container')) {
            isOpen.value = false;
        }
    };

    onMounted(() => {
      console.log("IN onMounted user_id=" + props.user_id);
      document.addEventListener('click', handleClickOutside);
      fetchTableData();
    });

    onUnmounted(() => {
        document.removeEventListener('click', handleClickOutside);
    });

    const fetchTableData = async () => {
        const apiUrl = 'http://127.0.0.1:8001/get-cpe-info/';
        const token = localStorage.getItem('access_token');
        console.log("token=" + token);
        const config = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };
        const requestBody = {
            user_id: props.user_id
        }
        try {
            const response = await axios.post(apiUrl, requestBody, config);
            tableData.value = response.data;
            loading.value = false;
        } catch (e) {
            loading.value = false;
            error.value = 'Error fetching data:' + e;
            console.error('Error fetching data:', e);
        }
    };
  </script>
  <style scoped>
  .settings-menu-right {
    margin-left: auto; /* Pushes this element and everything after it to the far right */
  }
  /* Add basic styling for the table if needed */
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  th {
    background-color: #f2f2f2;
  }
  .my-division {
    padding-top: 0px;
    padding-bottom: 0px;
  }
  .spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-left-color: #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
  .grid-container {
    display: grid;
    grid-template-columns: repeat(5, 1fr); /* 5 columns, equal width */
    grid-template-rows: repeat(1, auto); /* 1 rows, height determined by content */
    gap: 1px; /* Adjust as needed for spacing */
  }
  .grid-item {  
    /* Optional: Add styling for individual grid items */
    display: inline-block;
    border: 1px solid #ccc;
    padding: 1px;
  }

.settings-menu-container {
  position: absolute;
  top: 0; /* Aligns to the top edge of the parent */
  right: 0; /* Aligns to the right edge of the parent */
  display: inline-block;
}

.settings-button {
  background-color: lightgray; /* Example styling */
  color: white;
  padding: 0.33px .5px;
  border: none;
  cursor: pointer;
}

.settings-dropdown {
  position: absolute;
  right: 0;
  background-color: #f9f9f9;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
  z-index: 1;
}

.settings-dropdown ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.settings-dropdown li {
  padding: 12px 16px;
  cursor: pointer;
}

.settings-dropdown li:hover {
  background-color: #ddd;
}

.button-image {
  width: 24px; /* Set a specific width */
  height: auto; /* Maintain aspect ratio */
}
  </style>