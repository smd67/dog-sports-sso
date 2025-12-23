import { createRouter, createMemoryHistory } from 'vue-router'
import { createApp } from 'vue'
import LoginScreen from './components/LoginScreen.vue'
import DashBoard from './components/DashBoard.vue'
import CreateAccount from './components/CreateAccount.vue'
import ModifyAccount from './components/ModifyAccount.vue'
import ModifyProfile from './components/ModifyProfile.vue'

import App from './App.vue'

// 1. Define routes: Each route maps a path to a component
const routes = [
  { path: '/dashboard:user_id', name: 'dashboard', component: DashBoard, props: true },
  { path: '/login', name: 'login', component: LoginScreen },
  { path: '/create-account', name: 'create-account', component: CreateAccount },
  { path: '/modify-account:user_id', name: 'modify-account', component: ModifyAccount, props: true },
  { path: '/modify-profile:user_id', name: 'modify-profile', component: ModifyProfile, props: true },
]

// 2. Create the router instance
const router = createRouter({
  history: createMemoryHistory(), // Recommended HTML5 history mode
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')

// Manually push the initial navigation for memory history
router.push('/login');