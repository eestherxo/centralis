<script setup>
import { reactive, ref, watch } from 'vue'
import { post, fmt } from '../api'
import VisitPurpose from './VisitPurpose.vue'

const props = defineProps({ prefill: Object, session: { type: Object, default: null } })

const form = reactive({ visitor_id: '', purpose: '' })
const errors = ref({})
const banner = ref(null)
const busy = ref(false)
const formElement = ref(null)
const purposeForm = ref(null)

watch(
  () => props.prefill,
  (p) => {
    if (!p) return
    form.visitor_id = p.visitor_id || ''
    form.purpose = p.purpose || ''
    errors.value = {}
    banner.value = { ok: false, text: p.message }
  },
  { immediate: true },
)

async function submit(kind) {
  errors.value = {}
  banner.value = null
  if (kind === 'check-in' &&
      (purposeForm.value?.validate() === false || !formElement.value?.reportValidity())) return
  const reservationRequest = kind === 'check-in' ? purposeForm.value?.getReservationData() : null

  const visitorId = Number(form.visitor_id)
  if (!Number.isSafeInteger(visitorId) || visitorId <= 0) {
    errors.value = { visitor_id: 'Enter a valid visitor ID.' }
    return
  }
  const body = { visitor_id: visitorId }
  if (kind === 'check-in') body.purpose = form.purpose

  busy.value = true
  try {
    const { ok, data } = await post(`/visitors/${kind}`, body)
    if (ok) {
      const when = kind === 'check-in' ? data.visit.check_in : data.visit.check_out
      let reservationConfirmation = ''
      if (reservationRequest) {
        let result
        try {
          result = await post(`/reservations/${reservationRequest.type}`, {
            ...reservationRequest,
            visitor_id: visitorId,
          }, props.session.token)
        } catch (reservationError) {
          banner.value = { ok: false, text: `The visitor was checked in, but the reservation request could not be submitted: ${reservationError.message || 'Please try again.'}` }
          form.visitor_id = form.purpose = ''
          return
        }
        if (!result.ok) {
          banner.value = { ok: false, text: `The visitor was checked in, but the reservation request could not be submitted: ${result.data.error || 'Please try again.'}` }
          form.visitor_id = form.purpose = ''
          return
        }
        reservationConfirmation = ` Reservation request #${result.data.reservation.id} was submitted for administrator review.`
        const recent = JSON.parse(sessionStorage.getItem('centralis-recent-reservations') || '[]')
        recent.push({ ...result.data.reservation, visitor_name: result.data.visitor.name, resource_name: result.data.resource.name })
        sessionStorage.setItem('centralis-recent-reservations', JSON.stringify(recent.slice(-20)))
      }
      banner.value = {
        ok: true,
        text: `${data.message} ${fmt(when)}.${reservationConfirmation}`,
      }
      form.visitor_id = form.purpose = ''
    } else {
      errors.value = data.fields || {}
      banner.value = { ok: false, text: data.error || 'Something went wrong.' }
    }
  } catch {
    banner.value = { ok: false, text: 'Could not reach the server.' }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form ref="formElement" novalidate @submit.prevent>
    <label>Visitor ID
      <input v-model="form.visitor_id" :class="{ bad: errors.visitor_id }" placeholder="Enter your visitor ID" required />
      <span class="err">{{ errors.visitor_id }}</span>
    </label>

    <VisitPurpose ref="purposeForm" v-model="form.purpose"
      :staff-authenticated="session?.user?.role === 'staff'"
      :initial-reservation="prefill?.reservationRequest" />
    <span class="err">{{ errors.purpose }}</span>

    <div class="row">
      <button class="btn" type="button" :disabled="busy" @click="submit('check-in')">Check in</button>
      <button class="btn ghost" type="button" :disabled="busy" @click="submit('check-out')">Check out</button>
    </div>
    <div v-if="banner" class="banner" :class="banner.ok ? 'ok' : 'bad'">{{ banner.text }}</div>
  </form>
</template>
