<script setup>
import CheckForm from './CheckForm.vue'

defineProps({
  session: { type: Object, required: true },
})
</script>

<template>
  <section class="visitor-desk">
    <section class="ops-card">
      <div class="section-heading">
        <div>
          <h2>Returning visitor check-in</h2>
          <p class="sub">Check visitors in or out with their visitor ID.</p>
        </div>
      </div>
      <CheckForm :session="session" />
    </section>
  </section>
</template>
