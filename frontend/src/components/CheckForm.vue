<script setup>
import { reactive, ref } from 'vue'
import { post, fmt } from '../api'
import VisitPurpose from './VisitPurpose.vue'

defineProps({ session: { type: Object, default: null } })

const form = reactive({ visitor_id: '', purpose: '' })
const errors = ref({})
const banner = ref(null)
const busy = ref(false)
const formElement = ref(null)
const purposeForm = ref(null)

async function submit(kind) {
  errors.value = {}
  banner.value = null
  if (kind === 'check-in' &&
      (purposeForm.value?.validate() === false || !formElement.value?.reportValidity())) return

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
      banner.value = {
        ok: true,
        text: `${data.message} ${fmt(when)}.`,
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
      <input v-model="form.visitor_id" :class="{ bad: errors.visitor_id }" placeholder="Enter visitor ID" required />
      <span class="err">{{ errors.visitor_id }}</span>
    </label>

    <VisitPurpose ref="purposeForm" v-model="form.purpose" simple />
    <span class="err">{{ errors.purpose }}</span>

    <div class="row">
      <button class="btn" type="button" :disabled="busy" @click="submit('check-in')">Check in</button>
      <button class="btn ghost" type="button" :disabled="busy" @click="submit('check-out')">Check out</button>
    </div>
    <div v-if="banner" class="banner" :class="banner.ok ? 'ok' : 'bad'">{{ banner.text }}</div>
  </form>
</template>
