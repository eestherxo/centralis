<script setup>
import { reactive, ref, watch } from 'vue'
import { post, fmt } from '../api'

const props = defineProps({ prefill: Object })

const form = reactive({ id_number: '', purpose: '' })
const errors = ref({})
const banner = ref(null)
const busy = ref(false)

watch(
  () => props.prefill,
  (p) => {
    if (!p) return
    form.id_number = p.id_number || ''
    form.purpose = p.purpose || ''
    errors.value = {}
    banner.value = { ok: false, text: p.message }
  },
  { immediate: true },
)

async function submit(kind) {
  errors.value = {}
  banner.value = null

  const body = { id_number: form.id_number }
  const numericId = Number(form.id_number)
  if (Number.isSafeInteger(numericId) && numericId > 0) {
    body.visitor_id = numericId
  }
  if (kind === 'check-in') body.purpose = form.purpose

  busy.value = true
  try {
    const { ok, data } = await post(`/visitors/${kind}`, body)
    if (ok) {
      const when = kind === 'check-in' ? data.visit.check_in : data.visit.check_out
      banner.value = { ok: true, text: `${data.message} ${fmt(when)}.` }
      form.id_number = form.purpose = ''
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
  <form novalidate @submit.prevent>
    <label>ID number 
      <input v-model="form.id_number" :class="{ bad: errors.id_number || errors.visitor_id }" placeholder="Enter your ID" />
      <span class="err">{{ errors.id_number || errors.visitor_id }}</span>
    </label>

    <label>Purpose of visit <small>(needed to check in)</small>
      <input v-model="form.purpose" :class="{ bad: errors.purpose }" placeholder="e.g. Research" />
      <span class="err">{{ errors.purpose }}</span>
    </label>

    <div class="row">
      <button class="btn" type="button" :disabled="busy" @click="submit('check-in')">Check in</button>
      <button class="btn ghost" type="button" :disabled="busy" @click="submit('check-out')">Check out</button>
    </div>
    <div v-if="banner" class="banner" :class="banner.ok ? 'ok' : 'bad'">{{ banner.text }}</div>
  </form>
</template>