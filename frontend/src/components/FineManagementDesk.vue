<script setup>
import { computed, onMounted, ref } from 'vue'
import { apiUrl, get, post } from '../api'

const props = defineProps({ session: { type: Object, required: true } })
const loans = ref([])
const fines = ref([])
const visitors = ref([])
const resources = ref([])
const filter = ref('all')
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const notice = ref('')
const today = new Date()
const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const returnDates = ref({})
const lostForm = ref({ resource_id: '', visitor_id: '', condition: 'lost' })
const visibleFines = computed(() => fines.value.filter((fine) => filter.value === 'all' || fine.status === filter.value))
const selectedLossResource = computed(() => resources.value.find((item) => String(item.id) === String(lostForm.value.resource_id)))

function returnDateForm(loanId) {
  if (!returnDates.value[loanId]) returnDates.value[loanId] = { return_date: todayText, condition: 'good' }
  return returnDates.value[loanId]
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [loanResult, fineResult, visitorResult, resourceResult] = await Promise.all([
      get('/fines/loans', props.session.token),
      get('/fines', props.session.token),
      get('/fines/visitors', props.session.token),
      get('/fines/resources', props.session.token),
    ])
    const failed = [loanResult, fineResult, visitorResult, resourceResult].find((result) => !result.ok)
    if (failed) throw new Error(failed.data.error || 'Could not load fine management records.')
    loans.value = loanResult.data.loans || []
    fines.value = fineResult.data.fines || []
    visitors.value = visitorResult.data.visitors || []
    resources.value = resourceResult.data.resources || []
    if (!lostForm.value.resource_id && resources.value.length) lostForm.value.resource_id = String(resources.value[0].id)
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    loading.value = false
  }
}

async function recordReturn(loan) {
  error.value = ''
  notice.value = ''
  const form = returnDates.value[loan.id] || { return_date: todayText, condition: 'good' }
  busy.value = true
  try {
    const result = await post('/fines/returns', {
      reservation_id: Number(loan.id), return_date: form.return_date, condition: form.condition,
    }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not record this return.'
      return
    }
    const charges = result.data.fines || []
    notice.value = charges.length
      ? `Return recorded. ${charges.length} fine${charges.length === 1 ? '' : 's'} added to the visitor account.`
      : 'Return recorded. No fine is owed.'
    await loadData()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}

async function recordLostOrDamaged() {
  error.value = ''
  notice.value = ''
  if (!lostForm.value.resource_id) {
    error.value = 'Choose a resource.'
    return
  }
  busy.value = true
  try {
    const result = await post('/fines/lost-or-damaged', {
      resource_id: Number(lostForm.value.resource_id),
      condition: lostForm.value.condition,
      ...(lostForm.value.visitor_id ? { visitor_id: Number(lostForm.value.visitor_id) } : {}),
    }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not record this resource loss or damage.'
      return
    }
    notice.value = `${selectedLossResource.value?.name || 'Resource'} marked ${lostForm.value.condition}; a replacement fine was recorded.`
    lostForm.value.visitor_id = ''
    await loadData()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}

async function confirmPayment(fine) {
  error.value = ''
  notice.value = ''
  try {
    const result = await post(`/fines/${fine.id}/confirm-payment`, {}, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not confirm payment.'
      return
    }
    notice.value = `Payment confirmed for fine #${fine.id}.`
    await loadData()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

async function downloadReceipt(fine) {
  error.value = ''
  try {
    const response = await fetch(apiUrl(`/fines/${fine.id}/receipt`), {
      headers: { Authorization: `Bearer ${props.session.token}` },
    })
    if (!response.ok) {
      const data = await response.json()
      error.value = data.error || 'Could not create the fine receipt.'
      return
    }
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `fine-receipt-${fine.id}.pdf`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

onMounted(loadData)
</script>

<template>
  <div class="ops-grid fine-management">
    <section class="ops-card ops-span">
      <div class="section-heading">
        <div><h2>Borrowed books and returns</h2><p class="sub">Late returns are charged $50 per day. Mark damaged returns to add the replacement charge.</p></div>
        <button class="btn ghost refresh-button" type="button" :disabled="loading" @click="loadData">{{ loading ? 'Refreshing…' : 'Refresh' }}</button>
      </div>
      <div v-if="loans.length" class="table-wrap ops-table-wrap"><table>
        <thead><tr><th>Visitor</th><th>Book</th><th>Due date</th><th>Late</th><th>Fine so far</th><th>Return</th><th>Condition</th><th>Action</th></tr></thead>
        <tbody><tr v-for="loan in loans" :key="loan.id">
          <td>{{ loan.visitor_name }} · #{{ loan.visitor_id }}</td><td>{{ loan.resource_name }} · #{{ loan.resource_id }}</td>
          <td>{{ loan.expected_return }}</td><td>{{ loan.days_late }} days</td><td>${{ Number(loan.fine_so_far).toFixed(2) }}</td>
          <td><input v-model="returnDateForm(loan.id).return_date" type="date" :max="todayText" aria-label="Actual return date" /></td>
          <td><select v-model="returnDateForm(loan.id).condition" aria-label="Returned resource condition"><option value="good">Good</option><option value="damaged">Damaged</option></select></td>
          <td><button class="text-button" type="button" :disabled="busy" @click="recordReturn(loan)">Record return</button></td>
        </tr></tbody>
      </table></div>
      <p v-else-if="!loading" class="empty-state">No active book loans are currently listed.</p>
    </section>

    <section class="ops-card">
      <div class="section-heading"><div><h2>Record lost or damaged resource</h2><p class="sub">The responsible visitor is charged the resource replacement cost.</p></div></div>
      <form class="ops-form" @submit.prevent="recordLostOrDamaged">
        <label>Resource<select v-model="lostForm.resource_id" required><option value="" disabled>Choose a resource</option><option v-for="resource in resources" :key="`${resource.type}-${resource.id}`" :value="String(resource.id)">{{ resource.name }} · ${{ Number(resource.price).toFixed(2) }}</option></select></label>
        <label>Condition<select v-model="lostForm.condition"><option value="lost">Lost</option><option value="damaged">Damaged</option></select></label>
        <label>Responsible visitor<select v-model="lostForm.visitor_id"><option value="">Use active borrower if available</option><option v-for="visitor in visitors" :key="visitor.id" :value="String(visitor.id)">{{ visitor.name }} · #{{ visitor.id }}</option></select></label>
        <p v-if="selectedLossResource" class="field-hint">Replacement charge: ${{ Number(selectedLossResource.price).toFixed(2) }}.</p>
        <button class="btn" type="submit" :disabled="busy || !resources.length">{{ busy ? 'Saving…' : 'Record condition and fine' }}</button>
        <p v-if="!resources.length && !loading" class="empty-state">No eligible good-condition resources with a replacement price were found.</p>
      </form>
    </section>

    <section class="ops-card">
      <div class="section-heading"><div><h2>Fine records</h2><p class="sub">Confirm payments after SALISES receives them; receipts are available for paid fines.</p></div></div>
      <div class="filter-row"><label>Show<select v-model="filter"><option value="all">All fines</option><option value="unpaid">Unpaid</option><option value="paid">Paid</option></select></label></div>
      <div v-if="visibleFines.length" class="table-wrap ops-table-wrap"><table>
        <thead><tr><th>Fine</th><th>Visitor</th><th>Resource</th><th>Reason</th><th>Amount</th><th>Issued</th><th>Status</th><th>Action</th></tr></thead>
        <tbody><tr v-for="fine in visibleFines" :key="fine.id">
          <td>#{{ fine.id }}</td><td>{{ fine.visitor_name }} · #{{ fine.visitor_id }}</td><td>{{ fine.resource_name }} · #{{ fine.resource_id }}</td>
          <td>{{ fine.reason }}</td><td>${{ Number(fine.amount).toFixed(2) }}</td><td>{{ fine.date_issued }}</td><td>{{ fine.status }}</td>
          <td class="table-actions"><button v-if="fine.status === 'unpaid'" class="text-button" type="button" @click="confirmPayment(fine)">Confirm payment</button><button v-else class="text-button" type="button" @click="downloadReceipt(fine)">Receipt PDF</button></td>
        </tr></tbody>
      </table></div>
      <p v-else class="empty-state">No fines match this filter.</p>
    </section>

    <p v-if="error" class="banner bad ops-notice" role="alert">{{ error }}</p>
    <p v-if="notice" class="banner ok ops-notice" role="status">{{ notice }}</p>
  </div>
</template>
