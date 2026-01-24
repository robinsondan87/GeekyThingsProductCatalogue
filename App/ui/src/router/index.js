import { createRouter, createWebHistory } from 'vue-router'
import IndexView from '../views/IndexView.vue'
import AddView from '../views/AddView.vue'
import ProductView from '../views/ProductView.vue'
import LoginView from '../views/LoginView.vue'
import StockView from '../views/StockView.vue'
import EventsView from '../views/EventsView.vue'

const routes = [
  { path: '/', name: 'home', component: IndexView },
  { path: '/stock', name: 'stock', component: StockView },
  { path: '/events', name: 'events', component: EventsView },
  { path: '/add', name: 'add', component: AddView },
  { path: '/product', name: 'product', component: ProductView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.path === '/login') {
    try {
      const response = await fetch('/api/session')
      const payload = await response.json()
      if (payload.authenticated) {
        return '/'
      }
    } catch {
      return true
    }
    return true
  }
  try {
    const response = await fetch('/api/session')
    const payload = await response.json()
    if (!payload.authenticated) {
      return '/login'
    }
  } catch {
    return '/login'
  }
  return true
})

export default router
