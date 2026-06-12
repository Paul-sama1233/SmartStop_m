import { createRouter, createWebHistory } from 'vue-router'
import BusView from '../views/BusView.vue'
import MetroView from '../views/MetroView.vue'
import MapView from '../views/MapView.vue'
import RouteDetailView from '../views/RouteDetailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/bus' },
    { path: '/bus', name: 'bus', component: BusView },
    { path: '/metro', name: 'metro', component: MetroView },
    { path: '/map', name: 'map', component: MapView },
    { path: '/route/:number', name: 'route-detail', component: RouteDetailView },
  ],
})

export default router
