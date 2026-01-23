import { createRouter, createWebHistory } from 'vue-router'
import IndexView from '../views/IndexView.vue'
import AddView from '../views/AddView.vue'
import ProductView from '../views/ProductView.vue'

const routes = [
  { path: '/', name: 'home', component: IndexView },
  { path: '/add', name: 'add', component: AddView },
  { path: '/product', name: 'product', component: ProductView },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
