<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { get, post, put, remove } from '../api'
import ReservationDesk from './ReservationDesk.vue'
import SalesDesk from './SalesDesk.vue'
import ReportsDesk from './ReportsDesk.vue'
import UserAccountsDesk from './UserAccountsDesk.vue'

const props = defineProps({
  session: { type: Object, required: true },
})
const emit = defineEmits(['sign-out'])
const isAdmin = computed(() => props.session.user.role === 'admin')
const activePanel = ref(isAdmin.value ? 'inventory' : 'reservations')
const panels = computed(() => isAdmin.value
  ? [
      { id: 'inventory', label: 'Inventory' },
      { id: 'reservations', label: 'Reservations' },
      { id: 'sales', label: 'Journal sales' },
      { id: 'reports', label: 'Reports' },
      { id: 'accounts', label: 'Staff accounts' },
    ]
  : [
      { id: 'reservations', label: 'Reservations' },
      { id: 'sales', label: 'Journal sales' },
    ])

const resourceTypes = [
  { value: 'book', label: 'Book' },
  { value: 'journal', label: 'Academic journal' },
  { value: 'archival', label: 'Archival item' },
  { value: 'room', label: 'Room' },
]
const resources = ref([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref(false)
const error = ref('')
const notice = ref('')
const search = ref('')
const statusForm = reactive({ resource_type: 'book', id: '', status: 'reserved', condition: 'good' })
const form = reactive({
  id: null,
  resource_type: 'book',
  name: '',
  author: '',
  price: '',
  genre: '',
  stock: '',
  capacity: '',
  status: 'available',
  condition: 'good',
})

const visibleResources = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return resources.value
  return resources.value.filter((resource) =>
    [resource.id, resource.name, resource.resource_type, resource.status, resource.condition]
      .some((value) => String(value ?? '').toLowerCase().includes(query)),
  )
})
const typeLabel = (type) => resourceTypes.find((item) => item.value === type)?.label || type

function resetForm() {
  Object.assign(form, {
    id: null,
    resource_type: 'book',
    name: '',
    author: '',
    price: '',
    genre: '',
    stock: '',
    capacity: '',
    status: 'available',
    condition: 'good',
  })
  editing.value = false
  showForm.value = false
}

async function loadInventory() {
  loading.value = true
  error.value = ''
  try {
    const { ok, status, data } = await get('/inventory/available', props.session.token)
    if (!ok) {
      if (status === 401) {
        error.value = 'Your sign-in has expired. Sign in again to continue.'
      } else {
        error.value = data.error || 'Could not load available resources.'
      }
      return
    }
    if (!Array.isArray(data.resources)) {
      error.value = 'The server returned an invalid inventory response.'
      return
    }
    resources.value = data.resources
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    loading.value = false
  }
}

function editResource(resource) {
  Object.assign(form, {
    id: resource.id,
    resource_type: resource.resource_type,
    name: resource.name || '',
    author: resource.author || '',
    price: resource.price ?? '',
    genre: resource.genre || '',
    stock: resource.stock ?? '',
    capacity: resource.capacity ?? '',
    status: resource.status || 'available',
    condition: resource.condition || 'good',
  })
  editing.value = true
  showForm.value = true
  error.value = ''
  notice.value = ''
}

function startCreate() {
  resetForm()
  showForm.value = true
}

function resourcePayload() {
  const data = { name: form.name.trim() }
  if (form.resource_type === 'book' || form.resource_type === 'journal') {
    data.author = form.author.trim()
    data.price = Number(form.price)
  }
  if (form.resource_type === 'book') data.genre = form.genre.trim()
  if (form.resource_type === 'journal') data.stock = Number(form.stock)
  if (form.resource_type === 'room') data.capacity = Number(form.capacity)
  if (editing.value) {
    data.status = form.status
    data.condition = form.condition
  }
  return data
}

function validateForm(data) {
  if (!data.name) return 'Enter a resource name.'
  if ((form.resource_type === 'book' || form.resource_type === 'journal') &&
      (!data.author || !Number.isFinite(data.price) || data.price < 0)) {
    return 'Enter an author and a valid non-negative price.'
  }
  if (form.resource_type === 'book' && !data.genre) return 'Enter a book genre.'
  if (form.resource_type === 'journal' && (!Number.isInteger(data.stock) || data.stock < 0)) {
    return 'Enter a valid non-negative stock quantity.'
  }
  if (form.resource_type === 'room' && (!Number.isInteger(data.capacity) || data.capacity < 1)) {
    return 'Enter a valid room capacity.'
  }
  return ''
}

async function saveResource() {
  error.value = ''
  notice.value = ''
  const data = resourcePayload()
  const validationError = validateForm(data)
  if (validationError) {
    error.value = validationError
    return
  }

  saving.value = true
  try {
    const url = editing.value
      ? `/inventory/${form.resource_type}/${form.id}`
      : '/inventory/add'
    const result = editing.value
      ? await put(url, { data }, props.session.token)
      : await post(url, { type: form.resource_type, data }, props.session.token)
    if (!result.ok) {
      error.value = result.data.error || 'Could not save this resource.'
      return
    }

    const resource = result.data[form.resource_type]
    if (!resource) {
      error.value = 'The server saved the resource but returned an invalid response.'
      return
    }
    if (resource.status === 'available' && resource.condition === 'good') {
      const index = resources.value.findIndex((item) =>
        item.resource_type === resource.resource_type && item.id === resource.id,
      )
      if (index === -1) resources.value.unshift(resource)
      else resources.value.splice(index, 1, resource)
    } else {
      resources.value = resources.value.filter((item) =>
        !(item.resource_type === resource.resource_type && item.id === resource.id),
      )
    }
    notice.value = editing.value
      ? (resource.status === 'available' && resource.condition === 'good'
        ? 'Resource updated.'
        : 'Resource updated and removed from the available inventory.')
      : 'Resource added to the inventory.'
    resetForm()
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  } finally {
    saving.value = false
  }
}

async function updateResourceStatus() {
  error.value = ''
  notice.value = ''
  const resourceId = Number(statusForm.id)
  if (!Number.isSafeInteger(resourceId) || resourceId <= 0) {
    error.value = 'Enter a valid resource ID.'
    return
  }
  try {
    const result = await put(
      `/inventory/${statusForm.resource_type}/${resourceId}`,
      { data: { status: statusForm.status, condition: statusForm.condition } },
      props.session.token,
    )
    if (!result.ok) {
      error.value = result.data.error || 'Could not update this resource.'
      return
    }
    const resource = result.data[statusForm.resource_type]
    if (resource?.status === 'available' && resource?.condition === 'good') {
      const index = resources.value.findIndex((item) => item.resource_type === resource.resource_type && item.id === resource.id)
      if (index === -1) resources.value.unshift(resource)
      else resources.value.splice(index, 1, resource)
    } else {
      resources.value = resources.value.filter((item) => !(item.resource_type === statusForm.resource_type && item.id === resourceId))
    }
    notice.value = `${resource?.name || `Resource #${resourceId}`} status and condition updated.`
    statusForm.id = ''
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

async function deleteResource(resource) {
  const label = `${resource.name} (ID ${resource.id})`
  if (!window.confirm(`Delete ${label}? This action cannot be undone.`)) return

  error.value = ''
  notice.value = ''
  try {
    const { ok, status, data } = await remove(
      `/inventory/${resource.resource_type}/${resource.id}`,
      props.session.token,
    )
    if (!ok) {
      error.value = status === 409
        ? 'This resource has an active reservation and cannot be deleted.'
        : data.error || 'Could not delete this resource.'
      return
    }
    resources.value = resources.value.filter((item) =>
      !(item.resource_type === resource.resource_type && item.id === resource.id),
    )
    notice.value = 'Resource deleted.'
  } catch (requestError) {
    error.value = requestError.message || 'Could not reach the server.'
  }
}

onMounted(() => { if (isAdmin.value) loadInventory() })
</script>

<template>
  <main class="admin-page">
    <header class="admin-header">
      <a class="admin-brand" href="/" aria-label="SALISES visitor centre">
        <img src="/salises-logo.jpg" alt="SALISES - The University of the West Indies" />
      </a>
      <div class="admin-user">
        <span>{{ session.user.name }}</span>
        <button class="btn ghost sign-out" type="button" @click="emit('sign-out')">Sign out</button>
      </div>
    </header>

    <section class="dashboard-content">
      <nav class="dashboard-nav" aria-label="Staff tools">
        <button v-for="panel in panels" :key="panel.id" type="button"
          :class="{ active: activePanel === panel.id }" @click="activePanel = panel.id">
          {{ panel.label }}
        </button>
      </nav>

      <div v-if="activePanel === 'inventory'" class="dashboard-panel">
      <div class="dashboard-heading">
        <div>
          <p class="eyebrow">{{ isAdmin ? 'Administrator portal' : 'Staff portal' }}</p>
          <h1>Resource inventory</h1>
          <p class="sub">Manage SALISES books, journals, archival items, and rooms.</p>
        </div>
        <button class="btn add-resource" type="button" @click="startCreate">
          Add resource
        </button>
      </div>

      <section class="inventory-summary" aria-label="Inventory summary">
        <div class="summary-card">
          <span class="summary-label">Available resources</span>
          <strong>{{ resources.length }}</strong>
          <span class="summary-caption">In good condition</span>
        </div>
      </section>

      <section v-if="showForm" class="resource-form-card">
        <div class="section-heading">
          <div>
            <h2>{{ editing ? 'Edit resource' : 'Add a resource' }}</h2>
            <p class="sub">The resource ID is assigned by the system.</p>
          </div>
          <button class="text-button" type="button" @click="resetForm">Cancel</button>
        </div>
        <form class="resource-form" @submit.prevent="saveResource">
          <label>
            Category
            <select v-model="form.resource_type" :disabled="editing">
              <option v-for="type in resourceTypes" :key="type.value" :value="type.value">
                {{ type.label }}
              </option>
            </select>
          </label>
          <label>
            Name
            <input v-model="form.name" required maxlength="200" />
          </label>
          <template v-if="form.resource_type === 'book' || form.resource_type === 'journal'">
            <label>
              Author
              <input v-model="form.author" required maxlength="200" />
            </label>
            <label>
              Price
              <input v-model="form.price" type="number" min="0" step="0.01" required />
            </label>
          </template>
          <label v-if="form.resource_type === 'book'">
            Genre
            <input v-model="form.genre" required maxlength="100" />
          </label>
          <label v-if="form.resource_type === 'journal'">
            Stock
            <input v-model="form.stock" type="number" min="0" step="1" required />
          </label>
          <label v-if="form.resource_type === 'room'">
            Capacity
            <input v-model="form.capacity" type="number" min="1" step="1" required />
          </label>
          <template v-if="editing">
            <label>
              Status
              <select v-model="form.status">
                <option value="available">Available</option>
                <option value="reserved">Reserved</option>
              </select>
            </label>
            <label>
              Condition
              <select v-model="form.condition">
                <option value="good">Good</option>
                <option value="lost">Lost</option>
                <option value="damaged">Damaged</option>
              </select>
            </label>
          </template>
          <div class="resource-form-actions">
            <button class="btn" type="submit" :disabled="saving">
              {{ saving ? 'Saving…' : editing ? 'Save changes' : 'Add resource' }}
            </button>
          </div>
        </form>
      </section>

      <div v-if="error" class="banner bad dashboard-message" role="alert">{{ error }}</div>
      <div v-if="notice" class="banner ok dashboard-message" role="status">{{ notice }}</div>

      <section class="inventory-card">
        <div class="section-heading inventory-toolbar">
          <div>
            <h2>Available inventory</h2>
            <p class="sub">Resources with Available status and Good condition.</p>
          </div>
          <div class="inventory-actions">
            <input v-model="search" class="inventory-search" type="search" placeholder="Search inventory" aria-label="Search inventory" />
            <button class="btn ghost refresh-button" type="button" :disabled="loading" @click="loadInventory">
              {{ loading ? 'Refreshing…' : 'Refresh' }}
            </button>
          </div>
        </div>
        <div v-if="loading && resources.length === 0" class="empty-state">Loading inventory…</div>
        <div v-else-if="visibleResources.length === 0" class="empty-state">
          {{ search ? 'No matching resources found.' : 'No available resources found.' }}
        </div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Resource</th>
                <th scope="col">Category</th>
                <th scope="col">Status</th>
                <th scope="col">Condition</th>
                <th scope="col"><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="resource in visibleResources" :key="`${resource.resource_type}-${resource.id}`">
                <td>#{{ resource.id }}</td>
                <td class="resource-name">{{ resource.name }}</td>
                <td>{{ typeLabel(resource.resource_type) }}</td>
                <td><span class="status-tag" :class="resource.status">{{ resource.status }}</span></td>
                <td>{{ resource.condition }}</td>
                <td>
                  <div class="table-actions">
                    <button class="text-button" type="button" @click="editResource(resource)">Edit</button>
                    <button class="text-button danger-link" type="button" @click="deleteResource(resource)">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="resource-form-card status-lookup-card">
        <div class="section-heading">
          <div><h2>Update resource status</h2><p class="sub">Use the resource ID to change its availability or condition.</p></div>
        </div>
        <form class="ops-form" @submit.prevent="updateResourceStatus">
          <label>Resource type<select v-model="statusForm.resource_type"><option v-for="type in resourceTypes" :key="type.value" :value="type.value">{{ type.label }}</option></select></label>
          <label>Resource ID<input v-model="statusForm.id" type="number" min="1" step="1" required /></label>
          <label>Status<select v-model="statusForm.status"><option value="available">Available</option><option value="reserved">Reserved</option></select></label>
          <label>Condition<select v-model="statusForm.condition"><option value="good">Good</option><option value="lost">Lost</option><option value="damaged">Damaged</option></select></label>
          <button class="btn" type="submit">Save status</button>
        </form>
      </section>
      </div>

      <ReservationDesk v-else-if="activePanel === 'reservations'" :session="session" />
      <SalesDesk v-else-if="activePanel === 'sales'" :session="session" />
      <ReportsDesk v-else-if="activePanel === 'reports'" :session="session" />
      <UserAccountsDesk v-else-if="activePanel === 'accounts'" :session="session" />
    </section>
  </main>
</template>
