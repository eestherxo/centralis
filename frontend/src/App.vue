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
  page.value = session.user.role === 'staff' ? 'visitor' : 'dashboard'
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
    if (session?.token && ['admin', 'staff'].includes(session?.user?.role)) {
      adminSession.value = session
      page.value = session.user.role === 'staff' ? 'visitor' : 'dashboard'
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
      <div class="campus-caption">
        <span>SALISES · UWI</span>
        <p>Welcome to the visitor centre</p>
        <small>Register your visit or check in with your visitor ID.</small>
      </div>
    </section>

    <section class="form-panel">
      <header class="brand-header">
        <img class="brand-logo" src="/salises-logo.jpg" alt="SALISES - The University of the West Indies" />
      </header>

      <div v-if="adminSession?.user?.role === 'staff'" class="staff-mode-bar">
        <span>Staff assisted check-in · {{ adminSession.user.name }}</span>
        <div>
          <button class="text-button" type="button" @click="page = 'dashboard'">Open dashboard</button>
          <button class="text-button" type="button" @click="signOut">Sign out</button>
        </div>
      </div>

      <div class="form-content">
        <div class="heading">
          <p class="eyebrow">Visitor Centre</p>
          <h1>{{ tab === 'register' ? 'Visitor registration' : 'Returning visitor' }}</h1>
          <p class="sub">{{ tab === 'register' ? 'Complete the form to register and check in' : 'Use your visitor ID to check in or check out' }}</p>
        </div>

        <div class="tabs" aria-label="Visitor actions">
          <button :class="{ active: tab === 'register' }" @click="tab = 'register'">New visitor</button>
          <button :class="{ active: tab === 'check' }" @click="tab = 'check'">Returning visitor</button>
        </div>

        <RegisterForm v-if="tab === 'register'" :session="adminSession" @exists="onExists" />
        <CheckForm v-else :prefill="prefill" :session="adminSession" />
        <button v-if="!adminSession" class="text-button admin-entry" type="button" @click="page = 'admin-login'">
          Staff and administrator sign in
        </button>
      </div>
    </section>
  </main>
</template>
