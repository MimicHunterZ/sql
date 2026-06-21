import { createRouter, createWebHistory } from 'vue-router'

import Home       from '../views/Home.vue'
import Dashboard  from '../views/Dashboard.vue'
import GameDetail from '../views/GameDetail.vue'
import Compare    from '../views/Compare.vue'
import Market     from '../views/Market.vue'

const routes = [
  { path: '/',          name: 'home',      component: Home       },
  { path: '/dashboard', name: 'dashboard', component: Dashboard  },
  { path: '/game/:id',  name: 'game',      component: GameDetail },
  { path: '/compare',   name: 'compare',   component: Compare    },
  { path: '/market',    name: 'market',    component: Market     },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
