import { createRouter, createWebHistory } from 'vue-router'
import ModelList from './views/ModelList.vue'
import Annotation from './views/Annotation.vue'
import Training from './views/Training.vue'
import Inference from './views/Inference.vue'
import History from './views/History.vue'
import ProjectList from './views/ProjectList.vue'
import ProjectDetail from './views/ProjectDetail.vue'

const routes = [
  { path: '/', redirect: '/models' },
  { path: '/models', component: ModelList, name: 'ModelList' },
  { path: '/projects', component: ProjectList, name: 'ProjectList' },
  { path: '/projects/:id', component: ProjectDetail, name: 'ProjectDetail' },
  { path: '/annotation', component: Annotation, name: 'Annotation' },
  { path: '/training', component: Training, name: 'Training' },
  { path: '/inference', component: Inference, name: 'Inference' },
  { path: '/history', component: History, name: 'History' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
