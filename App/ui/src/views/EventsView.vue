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
  const eventSelect = document.getElementById('eventSelect')

  const productSearch = document.getElementById('productSearch')
  const productSelect = document.getElementById('productSelect')
  const colorSelect = document.getElementById('colorSelect')
  const sizeSelect = document.getElementById('sizeSelect')
  const qtyInput = document.getElementById('qtyInput')
  const paymentSelect = document.getElementById('paymentSelect')
  const defaultPriceInput = document.getElementById('defaultPrice')
  const overridePriceInput = document.getElementById('overridePrice')
  const totalPriceEl = document.getElementById('totalPrice')
  const saleStatus = document.getElementById('saleStatus')
  const recordSaleBtn = document.getElementById('recordSaleBtn')
  const salesBody = document.getElementById('salesTableBody')
  const salesEmpty = document.getElementById('salesEmpty')
  const logoutBtn = document.getElementById('logoutBtn')

  let events = []
  let editingEventId = null
  let products = []
  let productOptions = []
  const productsByKey = new Map()

  const buildKey = (category, folder) => `${category}|||${folder}`

  const parseList = (value) =>
    (value || '')
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length)

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

  const renderEventSelect = () => {
    const current = eventSelect.value
    eventSelect.innerHTML = '<option value="">Select event</option>'
    events.forEach((event) => {
      const option = document.createElement('option')
      option.value = event.id
      option.textContent = `${event.name} (${formatEventDate(event.event_date)})`
      eventSelect.appendChild(option)
    })
    if (current && [...eventSelect.options].some((option) => option.value === current)) {
      eventSelect.value = current
    }
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
        eventSelect.value = String(event.id)
        loadSales().catch(console.error)
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

  const loadEvents = async () => {
    const response = await fetch('/api/events', { cache: 'no-store' })
    if (!response.ok) {
      setStatus(eventStatus, 'Failed to load events.')
      return
    }
    const payload = await response.json()
    events = payload.events || []
    renderEventSelect()
    renderEventList()
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
    if (eventSelect.value === String(eventId)) {
      eventSelect.value = ''
      salesBody.innerHTML = ''
      salesEmpty.hidden = false
    }
    await loadEvents()
  }

  const renderProductOptions = (filter) => {
    const normalized = (filter || '').trim().toLowerCase()
    const current = productSelect.value
    productSelect.innerHTML = '<option value="">Select a product</option>'
    productOptions
      .filter((option) => option.label.toLowerCase().includes(normalized))
      .forEach((option) => {
        const el = document.createElement('option')
        el.value = option.key
        el.textContent = option.label
        productSelect.appendChild(el)
      })
    if (current && [...productSelect.options].some((option) => option.value === current)) {
      productSelect.value = current
    } else {
      productSelect.value = ''
    }
    refreshSuggestions()
  }

  const refreshSuggestions = () => {
    const selected = productsByKey.get(productSelect.value) || null
    const colors = selected ? parseList(selected.Colors) : []
    const sizes = selected ? parseList(selected.Sizes) : []

    const renderSelect = (selectEl, items, placeholder) => {
      const current = selectEl.value
      selectEl.innerHTML = ''
      const defaultOption = document.createElement('option')
      defaultOption.value = ''
      defaultOption.textContent = placeholder
      selectEl.appendChild(defaultOption)
      items
        .slice()
        .sort((a, b) => a.localeCompare(b))
        .forEach((item) => {
          const option = document.createElement('option')
          option.value = item
          option.textContent = item
          selectEl.appendChild(option)
        })
      if (current) {
        selectEl.value = current
      }
    }

    renderSelect(colorSelect, colors, colors.length ? 'Select color' : 'No colors set')
    renderSelect(sizeSelect, sizes, sizes.length ? 'Select size' : 'No sizes set')
    updatePricingDefaults(selected)
  }

  const updatePricingDefaults = (selected) => {
    const basePrice = selected ? parseFloat(selected['Sale Price'] || '0') : 0
    defaultPriceInput.value = Number.isFinite(basePrice) ? basePrice.toFixed(2) : '0.00'
    updateTotalPrice()
  }

  const getEffectivePrice = () => {
    const overrideValue = overridePriceInput.value.trim()
    if (!overrideValue) {
      return parseFloat(defaultPriceInput.value) || 0
    }
    const parsed = parseFloat(overrideValue)
    if (!Number.isFinite(parsed)) {
      return null
    }
    return parsed
  }

  const updateTotalPrice = () => {
    const qty = parseInt(qtyInput.value, 10) || 0
    const price = getEffectivePrice()
    if (price == null) {
      totalPriceEl.textContent = 'Total: invalid override'
      return
    }
    totalPriceEl.textContent = `Total: ${(price * qty).toFixed(2)} GBP`
  }

  const loadProducts = async () => {
    const response = await fetch('/api/rows', { cache: 'no-store' })
    if (!response.ok) {
      setStatus(saleStatus, 'Failed to load products.')
      return
    }
    const payload = await response.json()
    products = payload.rows || []
    productsByKey.clear()
    productOptions = []
    const sorted = [...products].sort((a, b) => {
      const keyA = `${a.category} ${a.product_folder}`.toLowerCase()
      const keyB = `${b.category} ${b.product_folder}`.toLowerCase()
      return keyA.localeCompare(keyB)
    })
    sorted.forEach((row) => {
      const category = row.category || ''
      const folder = row.product_folder || ''
      if (!category || !folder) return
      const key = buildKey(category, folder)
      productsByKey.set(key, row)
      const label = `${row.sku || 'No SKU'} · ${folder}`
      productOptions.push({ key, label })
    })
    renderProductOptions('')
  }

  const loadSales = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      salesBody.innerHTML = ''
      salesEmpty.hidden = false
      return
    }
    const response = await fetch(`/api/sales?event_id=${encodeURIComponent(eventId)}`)
    if (!response.ok) {
      setStatus(saleStatus, 'Failed to load sales.')
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

  const recordSale = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      setStatus(saleStatus, 'Select an event first.')
      return
    }
    const selected = productsByKey.get(productSelect.value)
    if (!selected) {
      setStatus(saleStatus, 'Select a product first.')
      return
    }
    const quantity = parseInt(qtyInput.value, 10)
    if (!quantity || quantity <= 0) {
      setStatus(saleStatus, 'Quantity must be greater than 0.')
      return
    }
    const price = getEffectivePrice()
    if (price == null) {
      setStatus(saleStatus, 'Override price must be a number.')
      return
    }
    const payload = {
      event_id: eventId,
      category: selected.category,
      product_folder: selected.product_folder,
      sku: selected.sku,
      color: colorSelect.value.trim(),
      size: sizeSelect.value.trim(),
      quantity,
      unit_price: price.toFixed(2),
      override_price: overridePriceInput.value.trim(),
      payment_method: paymentSelect.value,
    }
    const response = await fetch('/api/sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(saleStatus, data.error || 'Failed to record sale.')
      return
    }
    const stockNote = data.stock_adjusted ? '' : ' (stock not adjusted)'
    setStatus(saleStatus, `Sale recorded${stockNote}.`)
    overridePriceInput.value = ''
    updateTotalPrice()
    await loadSales()
  }

  eventSaveBtn.addEventListener('click', () => saveEvent().catch(console.error))
  eventCancelBtn.addEventListener('click', () => {
    resetEventForm()
    setStatus(eventStatus, '')
  })
  eventSelect.addEventListener('change', () => loadSales().catch(console.error))
  productSearch.addEventListener('input', () => renderProductOptions(productSearch.value))
  productSelect.addEventListener('change', refreshSuggestions)
  colorSelect.addEventListener('change', updateTotalPrice)
  sizeSelect.addEventListener('change', updateTotalPrice)
  qtyInput.addEventListener('input', updateTotalPrice)
  overridePriceInput.addEventListener('input', updateTotalPrice)
  recordSaleBtn.addEventListener('click', () => recordSale().catch(console.error))

  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' })
    window.location.href = '/login'
  })

  resetEventForm()
  loadEvents().catch(console.error)
  loadProducts().then(loadSales).catch(console.error)
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
        <h1 class="title">Events & Sales</h1>
        <p class="subtitle">Track craft fair events and record in-person sales.</p>
        <p class="version">
          Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
        </p>
      </div>
      <div class="nav-links">
        <RouterLink to="/">Products</RouterLink>
        <RouterLink to="/stock">Stock</RouterLink>
        <RouterLink to="/events">Events</RouterLink>
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
      <h2>Quick sale</h2>
      <div class="grid">
        <div>
          <label for="eventSelect">Event</label>
          <select id="eventSelect"></select>
        </div>
        <div>
          <label for="productSearch">Search</label>
          <input id="productSearch" type="search" placeholder="Search products..." />
        </div>
        <div>
          <label for="productSelect">Product</label>
          <select id="productSelect"></select>
        </div>
        <div>
          <label for="colorSelect">Color</label>
          <select id="colorSelect"></select>
        </div>
        <div>
          <label for="sizeSelect">Size</label>
          <select id="sizeSelect"></select>
        </div>
        <div>
          <label for="qtyInput">Quantity</label>
          <input id="qtyInput" type="number" min="1" value="1" />
        </div>
        <div>
          <label for="paymentSelect">Payment method</label>
          <select id="paymentSelect">
            <option value="Cash">Cash</option>
            <option value="Card">Card</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label for="defaultPrice">Default price (GBP)</label>
          <input id="defaultPrice" type="text" disabled />
        </div>
        <div>
          <label for="overridePrice">Override price (GBP)</label>
          <input id="overridePrice" type="text" placeholder="Optional override" />
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="recordSaleBtn" class="btn secondary" type="button">Record Sale</button>
        <div class="status" id="totalPrice">Total: 0.00 GBP</div>
      </div>
      <div class="status" id="saleStatus"></div>
    </section>

    <section class="card">
      <h2>Recent sales</h2>
      <div class="table-wrap">
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
