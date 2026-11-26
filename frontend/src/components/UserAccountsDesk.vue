<script setup>
import { reactive, ref } from 'vue'
import { post } from '../api'

const props = defineProps({ session: { type: Object, required: true } })
const form = reactive({ name: '', email: '', password: '', role: 'staff' })
const error = ref('')
const notice = ref('')
const busy = ref(false)

async function createAccount() {
  error.value = ''
  notice.value = ''
  busy.value = true
  try {
    const result = await post('/auth/users', { ...form }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not create this account.'
      return
    }
    notice.value = `${result.data.user.name} can now sign in as ${result.data.user.role}.`
    Object.assign(form, { name: '', email: '', password: '', role: 'staff' })
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="ops-card account-card">
    <div class="section-heading"><div><h2>Create a staff account</h2><p class="sub">Staff accounts can submit reservations and record journal sales.</p></div></div>
    <form class="ops-form" @submit.prevent="createAccount">
      <label>Full name<input v-model="form.name" autocomplete="name" required maxlength="200" /></label>
      <label>Email address<input v-model="form.email" type="email" autocomplete="email" required maxlength="254" /></label>
      <label>Temporary password<input v-model="form.password" type="password" autocomplete="new-password" required minlength="8" /></label>
      <label>Role<select v-model="form.role"><option value="staff">Staff</option><option value="admin">Administrator</option></select></label>
      <button class="btn" type="submit" :disabled="busy">{{ busy ? 'Creating…' : 'Create account' }}</button>
    </form>
    <p v-if="error" class="banner bad" role="alert">{{ error }}</p>
    <p v-if="notice" class="banner ok" role="status">{{ notice }}</p>
  </section>
</template>
