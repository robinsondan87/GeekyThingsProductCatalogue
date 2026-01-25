<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
  const eventNameInput = document.getElementById('eventName')
  const eventDateInput = document.getElementById('eventDate')
  const eventLocationInput = document.getElementById('eventLocation')
  const eventContactNameInput = document.getElementById('eventContactName')
  const eventContactEmailInput = document.getElementById('eventContactEmail')
  const eventNotesInput = document.getElementById('eventNotes')
  const eventStatus = document.getElementById('eventStatus')
  const eventSaveBtn = document.getElementById('eventSaveBtn')
  const eventCancelBtn = document.getElementById('eventCancelBtn')
  const eventList = document.getElementById('eventList')
  const eventSalesSelect = document.getElementById('eventSalesSelect')
  const salesEventName = document.getElementById('salesEventName')
  const salesBody = document.getElementById('salesTableBody')
  const salesEmpty = document.getElementById('salesEmpty')
  const salesStatus = document.getElementById('salesStatus')
  const logoutBtn = document.getElementById('logoutBtn')

  let events = []
  let editingEventId = null

  const setStatus = (el, message) => {
    el.textContent = message
  }

  const formatEventDate = (value) => {
    if (!value) return ''
    return value
  }

  const isUpcoming = (value) => {
    if (!value) return false
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const eventDate = new Date(value)
    return eventDate >= today
  }

  const resetEventForm = () => {
    editingEventId = null
    eventNameInput.value = ''
    eventDateInput.value = ''
    eventLocationInput.value = ''
    eventContactNameInput.value = ''
    eventContactEmailInput.value = ''
    eventNotesInput.value = ''
    eventSaveBtn.textContent = 'Create Event'
    eventCancelBtn.hidden = true
  }

  const fillEventForm = (event) => {
    editingEventId = event.id
    eventNameInput.value = event.name || ''
    eventDateInput.value = event.event_date || ''
    eventLocationInput.value = event.location || ''
    eventContactNameInput.value = event.contact_name || ''
    eventContactEmailInput.value = event.contact_email || ''
    eventNotesInput.value = event.notes || ''
    eventSaveBtn.textContent = 'Update Event'
    eventCancelBtn.hidden = false
  }

  const renderEventList = () => {
    eventList.innerHTML = ''
    if (!events.length) {
      eventList.textContent = 'No events yet.'
      return
    }
    events.forEach((event) => {
      const item = document.createElement('div')
      item.className = 'folder-item'

      const meta = document.createElement('div')
      const title = document.createElement('div')
      title.className = 'folder-title'
      title.textContent = event.name || '(untitled)'
      const date = document.createElement('div')
      date.className = 'folder-meta'
      date.textContent = `${formatEventDate(event.event_date)} · ${event.location || 'No location'}`
      const contact = document.createElement('div')
      contact.className = 'folder-meta'
      const contactParts = []
      if (event.contact_name) contactParts.push(event.contact_name)
      if (event.contact_email) contactParts.push(event.contact_email)
      contact.textContent = contactParts.length ? contactParts.join(' · ') : 'No contact info'
      const status = document.createElement('div')
      status.className = 'folder-meta'
      status.textContent = isUpcoming(event.event_date) ? 'Upcoming' : 'Past'

      meta.appendChild(title)
      meta.appendChild(date)
      meta.appendChild(contact)
      meta.appendChild(status)

      const actions = document.createElement('div')
      actions.className = 'row-actions'

      const selectBtn = document.createElement('button')
      selectBtn.type = 'button'
      selectBtn.className = 'btn ghost'
      selectBtn.textContent = 'Use'
      selectBtn.addEventListener('click', () => {
        window.location.href = `/event?event_id=${encodeURIComponent(event.id)}`
      })

      const editBtn = document.createElement('button')
      editBtn.type = 'button'
      editBtn.className = 'btn ghost'
      editBtn.textContent = 'Edit'
      editBtn.addEventListener('click', () => {
        fillEventForm(event)
        eventNameInput.focus()
      })

      const deleteBtn = document.createElement('button')
      deleteBtn.type = 'button'
      deleteBtn.className = 'btn ghost'
      deleteBtn.textContent = 'Delete'
      deleteBtn.addEventListener('click', async () => {
        if (!confirm('Delete this event? Sales tied to it will be removed.')) return
        await deleteEvent(event.id)
      })

      actions.appendChild(selectBtn)
      actions.appendChild(editBtn)
      actions.appendChild(deleteBtn)

      item.appendChild(meta)
      item.appendChild(actions)
      eventList.appendChild(item)
    })
  }

  const renderSalesSelect = () => {
    const current = eventSalesSelect.value
    eventSalesSelect.innerHTML = '<option value="">Select event</option>'
    events.forEach((event) => {
      const option = document.createElement('option')
      option.value = event.id
      option.textContent = `${event.name} (${formatEventDate(event.event_date)})`
      eventSalesSelect.appendChild(option)
    })
    if (current && [...eventSalesSelect.options].some((option) => option.value === current)) {
      eventSalesSelect.value = current
      return
    }
    if (events.length) {
      eventSalesSelect.value = events[0].id
    }
  }

  const loadEvents = async () => {
    const response = await fetch('/api/events', { cache: 'no-store' })
    if (!response.ok) {
      setStatus(eventStatus, 'Failed to load events.')
      return
    }
    const payload = await response.json()
    events = payload.events || []
    renderEventList()
    renderSalesSelect()
    await loadEventSales()
  }

  const saveEvent = async () => {
    const payload = {
      name: eventNameInput.value.trim(),
      event_date: eventDateInput.value.trim(),
      location: eventLocationInput.value.trim(),
      contact_name: eventContactNameInput.value.trim(),
      contact_email: eventContactEmailInput.value.trim(),
      notes: eventNotesInput.value.trim(),
    }
    if (!payload.name || !payload.event_date) {
      setStatus(eventStatus, 'Event name and date are required.')
      return
    }
    const body = editingEventId
      ? { action: 'update', id: editingEventId, event: payload }
      : { action: 'create', event: payload }
    const response = await fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(eventStatus, data.error || 'Failed to save event.')
      return
    }
    setStatus(eventStatus, editingEventId ? 'Event updated.' : 'Event created.')
    resetEventForm()
    await loadEvents()
  }

  const deleteEvent = async (eventId) => {
    const response = await fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id: eventId }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(eventStatus, data.error || 'Failed to delete event.')
      return
    }
    await loadEvents()
  }

  const loadEventSales = async () => {
    const eventId = eventSalesSelect.value
    if (!eventId) {
      salesBody.innerHTML = ''
      salesEmpty.hidden = false
      salesEventName.textContent = 'Select an event to view sales.'
      return
    }
    const eventMatch = events.find((event) => String(event.id) === String(eventId))
    salesEventName.textContent = eventMatch
      ? `${eventMatch.name} · ${formatEventDate(eventMatch.event_date)}`
      : 'Event sales'
    const response = await fetch(`/api/sales?event_id=${encodeURIComponent(eventId)}`)
    if (!response.ok) {
      setStatus(salesStatus, 'Failed to load sales.')
      return
    }
    const payload = await response.json()
    const rows = payload.rows || []
    salesBody.innerHTML = ''
    if (!rows.length) {
      salesEmpty.hidden = false
      return
    }
    salesEmpty.hidden = true
    rows.forEach((row) => {
      const tr = document.createElement('tr')

      const whenCell = document.createElement('td')
      const when = new Date(row.sold_at)
      whenCell.textContent = Number.isNaN(when.getTime()) ? row.sold_at : when.toLocaleString()

      const productCell = document.createElement('td')
      productCell.textContent = row.sku ? `${row.sku} · ${row.product_folder}` : row.product_folder

      const variationCell = document.createElement('td')
      const variationParts = [row.color, row.size].filter(Boolean)
      variationCell.textContent = variationParts.length ? variationParts.join(' / ') : '—'

      const qtyCell = document.createElement('td')
      qtyCell.textContent = row.quantity

      const priceCell = document.createElement('td')
      const unitPrice = parseFloat(row.unit_price || 0)
      priceCell.textContent = `${unitPrice.toFixed(2)} GBP`

      const paymentCell = document.createElement('td')
      paymentCell.textContent = row.payment_method || '—'

      const overrideCell = document.createElement('td')
      overrideCell.textContent = row.override_price || '—'

      tr.appendChild(whenCell)
      tr.appendChild(productCell)
      tr.appendChild(variationCell)
      tr.appendChild(qtyCell)
      tr.appendChild(priceCell)
      tr.appendChild(paymentCell)
      tr.appendChild(overrideCell)
      salesBody.appendChild(tr)
    })
  }

  eventSaveBtn.addEventListener('click', () => saveEvent().catch(console.error))
  eventCancelBtn.addEventListener('click', () => {
    resetEventForm()
    setStatus(eventStatus, '')
  })
  eventSalesSelect.addEventListener('change', () => {
    loadEventSales().catch(console.error)
  })

  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' })
    window.location.href = '/login'
  })

  resetEventForm()
  loadEvents().catch(console.error)
})
</script>

<template>
  <header>
    <nav class="nav">
      <div class="nav-brand">
        <img src="/logo.png" alt="Geeky Things logo" />
        <strong>GeekyThings</strong>
      </div>
      <div class="nav-center">
        <h1 class="title">Events</h1>
        <p class="subtitle">Manage craft fair events and review sales.</p>
        <p class="version">
          Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
        </p>
      </div>
      <div class="nav-links">
        <RouterLink to="/">Products</RouterLink>
        <RouterLink to="/stock">Stock</RouterLink>
        <RouterLink to="/production">Production</RouterLink>
        <RouterLink to="/events">Events</RouterLink>
        <RouterLink to="/supplies">Supplies</RouterLink>
        <RouterLink to="/add">Add Product</RouterLink>
        <button class="ghost" id="logoutBtn" type="button">Logout</button>
      </div>
    </nav>
  </header>

  <main>
    <section class="card">
      <h2>Event details</h2>
      <div class="grid">
        <div>
          <label for="eventName">Event name</label>
          <input id="eventName" type="text" placeholder="e.g. Stafford Craft Fair" />
        </div>
        <div>
          <label for="eventDate">Event date</label>
          <input id="eventDate" type="date" />
        </div>
        <div>
          <label for="eventLocation">Location</label>
          <input id="eventLocation" type="text" placeholder="Town Hall, Stafford" />
        </div>
        <div>
          <label for="eventContactName">Contact name</label>
          <input id="eventContactName" type="text" placeholder="Organiser name" />
        </div>
        <div>
          <label for="eventContactEmail">Contact email</label>
          <input id="eventContactEmail" type="email" placeholder="organiser@email.com" />
        </div>
        <div>
          <label for="eventNotes">Notes</label>
          <input id="eventNotes" type="text" placeholder="Stall size, fee, parking, etc." />
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="eventSaveBtn" class="btn" type="button">Create Event</button>
        <button id="eventCancelBtn" class="btn ghost" type="button" hidden>Cancel edit</button>
      </div>
      <div class="status" id="eventStatus"></div>
    </section>

    <section class="card">
      <h2>Events</h2>
      <div class="folder-list" id="eventList"></div>
    </section>

    <section class="card">
      <h2>Event sales</h2>
      <div class="grid">
        <div>
          <label for="eventSalesSelect">Event</label>
          <select id="eventSalesSelect"></select>
        </div>
        <div>
          <label>Selected event</label>
          <div class="status" id="salesEventName">Select an event to view sales.</div>
        </div>
      </div>
      <div class="status" id="salesStatus"></div>
      <div class="table-wrap" style="margin-top: 12px;">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Product</th>
              <th>Variation</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Payment</th>
              <th>Override</th>
            </tr>
          </thead>
          <tbody id="salesTableBody"></tbody>
        </table>
        <div class="empty" id="salesEmpty">No sales recorded yet.</div>
      </div>
    </section>

  </main>
</template>
