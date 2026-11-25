<script setup>
import { ref } from 'vue'
import { post } from '../api'

const emit = defineEmits(['authenticated', 'back'])
const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const { ok, data } = await post('/auth/login', {
      email: email.value.trim(),
      password: password.value,
    })
    if (!ok) {
      error.value = data.error || 'Sign in failed.'
      return
    }
    if (!['admin', 'staff'].includes(data.user?.role) || !data.access_token) {
      error.value = 'This account does not have staff or administrator access.'
      return
    }
    emit('authenticated', { token: data.access_token, user: data.user })
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="admin-auth-page">
    <section class="admin-auth-card">
      <a class="brand-link" href="/" aria-label="SALISES visitor centre">
        <img src="/salises-logo.jpg" alt="SALISES - The University of the West Indies" />
      </a>
      <p class="eyebrow">Staff and administrator portal</p>
      <h1>Sign in</h1>
      <p class="sub">Sign in with your SALISES staff or administrator account.</p>

      <form class="admin-form" @submit.prevent="submit">
        <label for="admin-email">Email address</label>
        <input
          id="admin-email"
          v-model="email"
          type="email"
          autocomplete="username"
          required
          :disabled="busy"
        />

        <label for="admin-password">Password</label>
        <input
          id="admin-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          :disabled="busy"
        />

        <p v-if="error" class="banner bad" role="alert">{{ error }}</p>
        <button class="btn" type="submit" :disabled="busy">
          {{ busy ? 'Signing in…' : 'Sign in to dashboard' }}
        </button>
      </form>

      <button class="text-button" type="button" @click="emit('back')">
        Return to visitor centre
      </button>
    </section>
  </main>
</template>
