<script setup>
import { reactive, ref } from 'vue'
import { post } from '../api'
import VisitPurpose from './VisitPurpose.vue'

const blank = () => ({
  type: 'undergraduate', name: '', phone_number: '',
  student_id: '', faculty: '', purpose: '',
})
const form = reactive(blank())
const errors = ref({})
const modal = ref(null)
const busy = ref(false)
const formElement = ref(null)
const purposeForm = ref(null)

const isStudent = () => form.type !== 'external'

function dismissModal() {
  modal.value = null
}

async function submit() {
  errors.value = {}
  modal.value = null
  if (purposeForm.value?.validate() === false || !formElement.value?.reportValidity()) return

  const body = {
    type: form.type,
    name: form.name,
    phone_number: form.phone_number,
    purpose: form.purpose,
  }
  if (isStudent()) {
    body.student_id = form.student_id
    body.faculty = form.faculty
  }

  busy.value = true
  try {
    const { ok, status, data } = await post('/visitors/register', body)
    if (ok) {
      modal.value = {
        ok: true,
        title: 'Registration complete',
        visitorId: data.visitor.id,
      }
      Object.assign(form, blank())
    } else if (status === 409) {
      modal.value = {
        ok: false,
        title: 'Registration failed',
        text: data.error || 'This visitor is already registered. Ask staff to check you in with your visitor ID.',
      }
    } else {
      errors.value = data.fields || {}
      modal.value = {
        ok: false,
        title: 'Registration failed',
        text: data.error || 'Registration failed.',
      }
    }
  } catch {
    modal.value = {
      ok: false,
      title: 'Registration failed',
      text: 'Could not reach the server.',
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form ref="formElement" novalidate @submit.prevent="submit">
    <label>Visitor type
      <select v-model="form.type" :class="{ bad: errors.type }">
        <option value="undergraduate">Undergraduate student</option>
        <option value="postgraduate">Postgraduate student</option>
        <option value="external">External visitor</option>
      </select>
      <span class="err">{{ errors.type }}</span>
    </label>

    <label>Full name
      <input v-model="form.name" :class="{ bad: errors.name }" placeholder="Jane Doe" required />
      <span class="err">{{ errors.name }}</span>
    </label>

    <label>Phone number
      <input v-model="form.phone_number" type="tel" :class="{ bad: errors.phone_number }" placeholder="876 123 4567" required />
      <span class="err">{{ errors.phone_number }}</span>
    </label>

    <label v-if="isStudent()">Student ID
      <input v-model="form.student_id" :class="{ bad: errors.student_id }" placeholder="e.g. 620123456" required />
      <span class="err">{{ errors.student_id }}</span>
    </label>

    <label v-if="isStudent()">Faculty
      <input v-model="form.faculty" list="faculties" :class="{ bad: errors.faculty }" placeholder="Choose or type" required />
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

    <VisitPurpose ref="purposeForm" v-model="form.purpose" simple />
    <span class="err">{{ errors.purpose }}</span>

    <button class="btn" type="submit" :disabled="busy">Register and check in</button>
  </form>

  <div
    v-if="modal"
    class="modal-backdrop"
    role="presentation"
    @click.self="dismissModal"
  >
    <div
      class="modal-dialog"
      :class="modal.ok ? 'ok' : 'bad'"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="modal.ok ? 'registration-confirm-title' : 'registration-error-title'"
    >
      <h2 :id="modal.ok ? 'registration-confirm-title' : 'registration-error-title'">{{ modal.title }}</h2>
      <p v-if="modal.ok">
        Visitor registered and checked in successfully. Your visitor ID is
        <strong class="visitor-id">{{ modal.visitorId }}</strong>
      </p>
      <p v-else>{{ modal.text }}</p>
      <button class="btn" type="button" @click="dismissModal">OK</button>
    </div>
  </div>
</template>
