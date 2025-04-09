import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  faTrash,
  faChartLine,
  faFire,
  faUser,
  faRightFromBracket
} from '@fortawesome/free-solid-svg-icons'

library.add(faTrash, faChartLine, faFire, faUser, faRightFromBracket)

const app = createApp(App)

app.component('font-awesome-icon', FontAwesomeIcon)
app.use(router).mount('#app')
