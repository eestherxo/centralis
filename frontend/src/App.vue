<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import RegisterForm from './components/RegisterForm.vue'
import AdminLogin from './components/AdminLogin.vue'
import AdminDashboard from './components/AdminDashboard.vue'

const page = ref('visitor')
const adminSession = ref(null)

function isAdminHash() {
  return window.location.hash === '#admin'
}

function showVisitor() {
  if (window.location.hash === '#admin') {
    history.replaceState(null, '', `${window.location.pathname}${window.location.search}`)
  }
  page.value = 'visitor'
}

function syncPageFromLocation() {
  if (adminSession.value) {
    if (!isAdminHash()) window.location.hash = 'admin'
    page.value = 'dashboard'
    return
  }
  page.value = isAdminHash() ? 'admin-login' : 'visitor'
}

function onAuthenticated(session) {
  adminSession.value = session
  sessionStorage.setItem('centralis-admin-session', JSON.stringify(session))
  if (!isAdminHash()) window.location.hash = 'admin'
  page.value = 'dashboard'
}

function signOut() {
  sessionStorage.removeItem('centralis-admin-session')
  adminSession.value = null
  showVisitor()
}

onMounted(() => {
  const savedSession = sessionStorage.getItem('centralis-admin-session')
  if (savedSession) {
    try {
      const session = JSON.parse(savedSession)
      if (session?.token && ['admin', 'staff'].includes(session?.user?.role)) {
        adminSession.value = session
      } else {
        sessionStorage.removeItem('centralis-admin-session')
      }
    } catch {
      sessionStorage.removeItem('centralis-admin-session')
    }
  }

  syncPageFromLocation()
  window.addEventListener('hashchange', syncPageFromLocation)
})

onUnmounted(() => {
  window.removeEventListener('hashchange', syncPageFromLocation)
})
</script>

<template>
  <AdminLogin
    v-if="page === 'admin-login'"
    @authenticated="onAuthenticated"
    @back="showVisitor"
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
        <small>Register your visit at the desk.</small>
      </div>
    </section>

    <section class="form-panel">
      <header class="brand-header">
        <img class="brand-logo" src="/salises-logo.jpg" alt="SALISES - The University of the West Indies" />
      </header>

      <div class="form-content">
        <div class="heading">
          <p class="eyebrow">Visitor Centre</p>
          <h1>Visitor registration</h1>
          <p class="sub">Complete the form to register and check in</p>
        </div>

        <RegisterForm />
      </div>
    </section>
  </main>
</template>
