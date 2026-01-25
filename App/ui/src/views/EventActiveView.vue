<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
  const eventSelect = document.getElementById('eventSelect')
  const activeEventName = document.getElementById('activeEventName')
  const activeEventMeta = document.getElementById('activeEventMeta')
  const totalsItems = document.getElementById('totalsItems')
  const totalsRevenue = document.getElementById('totalsRevenue')
  const paymentBreakdownBody = document.getElementById('paymentBreakdownBody')

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
  const saleCancelBtn = document.getElementById('saleCancelBtn')
  const salesBody = document.getElementById('salesTableBody')
  const salesEmpty = document.getElementById('salesEmpty')
  const eventMediaInput = document.getElementById('eventMediaInput')
  const eventMediaUploadBtn = document.getElementById('eventMediaUploadBtn')
  const eventMediaBody = document.getElementById('eventMediaBody')
  const eventMediaEmpty = document.getElementById('eventMediaEmpty')
  const eventMediaStatus = document.getElementById('eventMediaStatus')
  const logoutBtn = document.getElementById('logoutBtn')

  let events = []
  let products = []
  let productOptions = []
  const productsByKey = new Map()
  const initialEventId = new URLSearchParams(window.location.search).get('event_id')
  let initialEventApplied = false
  let editingSaleId = null

  const buildKey = (category, folder) => `${category}|||${folder}`

  const parseList = (value) =>
    (value || '')
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length)

  const renderSelectOptions = (selectEl, items, placeholder) => {
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

  const setStatus = (el, message) => {
    el.textContent = message
  }

  const formatEventDate = (value) => {
    if (!value) return ''
    return value
  }

  const setSelectValue = (selectEl, value) => {
    const target = value || ''
    if ([...selectEl.options].some((option) => option.value === target)) {
      selectEl.value = target
      return
    }
    if (!target) {
      selectEl.value = ''
      return
    }
    const option = document.createElement('option')
    option.value = target
    option.textContent = target
    selectEl.appendChild(option)
    selectEl.value = target
  }

  const getSelectedEvent = () => {
    const eventId = eventSelect.value
    if (!eventId) return null
    return events.find((event) => String(event.id) === String(eventId)) || null
  }

  const updateActiveEventMeta = () => {
    const selected = getSelectedEvent()
    if (!selected) {
      activeEventName.textContent = 'Select an event to start selling.'
      activeEventMeta.textContent = 'No active event selected.'
      return
    }
    activeEventName.textContent = selected.name || 'Untitled event'
    const metaParts = [formatEventDate(selected.event_date), selected.location || 'No location']
    const contactParts = []
    if (selected.contact_name) contactParts.push(selected.contact_name)
    if (selected.contact_email) contactParts.push(selected.contact_email)
    const contactText = contactParts.length ? contactParts.join(' · ') : 'No contact info'
    activeEventMeta.textContent = `${metaParts.join(' · ')} · ${contactText}`
  }

  const clearTotals = () => {
    totalsItems.textContent = '0'
    totalsRevenue.textContent = '0.00 GBP'
    paymentBreakdownBody.innerHTML = '<tr><td colspan="2">No payments yet.</td></tr>'
  }

  const renderTotals = (totals) => {
    totalsItems.textContent = String(totals.total_items ?? 0)
    totalsRevenue.textContent = `${totals.total_revenue || '0.00'} GBP`
    const payments = totals.payments || {}
    paymentBreakdownBody.innerHTML = ''
    const entries = Object.entries(payments)
    if (!entries.length) {
      paymentBreakdownBody.innerHTML = '<tr><td colspan="2">No payments yet.</td></tr>'
      return
    }
    entries.forEach(([method, total]) => {
      const row = document.createElement('tr')
      const methodCell = document.createElement('td')
      methodCell.textContent = method
      const totalCell = document.createElement('td')
      totalCell.textContent = `${total} GBP`
      row.appendChild(methodCell)
      row.appendChild(totalCell)
      paymentBreakdownBody.appendChild(row)
    })
  }

  const loadEventTotals = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      clearTotals()
      return
    }
    const response = await fetch(`/api/event_totals?event_id=${encodeURIComponent(eventId)}`)
    if (!response.ok) {
      clearTotals()
      return
    }
    const payload = await response.json()
    renderTotals(payload.totals || {})
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

  const renderProductOptions = (query) => {
    const normalized = (query || '').trim().toLowerCase()
    productSelect.innerHTML = ''
    const filtered = productOptions.filter((option) =>
      option.label.toLowerCase().includes(normalized)
    )
    const emptyOption = document.createElement('option')
    emptyOption.value = ''
    emptyOption.textContent = filtered.length ? 'Select product' : 'No matches'
    productSelect.appendChild(emptyOption)
    filtered
      .slice(0, 100)
      .forEach((option) => {
        const el = document.createElement('option')
        el.value = option.key
        el.textContent = option.label
        productSelect.appendChild(el)
      })
    if (filtered.length) {
      productSelect.value = filtered[0].key
      refreshSuggestions()
    } else {
      refreshSuggestions()
    }
  }

  const refreshSuggestions = () => {
    const selected = productsByKey.get(productSelect.value) || null
    const colors = selected ? parseList(selected.Colors) : []
    const sizes = selected ? parseList(selected.Sizes) : []
    renderSelectOptions(colorSelect, colors, colors.length ? 'Select color' : 'No colors set')
    renderSelectOptions(sizeSelect, sizes, sizes.length ? 'Select size' : 'No sizes set')
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

  const renderSalesRows = (rows) => {
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

      const actionsCell = document.createElement('td')
      const actions = document.createElement('div')
      actions.className = 'row-actions'
      const editBtn = document.createElement('button')
      editBtn.type = 'button'
      editBtn.textContent = 'Edit'
      editBtn.addEventListener('click', () => {
        fillSaleForm(row)
      })
      const deleteBtn = document.createElement('button')
      deleteBtn.type = 'button'
      deleteBtn.textContent = 'Delete'
      deleteBtn.addEventListener('click', () => {
        if (!confirm('Delete this sale?')) return
        deleteSale(row.id).catch(console.error)
      })
      actions.appendChild(editBtn)
      actions.appendChild(deleteBtn)
      actionsCell.appendChild(actions)

      tr.appendChild(whenCell)
      tr.appendChild(productCell)
      tr.appendChild(variationCell)
      tr.appendChild(qtyCell)
      tr.appendChild(priceCell)
      tr.appendChild(paymentCell)
      tr.appendChild(overrideCell)
      tr.appendChild(actionsCell)
      salesBody.appendChild(tr)
    })
  }

  const loadSales = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      salesBody.innerHTML = ''
      salesEmpty.hidden = false
      clearTotals()
      return
    }
    const response = await fetch(`/api/sales?event_id=${encodeURIComponent(eventId)}`)
    if (!response.ok) {
      setStatus(saleStatus, 'Failed to load sales.')
      return
    }
    const payload = await response.json()
    renderSalesRows(payload.rows || [])
  }

  const loadEventMedia = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      eventMediaBody.innerHTML = ''
      eventMediaEmpty.hidden = false
      setStatus(eventMediaStatus, 'Select an event to view images.')
      return
    }
    const response = await fetch(`/api/event_media?event_id=${encodeURIComponent(eventId)}`)
    if (!response.ok) {
      setStatus(eventMediaStatus, 'Failed to load event images.')
      return
    }
    const payload = await response.json()
    const rows = payload.rows || []
    eventMediaBody.innerHTML = ''
    if (!rows.length) {
      eventMediaEmpty.hidden = false
      return
    }
    eventMediaEmpty.hidden = true
    rows.forEach((row) => {
      const tr = document.createElement('tr')

      const previewCell = document.createElement('td')
      const img = document.createElement('img')
      img.src = `/files-records/${encodeURI(row.file_path)}`
      img.alt = 'Event poster'
      img.style.maxWidth = '120px'
      img.style.borderRadius = '8px'
      previewCell.appendChild(img)

      const nameCell = document.createElement('td')
      const fileName = (row.file_path || '').split('/').pop()
      nameCell.textContent = fileName || row.file_path || 'Image'

      const actionsCell = document.createElement('td')
      const actions = document.createElement('div')
      actions.className = 'row-actions'
      const openLink = document.createElement('a')
      openLink.href = `/files-records/${encodeURI(row.file_path)}`
      openLink.target = '_blank'
      openLink.rel = 'noopener noreferrer'
      openLink.textContent = 'Open'
      openLink.className = 'btn ghost'
      const deleteBtn = document.createElement('button')
      deleteBtn.type = 'button'
      deleteBtn.textContent = 'Delete'
      deleteBtn.addEventListener('click', () => {
        if (!confirm('Delete this event image?')) return
        deleteEventMedia(row.id).catch(console.error)
      })
      actions.appendChild(openLink)
      actions.appendChild(deleteBtn)
      actionsCell.appendChild(actions)

      tr.appendChild(previewCell)
      tr.appendChild(nameCell)
      tr.appendChild(actionsCell)
      eventMediaBody.appendChild(tr)
    })
  }

  const uploadEventMedia = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      setStatus(eventMediaStatus, 'Select an event first.')
      return
    }
    if (!eventMediaInput.files || !eventMediaInput.files.length) {
      setStatus(eventMediaStatus, 'Choose images to upload.')
      return
    }
    const formData = new FormData()
    formData.append('event_id', eventId)
    Array.from(eventMediaInput.files).forEach((file) => {
      formData.append('file', file)
    })
    const response = await fetch('/api/event_upload', {
      method: 'POST',
      body: formData,
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(eventMediaStatus, data.error || 'Failed to upload images.')
      return
    }
    eventMediaInput.value = ''
    setStatus(eventMediaStatus, 'Images uploaded.')
    await loadEventMedia()
  }

  const deleteEventMedia = async (mediaId) => {
    const response = await fetch('/api/event_media', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id: mediaId }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(eventMediaStatus, data.error || 'Failed to delete image.')
      return
    }
    await loadEventMedia()
  }

  const resetSaleForm = () => {
    editingSaleId = null
    recordSaleBtn.textContent = 'Record Sale'
    saleCancelBtn.hidden = true
    overridePriceInput.value = ''
    qtyInput.value = '1'
    paymentSelect.value = 'Cash'
    updateTotalPrice()
  }

  const fillSaleForm = (row) => {
    editingSaleId = row.id
    recordSaleBtn.textContent = 'Update Sale'
    saleCancelBtn.hidden = false
    productSearch.value = ''
    renderProductOptions('')
    const key = buildKey(row.category, row.product_folder)
    if (![...productSelect.options].some((option) => option.value === key)) {
      const option = document.createElement('option')
      option.value = key
      option.textContent = row.sku ? `${row.sku} · ${row.product_folder}` : row.product_folder
      productSelect.appendChild(option)
    }
    productSelect.value = key
    refreshSuggestions()
    setSelectValue(colorSelect, row.color || '')
    setSelectValue(sizeSelect, row.size || '')
    qtyInput.value = String(row.quantity || 1)
    paymentSelect.value = row.payment_method || 'Cash'
    overridePriceInput.value = row.override_price || ''
    updateTotalPrice()
  }

  const recordSale = async () => {
    if (editingSaleId) {
      await updateSale()
      return
    }
    const eventId = eventSelect.value
    if (!eventId) {
      setStatus(saleStatus, 'Select an event first.')
      return
    }
    const selected = productsByKey.get(productSelect.value) || null
    if (!selected) {
      setStatus(saleStatus, 'Select a product first.')
      return
    }
    const quantity = parseInt(qtyInput.value, 10) || 0
    if (quantity <= 0) {
      setStatus(saleStatus, 'Quantity must be greater than 0.')
      return
    }
    const overrideValue = overridePriceInput.value.trim()
    if (overrideValue && Number.isNaN(parseFloat(overrideValue))) {
      setStatus(saleStatus, 'Override price must be a number.')
      return
    }
    const unitPrice = parseFloat(defaultPriceInput.value) || 0
    const body = {
      event_id: eventId,
      category: selected.category,
      product_folder: selected.product_folder,
      sku: selected.sku,
      color: colorSelect.value || '',
      size: sizeSelect.value || '',
      quantity,
      unit_price: unitPrice.toFixed(2),
      override_price: overrideValue,
      payment_method: paymentSelect.value || '',
    }
    const response = await fetch('/api/sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(saleStatus, data.error || 'Failed to record sale.')
      return
    }
    const stockNote = data.stock_adjusted ? ` (stock now ${data.new_quantity})` : ''
    setStatus(saleStatus, `Sale recorded${stockNote}.`)
    overridePriceInput.value = ''
    updateTotalPrice()
    await loadSales()
    await loadEventTotals()
  }

  const updateSale = async () => {
    const eventId = eventSelect.value
    if (!eventId) {
      setStatus(saleStatus, 'Select an event first.')
      return
    }
    const selected = productsByKey.get(productSelect.value) || null
    if (!selected) {
      setStatus(saleStatus, 'Select a product first.')
      return
    }
    const quantity = parseInt(qtyInput.value, 10) || 0
    if (quantity <= 0) {
      setStatus(saleStatus, 'Quantity must be greater than 0.')
      return
    }
    const overrideValue = overridePriceInput.value.trim()
    if (overrideValue && Number.isNaN(parseFloat(overrideValue))) {
      setStatus(saleStatus, 'Override price must be a number.')
      return
    }
    const unitPrice = parseFloat(defaultPriceInput.value) || 0
    const body = {
      id: editingSaleId,
      event_id: eventId,
      category: selected.category,
      product_folder: selected.product_folder,
      sku: selected.sku,
      color: colorSelect.value || '',
      size: sizeSelect.value || '',
      quantity,
      unit_price: unitPrice.toFixed(2),
      override_price: overrideValue,
      payment_method: paymentSelect.value || '',
    }
    const response = await fetch('/api/sale_update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(saleStatus, data.error || 'Failed to update sale.')
      return
    }
    setStatus(saleStatus, 'Sale updated.')
    resetSaleForm()
    await loadSales()
    await loadEventTotals()
  }

  const deleteSale = async (saleId) => {
    const response = await fetch('/api/sale_delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: saleId, event_id: eventSelect.value }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(saleStatus, data.error || 'Failed to delete sale.')
      return
    }
    if (editingSaleId === saleId) {
      resetSaleForm()
    }
    setStatus(saleStatus, 'Sale deleted.')
    await loadSales()
    await loadEventTotals()
  }

  const refreshActiveEvent = async () => {
    updateActiveEventMeta()
    await loadEventTotals()
    await loadSales()
    await loadEventMedia()
  }

  const loadEvents = async () => {
    const response = await fetch('/api/events', { cache: 'no-store' })
    if (!response.ok) {
      setStatus(saleStatus, 'Failed to load events.')
      return
    }
    const payload = await response.json()
    events = payload.events || []
    renderEventSelect()
    if (!initialEventApplied && initialEventId) {
      if ([...eventSelect.options].some((option) => option.value === String(initialEventId))) {
        eventSelect.value = String(initialEventId)
      }
      initialEventApplied = true
    }
    await refreshActiveEvent()
  }

  eventSelect.addEventListener('change', () => {
    refreshActiveEvent().catch(console.error)
  })
  productSearch.addEventListener('input', () => renderProductOptions(productSearch.value))
  productSelect.addEventListener('change', refreshSuggestions)
  colorSelect.addEventListener('change', updateTotalPrice)
  sizeSelect.addEventListener('change', updateTotalPrice)
  qtyInput.addEventListener('input', updateTotalPrice)
  overridePriceInput.addEventListener('input', updateTotalPrice)
  recordSaleBtn.addEventListener('click', () => recordSale().catch(console.error))
  saleCancelBtn.addEventListener('click', () => {
    resetSaleForm()
    setStatus(saleStatus, '')
  })
  eventMediaUploadBtn.addEventListener('click', () => {
    uploadEventMedia().catch(console.error)
  })

  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' })
    window.location.href = '/login'
  })

  resetSaleForm()
  clearTotals()
  loadEvents().catch(console.error)
  loadProducts().catch(console.error)
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
        <h1 class="title">Active Event</h1>
        <p class="subtitle" id="activeEventName">Select an event to start selling.</p>
        <p class="version">
          Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
        </p>
      </div>
      <div class="nav-links">
        <RouterLink to="/">Products</RouterLink>
        <RouterLink to="/stock">Stock</RouterLink>
        <RouterLink to="/events">Events</RouterLink>
        <RouterLink to="/supplies">Supplies</RouterLink>
        <RouterLink to="/add">Add Product</RouterLink>
        <button class="ghost" id="logoutBtn" type="button">Logout</button>
      </div>
    </nav>
  </header>

  <main>
    <section class="card">
      <h2>Active event</h2>
      <div class="grid">
        <div>
          <label for="eventSelect">Event</label>
          <select id="eventSelect"></select>
        </div>
        <div>
          <label>Total items</label>
          <div class="status" id="totalsItems">0</div>
        </div>
        <div>
          <label>Total revenue</label>
          <div class="status" id="totalsRevenue">0.00 GBP</div>
        </div>
      </div>
      <div class="status" id="activeEventMeta" style="margin-top: 8px;">No active event selected.</div>
      <div class="table-wrap" style="margin-top: 12px;">
        <table>
          <thead>
            <tr>
              <th>Payment method</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody id="paymentBreakdownBody"></tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <h2>Quick sale</h2>
      <div class="grid">
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
        <button id="saleCancelBtn" class="btn ghost" type="button" hidden>Cancel edit</button>
        <div class="status" id="totalPrice">Total: 0.00 GBP</div>
      </div>
      <div class="status" id="saleStatus"></div>
    </section>

    <section class="card">
      <h2>Sales for this event</h2>
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
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="salesTableBody"></tbody>
        </table>
        <div class="empty" id="salesEmpty">No sales recorded yet.</div>
      </div>
    </section>

    <section class="card">
      <h2>Event images</h2>
      <div class="grid">
        <div>
          <label for="eventMediaInput">Upload posters</label>
          <input id="eventMediaInput" type="file" accept="image/*" multiple />
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="eventMediaUploadBtn" class="btn" type="button">Upload Images</button>
      </div>
      <div class="status" id="eventMediaStatus"></div>
      <div class="table-wrap" style="margin-top: 12px;">
        <table>
          <thead>
            <tr>
              <th>Preview</th>
              <th>Filename</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="eventMediaBody"></tbody>
        </table>
        <div class="empty" id="eventMediaEmpty">No images uploaded yet.</div>
      </div>
    </section>
  </main>
</template>
