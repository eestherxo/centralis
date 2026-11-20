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
    <h1>Document Centre / Databank</h1>
    <p class="sub">Visitor register</p>

    <div class="tabs">
      <button :class="{ active: tab === 'register' }" @click="tab = 'register'">New visitor</button>
      <button :class="{ active: tab === 'check' }" @click="tab = 'check'">Check in / out</button>
    </div>

    <RegisterForm v-if="tab === 'register'" @exists="onExists" />
    <CheckForm v-else :prefill="prefill" />
  </main>
</template>