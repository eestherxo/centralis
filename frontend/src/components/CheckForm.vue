<script setup>
import { reactive, ref, watch } from 'vue'
import { post, fmt } from '../api'

const props = defineProps({ prefill: Object })

const mode = ref('id') // 'id' or 'phone'
const form = reactive({ id_number: '', phone_number: '', purpose: '' })
const errors = ref({})
const banner = ref(null)
const busy = ref(false)

watch(
  () => props.prefill,
  (p) => {
    if (!p) return
    mode.value = p.mode
    form.id_number = p.id_number || ''
    form.phone_number = p.phone_number || ''
    form.purpose = p.purpose || ''
    errors.value = {}
    banner.value = { ok: false, text: p.message }
  },
  { immediate: true },
)

function setMode(next) {
  mode.value = next
  errors.value = {}
}

async function submit(kind) {
  errors.value = {}
  banner.value = null

  const body = mode.value === 'id'
    ? { id_number: form.id_number }
    : { phone_number: form.phone_number }
  if (kind === 'check-in') body.purpose = form.purpose

  busy.value = true
  try {
    const { ok, data } = await post(`/visitors/${kind}`, body)
    if (ok) {
      const when = kind === 'check-in' ? data.visit.check_in : data.visit.check_out
      banner.value = { ok: true, text: `${data.message} ${fmt(when)}.` }
      form.id_number = form.phone_number = form.purpose = ''
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
    <div class="seg">
      <button type="button" :class="{ active: mode === 'id' }" @click="setMode('id')">I have an ID number</button>
      <button type="button" :class="{ active: mode === 'phone' }" @click="setMode('phone')">Use phone number</button>
    </div>

    <label v-if="mode === 'id'">ID number
      <input v-model="form.id_number" :class="{ bad: errors.id_number }" placeholder="e.g. 620123456" />
      <span class="err">{{ errors.id_number }}</span>
    </label>
    <label v-else>Phone number
      <input v-model="form.phone_number" type="tel" :class="{ bad: errors.phone_number || errors.id_number }" placeholder="876 123 4567" />
      <span class="err">{{ errors.phone_number || errors.id_number }}</span>
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