<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { get, post } from '../api'

const props = defineProps({ session: { type: Object, required: true } })
const isAdmin = computed(() => props.session.user.role === 'admin')
const reservationTypes = [
  { value: 'room', label: 'Room' },
  { value: 'archival', label: 'Archival item' },
  { value: 'book', label: 'Book' },
]
const resources = ref([])
const reservations = ref([])
const recentRequests = ref([])
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const notice = ref('')
const today = new Date()
const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const form = reactive({
  type: 'room', visitor_id: '', resource_id: '', reserve_date: todayText,
  start_time: '09:00', end_time: '10:00', occupants: 1, expected_return: todayText,
})
const actionForm = reactive({ id: '', action: 'cancel', actual_return: todayText })
const selectedResource = computed(() => resources.value.find((item) => String(item.id) === String(form.resource_id)))

async function loadResources() {
  form.resource_id = ''
  try {
    const result = await get(`/inventory/available?type=${form.type}`)
    resources.value = result.ok ? result.data.resources || [] : []
  } catch {
    resources.value = []
  }
}

async function loadReservations() {
  if (!isAdmin.value) return
  loading.value = true
  error.value = ''
  try {
    const result = await post('/reports/generate', {
      report_type: 'reservation', start_date: '2000-01-01', end_date: todayText,
    }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not load reservation requests.'
      return
    }
    reservations.value = result.data.records || []
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    loading.value = false
  }
}

async function submitRequest() {
  error.value = ''
  notice.value = ''
  const data = { visitor_id: Number(form.visitor_id), resource_id: Number(form.resource_id) }
  if (form.type === 'book') data.expected_return = form.expected_return
  else Object.assign(data, {
    reserve_date: form.reserve_date,
    start_time: form.start_time,
    end_time: form.end_time,
    ...(form.type === 'room' ? { occupants: Number(form.occupants) } : {}),
  })

  busy.value = true
  try {
    const result = await post(`/reservations/${form.type}`, data, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not submit the reservation request.'
      return
    }
    notice.value = `Reservation request #${result.data.reservation.id} was submitted for administrator review.`
    const recent = {
      ...result.data.reservation,
      visitor_name: result.data.visitor.name,
      resource_name: result.data.resource.name,
    }
    recentRequests.value = [...recentRequests.value.filter((item) => item.id !== recent.id), recent].slice(-20)
    sessionStorage.setItem('centralis-recent-reservations', JSON.stringify(recentRequests.value))
    form.visitor_id = ''
    if (isAdmin.value) await loadReservations()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    busy.value = false
  }
}

async function reviewRequest(reservation, decision) {
  error.value = ''
  notice.value = ''
  try {
    const result = await post(`/reservations/${reservation.id}/${decision}`, {}, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || `Could not ${decision} this request.`
      return
    }
    notice.value = `Reservation #${reservation.id} ${decision}d.`
    await loadReservations()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

async function updateExisting() {
  error.value = ''
  notice.value = ''
  const id = Number(actionForm.id)
  if (!Number.isSafeInteger(id) || id <= 0) {
    error.value = 'Enter a valid reservation ID.'
    return
  }
  const path = actionForm.action === 'return'
    ? `/reservations/${id}/return`
    : `/reservations/${id}/cancel`
  const body = actionForm.action === 'return' ? { actual_return: actionForm.actual_return } : {}
  try {
    const result = await post(path, body, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not update this reservation.'
      return
    }
    notice.value = actionForm.action === 'return'
      ? `Book reservation #${id} marked as returned.`
      : `Reservation #${id} cancelled.`
    recentRequests.value = recentRequests.value.map((item) => item.id === id
      ? { ...item, status: actionForm.action === 'return' ? 'returned' : 'cancelled', actual_return: body.actual_return }
      : item)
    sessionStorage.setItem('centralis-recent-reservations', JSON.stringify(recentRequests.value))
    actionForm.id = ''
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

watch(() => form.type, loadResources)
onMounted(() => {
  loadResources()
  loadReservations()
  if (!isAdmin.value) {
    try { recentRequests.value = JSON.parse(sessionStorage.getItem('centralis-recent-reservations') || '[]') }
    catch { recentRequests.value = [] }
  }
})
</script>

<template>
  <div class="ops-grid">
    <section v-if="!isAdmin && recentRequests.length" class="ops-card ops-span">
      <div class="section-heading"><div><h2>Requests from the visitor desk</h2><p class="sub">Reservation requests submitted by this staff session.</p></div></div>
      <div class="table-wrap ops-table-wrap"><table>
        <thead><tr><th>Request</th><th>Visitor</th><th>Resource</th><th>Requested</th><th>Status</th></tr></thead>
        <tbody><tr v-for="item in [...recentRequests].reverse()" :key="item.id">
          <td>#{{ item.id }}</td><td>{{ item.visitor_name || `Visitor #${item.visitor_id}` }}</td><td>{{ item.resource_name || `Resource #${item.resource_id}` }}</td><td>{{ item.request_date }}</td><td>{{ item.status }}</td>
        </tr></tbody>
      </table></div>
    </section>
    <section v-if="!isAdmin" class="ops-card">
      <div class="section-heading"><div><h2>Submit a resource request</h2><p class="sub">Requests are sent to an administrator for approval.</p></div></div>
      <form class="ops-form reservation-form" @submit.prevent="submitRequest">
        <label>Reservation type
          <select v-model="form.type"><option v-for="type in reservationTypes" :key="type.value" :value="type.value">{{ type.label }}</option></select>
        </label>
        <label>Visitor ID<input v-model="form.visitor_id" type="number" min="1" step="1" required /></label>
        <label>Resource
          <select v-if="resources.length" v-model="form.resource_id" required>
            <option value="" disabled>Choose an available resource</option>
            <option v-for="resource in resources" :key="resource.id" :value="String(resource.id)">{{ resource.name }}{{ resource.capacity ? ` · capacity ${resource.capacity}` : '' }}</option>
          </select>
          <input v-else v-model="form.resource_id" type="number" min="1" step="1" required placeholder="Available resource ID" />
        </label>
        <template v-if="form.type === 'book'"><label>Expected return<input v-model="form.expected_return" type="date" :min="todayText" required /></label></template>
        <template v-else>
          <label>Reservation date<input v-model="form.reserve_date" type="date" :min="todayText" required /></label>
          <label>Start time<input v-model="form.start_time" type="time" min="08:30" max="16:30" required /></label>
          <label>End time<input v-model="form.end_time" type="time" min="08:30" max="16:30" required /></label>
          <label v-if="form.type === 'room'">Occupants<input v-model.number="form.occupants" type="number" min="1" :max="selectedResource?.capacity" step="1" required /></label>
        </template>
        <p v-if="selectedResource?.capacity && form.type === 'room'" class="field-hint">This room accommodates up to {{ selectedResource.capacity }} people.</p>
        <button class="btn" type="submit" :disabled="busy">{{ busy ? 'Submitting…' : 'Submit request' }}</button>
      </form>
    </section>

    <section v-if="!isAdmin" class="ops-card">
      <div class="section-heading"><div><h2>Update a request</h2><p class="sub">Use the reservation ID shown when the request was submitted.</p></div></div>
      <form class="ops-form" @submit.prevent="updateExisting">
        <label>Reservation ID<input v-model="actionForm.id" type="number" min="1" step="1" required /></label>
        <label>Action<select v-model="actionForm.action"><option value="cancel">Cancel room or archival request</option><option value="return">Record book return</option></select></label>
        <label v-if="actionForm.action === 'return'">Actual return date<input v-model="actionForm.actual_return" type="date" required /></label>
        <button class="btn" type="submit">{{ actionForm.action === 'return' ? 'Record return' : 'Cancel request' }}</button>
      </form>
    </section>

    <section v-else class="ops-card">
      <div class="section-heading"><div><h2>Reservation requests</h2><p class="sub">Review pending requests submitted by staff.</p></div><button class="btn ghost refresh-button" type="button" :disabled="loading" @click="loadReservations">{{ loading ? 'Refreshing…' : 'Refresh' }}</button></div>
      <div v-if="reservations.length" class="table-wrap ops-table-wrap"><table>
        <thead><tr><th>Request</th><th>Visitor</th><th>Resource</th><th>Requested</th><th>Status</th><th>Review</th></tr></thead>
        <tbody><tr v-for="item in [...reservations].reverse()" :key="item.id">
          <td>#{{ item.id }}</td><td>#{{ item.visitor_id }}</td><td>#{{ item.resource_id }}</td><td>{{ item.request_date }}</td><td>{{ item.status }}</td>
          <td class="table-actions"><template v-if="item.status === 'pending'"><button class="text-button" type="button" @click="reviewRequest(item, 'approve')">Approve</button><button class="text-button danger-link" type="button" @click="reviewRequest(item, 'decline')">Decline</button></template><span v-else>—</span></td>
        </tr></tbody>
      </table></div>
      <p v-else-if="!loading" class="empty-state">No reservation requests found for the report period.</p>
    </section>
    <p v-if="error" class="banner bad ops-notice" role="alert">{{ error }}</p>
    <p v-if="notice" class="banner ok ops-notice" role="status">{{ notice }}</p>
  </div>
</template>
