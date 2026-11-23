<script setup>
import { onMounted, ref } from 'vue'
import RegisterForm from './components/RegisterForm.vue'
import CheckForm from './components/CheckForm.vue'
import AdminLogin from './components/AdminLogin.vue'
import AdminDashboard from './components/AdminDashboard.vue'

const tab = ref('register')
const prefill = ref(null)
const page = ref('visitor')
const adminSession = ref(null)

function onExists(payload) {
  prefill.value = payload
  tab.value = 'check'
}

function onAuthenticated(session) {
  adminSession.value = session
  sessionStorage.setItem('centralis-admin-session', JSON.stringify(session))
  page.value = 'dashboard'
}

function signOut() {
  sessionStorage.removeItem('centralis-admin-session')
  adminSession.value = null
  page.value = 'visitor'
}

onMounted(() => {
  const savedSession = sessionStorage.getItem('centralis-admin-session')
  if (!savedSession) return

  try {
    const session = JSON.parse(savedSession)
    if (session?.token && session?.user?.role === 'admin') {
      adminSession.value = session
      page.value = 'dashboard'
    } else {
      sessionStorage.removeItem('centralis-admin-session')
    }
  } catch {
    sessionStorage.removeItem('centralis-admin-session')
  }
})
</script>

<template>
  <AdminLogin
    v-if="page === 'admin-login'"
    @authenticated="onAuthenticated"
    @back="page = 'visitor'"
  />
  <AdminDashboard
    v-else-if="page === 'dashboard' && adminSession"
    :session="adminSession"
    @sign-out="signOut"
  />
  <main v-else class="card">
    <section class="campus-panel" aria-label="SALISES campus">
      <img class="campus-image" src="/campus.png" alt="SALISES at the University of the West Indies" />
    </section>

    <section class="form-panel">
      <header class="brand-header">
        <img class="brand-logo" src="/salises-logo.jpg" alt="SALISES - The University of the West Indies" />
      </header>

      <div class="form-content">
        <div class="heading">
          <p class="eyebrow">Visitor Centre</p>
          <h1>{{ tab === 'register' ? 'Visitor registration' : 'Welcome back' }}</h1>
          <p class="sub">{{ tab === 'register' ? 'Enter your details to check in' : 'Check in or check out of the campus' }}</p>
        </div>

        <div class="tabs" aria-label="Visitor actions">
          <button :class="{ active: tab === 'register' }" @click="tab = 'register'">New visitor</button>
          <button :class="{ active: tab === 'check' }" @click="tab = 'check'">Check in / out</button>
        </div>

        <RegisterForm v-if="tab === 'register'" @exists="onExists" />
        <CheckForm v-else :prefill="prefill" />
        <button class="text-button admin-entry" type="button" @click="page = 'admin-login'">
          Administrator sign in
        </button>
      </div>
    </section>
  </main>
</template>