<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { get, post } from '../api'

const props = defineProps({ session: { type: Object, required: true } })
const journals = ref([])
const sales = ref([])
const error = ref('')
const notice = ref('')
const busy = ref(false)
const today = new Date()
const form = reactive({ journal_id: '', quantity: 1, date_sold: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}` })
const selectedJournal = computed(() => journals.value.find((item) => String(item.id) === String(form.journal_id)))

async function loadData() {
  error.value = ''
  try {
    const [journalResult, salesResult] = await Promise.all([
      get('/inventory/available?type=journal'),
      get('/sales', props.session.token),
    ])
    if (!journalResult.ok) throw new Error(journalResult.data.error || 'Could not load journals.')
    if (!salesResult.ok) throw new Error(salesResult.data.error || 'Could not load sales.')
    journals.value = journalResult.data.resources || []
    sales.value = salesResult.data.sales || []
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

async function recordSale() {
  error.value = ''
  notice.value = ''
  busy.value = true
  let createdSale = null
  try {
    const result = await post('/sales', {
      journal_id: Number(form.journal_id),
      quantity: Number(form.quantity),
      date_sold: form.date_sold,
    }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not record the sale.'
      return
    }
    const sale = result.data.sale
    createdSale = sale
    const paymentResult = await post(`/sales/${sale.id}/confirm-payment`, {}, props.session.token)
    if (!paymentResult.ok) {
      notice.value = `Sale #${sale.id} was recorded, but payment could not be confirmed. You can retry from Recent sales.`
      form.quantity = 1
      await loadData()
      error.value = paymentResult.data.error || 'Payment confirmation failed.'
      return
    }
    notice.value = `Sale #${sale.id} recorded and payment confirmed.`
    form.quantity = 1
    await loadData()
  } catch (requestError) {
    if (createdSale) {
      notice.value = `Sale #${createdSale.id} was recorded, but payment confirmation could not be completed. You can retry from Recent sales.`
      await loadData()
      error.value = requestError.message || 'Payment confirmation failed.'
    } else {
      error.value = requestError.message || 'Could not reach the server.'
    }
  } finally {
    busy.value = false
  }
}

async function confirmPayment(sale) {
  error.value = ''
  notice.value = ''
  try {
    const result = await post(`/sales/${sale.id}/confirm-payment`, {}, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not confirm payment.'
      return
    }
    notice.value = `Payment confirmed for sale #${sale.id}.`
    await loadData()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

async function downloadReceipt(sale) {
  error.value = ''
  try {
    const response = await fetch(`/sales/${sale.id}/receipt`, {
      headers: { Authorization: `Bearer ${props.session.token}` },
    })
    if (!response.ok) {
      const data = await response.json()
      error.value = data.error || 'Could not create the receipt.'
      return
    }
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `receipt-${sale.id}.pdf`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

onMounted(loadData)
</script>

<template>
  <section class="ops-grid">
    <section class="ops-card">
      <div class="section-heading"><div><h2>Record a journal sale</h2><p class="sub">Record the sale once payment has been received through SALISES channels.</p></div></div>
      <form class="ops-form sales-form" @submit.prevent="recordSale">
        <label>Journal
          <select v-model="form.journal_id" required>
            <option value="" disabled>Choose a journal</option>
            <option v-for="journal in journals" :key="journal.id" :value="String(journal.id)">
              {{ journal.name }} · {{ journal.stock }} in stock · ${{ Number(journal.price).toFixed(2) }}
            </option>
          </select>
        </label>
        <label>Quantity<input v-model.number="form.quantity" type="number" min="1" :max="selectedJournal?.stock" step="1" required /></label>
        <label>Date sold<input v-model="form.date_sold" type="date" required /></label>
        <p v-if="selectedJournal" class="sales-total">Total: ${{ (Number(form.quantity || 0) * Number(selectedJournal.price)).toFixed(2) }}</p>
        <button class="btn" type="submit" :disabled="busy || !journals.length">{{ busy ? 'Saving…' : 'Record sale' }}</button>
      </form>
      <p v-if="!journals.length" class="empty-state">No available journals are listed.</p>
    </section>

    <section class="ops-card">
      <div class="section-heading"><div><h2>Recent sales</h2><p class="sub">Review payment status and issue receipts from here.</p></div><button class="btn ghost refresh-button" type="button" @click="loadData">Refresh</button></div>
      <p v-if="error" class="banner bad" role="alert">{{ error }}</p>
      <p v-if="notice" class="banner ok" role="status">{{ notice }}</p>
      <div v-if="sales.length" class="table-wrap ops-table-wrap"><table>
        <thead><tr><th>Sale</th><th>Journal</th><th>Qty</th><th>Total</th><th>Date</th><th>Payment</th><th>Actions</th></tr></thead>
        <tbody><tr v-for="sale in [...sales].reverse()" :key="sale.id">
          <td>#{{ sale.id }}</td><td>{{ sale.journal_name || `Journal #${sale.journal_id}` }}</td><td>{{ sale.quantity }}</td><td>${{ Number(sale.sale_amount).toFixed(2) }}</td><td>{{ sale.date_sold }}</td>
          <td>{{ sale.payment_confirmed ? 'Confirmed' : 'Pending' }}</td><td class="table-actions">
            <button v-if="!sale.payment_confirmed" class="text-button" type="button" @click="confirmPayment(sale)">Confirm payment</button>
            <button v-else class="text-button" type="button" @click="downloadReceipt(sale)">Receipt PDF</button>
          </td>
        </tr></tbody>
      </table></div>
      <p v-else class="empty-state">No sales have been recorded.</p>
    </section>
  </section>
</template>
