<script setup>
import { reactive, ref } from 'vue'
import { post, fmt } from '../api'

const emit = defineEmits(['exists'])
const blank = () => ({
  type: 'undergraduate', name: '', phone_number: '',
  id_number: '', faculty: '', purpose: '',
})
const form = reactive(blank())
const errors = ref({})
const banner = ref(null)
const busy = ref(false)

const isStudent = () => form.type !== 'external'

async function submit() {
  errors.value = {}
  banner.value = null

  const body = {
    type: form.type,
    name: form.name,
    phone_number: form.phone_number,
    purpose: form.purpose,
  }
  if (isStudent()) {
    body.id_number = form.id_number
    body.faculty = form.faculty
  } else if (form.id_number.trim()) {
    body.id_number = form.id_number   // optional for externals
  }

  busy.value = true
  try {
    const { ok, status, data } = await post('/visitors/register', body)
    if (ok) {
      banner.value = { ok: true, text: `${data.message} Checked in at ${fmt(data.visit.check_in)}.` }
      Object.assign(form, blank())
    } else if (status === 409) {
      const hasId = !!(body.id_number && body.id_number.trim())
      emit('exists', {
        mode: hasId ? 'id' : 'phone',
        id_number: body.id_number || '',
        phone_number: body.phone_number,
        purpose: body.purpose,
        message: data.error,
      })
    } else {
      errors.value = data.fields || {}
      banner.value = { ok: false, text: data.error || 'Registration failed.' }
    }
  } catch {
    banner.value = { ok: false, text: 'Could not reach the server.' }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form novalidate @submit.prevent="submit">
    <label>Visitor type
      <select v-model="form.type" :class="{ bad: errors.type }">
        <option value="undergraduate">Undergraduate student</option>
        <option value="postgraduate">Postgraduate student</option>
        <option value="external">External visitor</option>
      </select>
      <span class="err">{{ errors.type }}</span>
    </label>

    <label>Full name
      <input v-model="form.name" :class="{ bad: errors.name }" placeholder="Jane Doe" />
      <span class="err">{{ errors.name }}</span>
    </label>

    <label>Phone number
      <input v-model="form.phone_number" type="tel" :class="{ bad: errors.phone_number }" placeholder="876 123 4567" />
      <span class="err">{{ errors.phone_number }}</span>
    </label>

    <label>ID number <small v-if="!isStudent()">(optional)</small>
      <input v-model="form.id_number" :class="{ bad: errors.id_number }" placeholder="e.g. 620123456" />
      <span class="err">{{ errors.id_number }}</span>
    </label>

    <label v-if="isStudent()">Faculty
      <input v-model="form.faculty" list="faculties" :class="{ bad: errors.faculty }" placeholder="Choose or type" />
      <datalist id="faculties">
        <option>Engineering</option>
        <option>Humanities and Education</option>
        <option>Law</option>
        <option>Medical Sciences</option>
        <option>Science and Technology</option>
        <option>Social Sciences</option>
        <option>Sport</option>
      </datalist>
      <span class="err">{{ errors.faculty }}</span>
    </label>

    <label>Purpose of visit
      <input v-model="form.purpose" :class="{ bad: errors.purpose }" placeholder="e.g. Research" />
      <span class="err">{{ errors.purpose }}</span>
    </label>

    <button class="btn" type="submit" :disabled="busy">Register and check in</button>
    <div v-if="banner" class="banner" :class="banner.ok ? 'ok' : 'bad'">{{ banner.text }}</div>
  </form>
</template>