<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { get } from '../api'

const props = defineProps({
  modelValue: { type: String, default: '' },
  staffAuthenticated: { type: Boolean, default: false },
  initialReservation: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

const reasons = [
  { value: 'research', label: 'Research' },
  { value: 'study', label: 'Reading or study' },
  { value: 'consultation', label: 'Consultation' },
  { value: 'meeting', label: 'Meeting' },
  { value: 'reservation', label: 'Make a reservation' },
  { value: 'other', label: 'Other' },
]
const reservationTypes = [
  { value: 'room', label: 'Room reservation' },
  { value: 'archival', label: 'Archival item request' },
  { value: 'book', label: 'Book borrowing' },
]
const reason = ref('research')
const details = ref('')
const reservationType = ref('room')
const resources = ref([])
const resourceLoading = ref(false)
const validationError = ref('')
const today = new Date()
const minDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const reservation = reactive({
  resource_id: '',
  reserve_date: '',
  start_time: '',
  end_time: '',
  occupants: '',
  expected_return: '',
})
let hydrating = true

const selectedResource = computed(() => resources.value.find(
  (resource) => String(resource.id) === String(reservation.resource_id),
))
const composedPurpose = computed(() => {
  if (reason.value === 'other') return details.value.trim()
  if (reason.value !== 'reservation') {
    const label = reasons.find((item) => item.value === reason.value)?.label || ''
    return details.value.trim() ? `${label}: ${details.value.trim()}` : label
  }

  const typeLabel = reservationTypes.find((item) => item.value === reservationType.value)?.label
  const resourceName = selectedResource.value?.name || (reservation.resource_id ? `#${reservation.resource_id}` : '')
  const lines = [`${typeLabel} request`, `Resource: ${resourceName}`]
  if (reservationType.value === 'book') {
    if (reservation.expected_return) lines.push(`Expected return: ${reservation.expected_return}`)
  } else {
    if (reservation.reserve_date) lines.push(`Date: ${reservation.reserve_date}`)
    if (reservation.start_time && reservation.end_time) {
      lines.push(`Time: ${reservation.start_time}–${reservation.end_time}`)
    }
    if (reservationType.value === 'room' && reservation.occupants) {
      lines.push(`Occupants: ${reservation.occupants}`)
    }
  }
  if (details.value.trim()) lines.push(`Notes: ${details.value.trim()}`)
  return lines.join(' | ')
})

watch(composedPurpose, (value) => {
  if (!hydrating) emit('update:modelValue', value)
})

watch([reason, reservationType, reservation], () => {
  validationError.value = ''
}, { deep: true })

function validate() {
  validationError.value = ''
  if (reason.value !== 'reservation') return true
  if (!props.staffAuthenticated) {
    validationError.value = 'A SALISES staff member must sign in before submitting a reservation.'
    return false
  }
  if (!reservation.resource_id) {
    validationError.value = 'Choose an available resource.'
    return false
  }
  if (reservation.reserve_date) {
    const weekday = new Date(`${reservation.reserve_date}T12:00:00`).getDay()
    if (weekday === 0 || weekday === 6) {
      validationError.value = 'Room and archival requests must be for a weekday.'
      return false
    }
  }
  if (reservation.start_time && reservation.end_time && reservation.start_time >= reservation.end_time) {
    validationError.value = 'End time must be later than start time.'
    return false
  }
  if (reservationType.value === 'room' && selectedResource.value?.capacity && reservation.occupants &&
      Number(reservation.occupants) > selectedResource.value.capacity) {
    validationError.value = `This room can hold up to ${selectedResource.value.capacity} occupants.`
    return false
  }
  return true
}

function getReservationData() {
  if (reason.value !== 'reservation') return null
  const data = { type: reservationType.value, resource_id: Number(reservation.resource_id) }
  if (reservationType.value === 'book') data.expected_return = reservation.expected_return
  else Object.assign(data, {
    reserve_date: reservation.reserve_date,
    start_time: reservation.start_time,
    end_time: reservation.end_time,
    ...(reservationType.value === 'room' ? { occupants: Number(reservation.occupants) } : {}),
  })
  return data
}

defineExpose({ validate, getReservationData })

watch(() => props.modelValue, (value) => {
  if (value === composedPurpose.value) return
  if (!value) {
    reason.value = 'research'
    details.value = ''
    Object.assign(reservation, {
      resource_id: '', reserve_date: '', start_time: '',
      end_time: '', occupants: '', expected_return: '',
    })
  } else {
    reason.value = 'other'
    details.value = value
  }
})

async function loadResources() {
  resources.value = []
  reservation.resource_id = ''
  resourceLoading.value = true
  try {
    const { ok, data } = await get(`/inventory/available?type=${reservationType.value}`)
    if (ok && Array.isArray(data.resources)) resources.value = data.resources
  } catch {
    // The free-text resource field remains available when inventory cannot load.
  } finally {
    resourceLoading.value = false
  }
}

watch(reservationType, loadResources)
onMounted(async () => {
  if (props.initialReservation) {
    reason.value = 'reservation'
    reservationType.value = props.initialReservation.type || 'room'
    await loadResources()
    Object.assign(reservation, props.initialReservation)
    details.value = props.initialReservation.notes || ''
  } else if (props.modelValue) {
    reason.value = 'other'
    details.value = props.modelValue
    await loadResources()
  } else await loadResources()
  hydrating = false
  if (!props.modelValue) emit('update:modelValue', composedPurpose.value)
})
</script>

<template>
  <div class="visit-purpose">
    <label>Reason for visit
      <select v-model="reason">
        <option v-for="item in reasons" :key="item.value" :value="item.value">{{ item.label }}</option>
      </select>
    </label>

    <template v-if="reason === 'reservation'">
      <div class="reservation-intake">
        <p class="reservation-intake-title">Reservation details</p>
        <label>What would you like to reserve?
          <select v-model="reservationType">
            <option v-for="item in reservationTypes" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </label>

        <label v-if="resources.length">Available resource
          <select v-model="reservation.resource_id" required>
            <option value="" disabled>{{ resourceLoading ? 'Loading resources…' : 'Choose a resource' }}</option>
            <option v-for="resource in resources" :key="resource.id" :value="String(resource.id)">
              {{ resource.name }}
            </option>
          </select>
        </label>
        <label v-else>Available resource ID
          <input v-model="reservation.resource_id" type="number" min="1" step="1" required placeholder="Enter the resource ID" />
        </label>

        <template v-if="reservationType === 'book'">
          <label>Expected return date
            <input v-model="reservation.expected_return" type="date" :min="minDate" required />
          </label>
        </template>
        <template v-else>
          <label>Reservation date
            <input v-model="reservation.reserve_date" type="date" :min="minDate" required />
          </label>
          <div class="row">
            <label>Start time
              <input v-model="reservation.start_time" type="time" min="08:30" max="16:30" required />
            </label>
            <label>End time
              <input v-model="reservation.end_time" type="time" min="08:30" max="16:30" required />
            </label>
          </div>
          <label v-if="reservationType === 'room'">Number of occupants
            <input v-model="reservation.occupants" type="number" min="1" step="1" required />
          </label>
        </template>

        <label>Additional details <small>(optional)</small>
          <textarea v-model="details" rows="2" maxlength="500" placeholder="Anything staff should know?" />
        </label>
        <p class="reservation-note">
          A staff member will submit this request for the visitor. It remains pending until an administrator reviews it.
        </p>
        <p v-if="validationError" class="err purpose-error" role="alert">{{ validationError }}</p>
      </div>
    </template>
    <label v-else-if="reason === 'other'">What are you visiting for?
      <textarea v-model="details" rows="2" maxlength="500" required placeholder="Tell us the reason for your visit" />
    </label>
    <label v-else>Additional details <small>(optional)</small>
      <input v-model="details" maxlength="200" placeholder="Add a little more detail" />
    </label>
  </div>
</template>
