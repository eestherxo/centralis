<script setup>
import { ref } from 'vue'
import RegisterForm from './components/RegisterForm.vue'
import CheckForm from './components/CheckForm.vue'

const tab = ref('register')
const prefill = ref(null)

function onExists(payload) {
  prefill.value = payload
  tab.value = 'check'
}
</script>

<template>
  <main class="card">
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
      </div>
    </section>
  </main>
</template>