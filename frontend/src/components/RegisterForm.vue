<script setup>
import { reactive, ref } from 'vue'
import { post, fmt } from '../api'
import VisitPurpose from './VisitPurpose.vue'

const emit = defineEmits(['exists'])
const props = defineProps({ session: { type: Object, default: null } })
const blank = () => ({
  type: 'undergraduate', name: '', phone_number: '',
  student_id: '', faculty: '', purpose: '',
})
const form = reactive(blank())
const errors = ref({})
const banner = ref(null)
const busy = ref(false)
const formElement = ref(null)
const purposeForm = ref(null)

const isStudent = () => form.type !== 'external'

async function submit() {
  errors.value = {}
  banner.value = null
  if (purposeForm.value?.validate() === false || !formElement.value?.reportValidity()) return
  const reservationRequest = purposeForm.value?.getReservationData()

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
      let reservationConfirmation = ''
      if (reservationRequest) {
        let result
        try {
          result = await post(`/reservations/${reservationRequest.type}`, {
            ...reservationRequest,
            visitor_id: data.visitor.id,
          }, props.session.token)
        } catch (reservationError) {
          banner.value = {
            ok: false,
            text: `The visitor was registered and checked in, but the reservation request could not be submitted: ${reservationError.message || 'Please try again.'}`,
          }
          Object.assign(form, blank())
          return
        }
        if (!result.ok) {
          banner.value = {
            ok: false,
            text: `The visitor was registered and checked in, but the reservation request could not be submitted: ${result.data.error || 'Please try again.'}`,
          }
          Object.assign(form, blank())
          return
        }
        reservationConfirmation = ` Reservation request #${result.data.reservation.id} was submitted for administrator review.`
        const recent = JSON.parse(sessionStorage.getItem('centralis-recent-reservations') || '[]')
        recent.push({ ...result.data.reservation, visitor_name: data.visitor.name, resource_name: result.data.resource.name })
        sessionStorage.setItem('centralis-recent-reservations', JSON.stringify(recent.slice(-20)))
      }
      banner.value = {
        ok: true,
        text: `${data.message} Checked in at ${fmt(data.visit.check_in)}. Your visitor ID is ${data.visitor.id}; use it for future visits.${reservationConfirmation}`,
      }
      Object.assign(form, blank())
    } else if (status === 409) {
      emit('exists', {
        student_id: body.student_id || '',
        purpose: body.purpose,
        reservationRequest,
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

    <VisitPurpose ref="purposeForm" v-model="form.purpose"
      :staff-authenticated="session?.user?.role === 'staff'" />
    <span class="err">{{ errors.purpose }}</span>

    <button class="btn" type="submit" :disabled="busy">Register and check in</button>
    <div v-if="banner" class="banner" :class="banner.ok ? 'ok' : 'bad'">{{ banner.text }}</div>
  </form>
</template>
