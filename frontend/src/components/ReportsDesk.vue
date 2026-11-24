<script setup>
import { reactive, ref } from 'vue'
import { post } from '../api'

const props = defineProps({ session: { type: Object, required: true } })

const reportTypes = [
  { value: 'visitor', label: 'Visitor activity' },
  { value: 'reservation', label: 'Resource reservations' },
  { value: 'journal_sales', label: 'Journal sales' },
  { value: 'fines', label: 'Fines' },
]
const today = new Date()
const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const startOfYear = `${today.getFullYear()}-01-01`
const form = reactive({ report_type: 'visitor', start_date: startOfYear, end_date: todayText })
const report = ref(null)
const error = ref('')
const busy = ref(false)

async function generate() {
  error.value = ''
  report.value = null
  busy.value = true
  try {
    const result = await post('/reports/generate', { ...form }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not generate this report.'
      return
    }
    report.value = result.data
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}

async function exportReport() {
  error.value = ''
  busy.value = true
  try {
    const response = await fetch('/reports/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${props.session.token}` },
      body: JSON.stringify(form),
    })
    if (!response.ok) {
      const data = await response.json()
      error.value = data.error || 'Could not export this report.'
      return
    }
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${form.report_type}_report.xlsx`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="ops-card">
    <div class="section-heading">
      <div><h2>Reports</h2><p class="sub">Review SALISES activity and export records to Excel.</p></div>
    </div>
    <form class="ops-form" @submit.prevent="generate">
      <label>Report type
        <select v-model="form.report_type">
          <option v-for="type in reportTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
        </select>
      </label>
      <label>From<input v-model="form.start_date" type="date" required /></label>
      <label>To<input v-model="form.end_date" type="date" required /></label>
      <button class="btn" type="submit" :disabled="busy">{{ busy ? 'Working…' : 'Generate report' }}</button>
      <button class="btn ghost" type="button" :disabled="busy" @click="exportReport">Export Excel</button>
    </form>
    <p v-if="error" class="banner bad" role="alert">{{ error }}</p>
    <p v-if="report?.message" class="empty-state">{{ report.message }}</p>
    <div v-if="report?.records?.length" class="table-wrap ops-table-wrap">
      <table>
        <thead><tr><th v-for="key in Object.keys(report.records[0])" :key="key">{{ key.replaceAll('_', ' ') }}</th></tr></thead>
        <tbody><tr v-for="(record, index) in report.records" :key="record.id || record.visitor_id || index">
          <td v-for="key in Object.keys(report.records[0])" :key="key">{{ Array.isArray(record[key]) ? record[key].join(', ') : record[key] }}</td>
        </tr></tbody>
      </table>
    </div>
  </section>
</template>
