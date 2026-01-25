<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
  const productSearch = document.getElementById('productSearch')
  const productSelect = document.getElementById('productSelect')
  const colorSelect = document.getElementById('colorSelect')
  const sizeSelect = document.getElementById('sizeSelect')
  const qtyInput = document.getElementById('qtyInput')
  const statusSelect = document.getElementById('statusSelect')
  const addBtn = document.getElementById('addBtn')
  const statusEl = document.getElementById('status')
  const queueBody = document.getElementById('queueTableBody')
  const queueEmpty = document.getElementById('queueEmpty')
  const logoutBtn = document.getElementById('logoutBtn')

  let products = []
  let queueRows = []
  const productsByKey = new Map()
  let productOptions = []

  const buildKey = (category, folder) => `${category}|||${folder}`

  const parseList = (value) =>
    (value || '')
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length)

  const setStatus = (message) => {
    statusEl.textContent = message
  }

  const getSelectedProduct = () => {
    const key = productSelect.value
    return productsByKey.get(key) || null
  }

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

  const refreshSuggestions = () => {
    const selected = getSelectedProduct()
    const colors = selected ? parseList(selected.Colors) : []
    const sizes = selected ? parseList(selected.Sizes) : []
    renderSelect(colorSelect, colors, colors.length ? 'Select color' : 'No colors set')
    renderSelect(sizeSelect, sizes, sizes.length ? 'Select size' : 'No sizes set')
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
    if (current) {
      productSelect.value = current
    }
  }

  const renderQueue = () => {
    queueBody.innerHTML = ''
    if (!queueRows.length) {
      queueEmpty.hidden = false
      return
    }
    queueEmpty.hidden = true
    queueRows.forEach((row) => {
      const tr = document.createElement('tr')
      const productCell = document.createElement('td')
      productCell.textContent = row.sku ? `${row.sku} · ${row.product_folder}` : row.product_folder

      const variationCell = document.createElement('td')
      const variationParts = [row.color, row.size].filter(Boolean)
      variationCell.textContent = variationParts.length ? variationParts.join(' / ') : '—'

      const qtyCell = document.createElement('td')
      qtyCell.textContent = row.quantity

      const statusCell = document.createElement('td')
      statusCell.textContent = row.status || 'Queued'

      const actionsCell = document.createElement('td')
      const actions = document.createElement('div')
      actions.className = 'row-actions'

      const minusBtn = document.createElement('button')
      minusBtn.type = 'button'
      minusBtn.textContent = '-1'
      minusBtn.addEventListener('click', () => adjustQueue(row.id, -1))

      const plusBtn = document.createElement('button')
      plusBtn.type = 'button'
      plusBtn.textContent = '+1'
      plusBtn.addEventListener('click', () => adjustQueue(row.id, 1))

      const toggleBtn = document.createElement('button')
      toggleBtn.type = 'button'
      toggleBtn.textContent = row.status === 'Printing' ? 'Queue' : 'Start'
      toggleBtn.addEventListener('click', () => toggleStatus(row))

      const completeBtn = document.createElement('button')
      completeBtn.type = 'button'
      completeBtn.textContent = 'Complete'
      completeBtn.addEventListener('click', () => completeQueue(row.id))

      const deleteBtn = document.createElement('button')
      deleteBtn.type = 'button'
      deleteBtn.textContent = 'Delete'
      deleteBtn.addEventListener('click', () => {
        if (!confirm('Remove this production item?')) return
        deleteQueue(row.id).catch(console.error)
      })

      actions.appendChild(minusBtn)
      actions.appendChild(plusBtn)
      actions.appendChild(toggleBtn)
      actions.appendChild(completeBtn)
      actions.appendChild(deleteBtn)
      actionsCell.appendChild(actions)

      tr.appendChild(productCell)
      tr.appendChild(variationCell)
      tr.appendChild(qtyCell)
      tr.appendChild(statusCell)
      tr.appendChild(actionsCell)
      queueBody.appendChild(tr)
    })
  }

  const loadQueue = async () => {
    const response = await fetch('/api/production', { cache: 'no-store' })
    if (!response.ok) {
      setStatus('Failed to load production queue.')
      return
    }
    const payload = await response.json()
    queueRows = payload.rows || []
    renderQueue()
  }

  const loadProducts = async () => {
    const response = await fetch('/api/rows', { cache: 'no-store' })
    if (!response.ok) {
      setStatus('Failed to load products.')
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

  const addQueue = async () => {
    const selected = getSelectedProduct()
    if (!selected) {
      setStatus('Select a product first.')
      return
    }
    const quantity = parseInt(qtyInput.value, 10) || 0
    if (quantity <= 0) {
      setStatus('Quantity must be greater than 0.')
      return
    }
    const body = {
      action: 'create',
      category: selected.category,
      product_folder: selected.product_folder,
      color: colorSelect.value || '',
      size: sizeSelect.value || '',
      quantity,
      status: statusSelect.value || 'Queued',
    }
    const response = await fetch('/api/production', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Failed to add production item.')
      return
    }
    setStatus('Production item saved.')
    qtyInput.value = '1'
    await loadQueue()
  }

  const adjustQueue = async (itemId, delta) => {
    const response = await fetch('/api/production_adjust', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: itemId, delta }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Failed to adjust production item.')
      return
    }
    await loadQueue()
  }

  const toggleStatus = async (row) => {
    const nextStatus = row.status === 'Printing' ? 'Queued' : 'Printing'
    const response = await fetch('/api/production', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update', id: row.id, status: nextStatus }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Failed to update status.')
      return
    }
    await loadQueue()
  }

  const completeQueue = async (itemId) => {
    const response = await fetch('/api/production_complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: itemId }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Failed to complete production item.')
      return
    }
    const stockNote = data.stock_adjusted ? ` Stock now ${data.new_quantity}.` : ''
    setStatus(`Moved to stock.${stockNote}`)
    await loadQueue()
  }

  const deleteQueue = async (itemId) => {
    const response = await fetch('/api/production', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id: itemId }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(data.error || 'Failed to delete production item.')
      return
    }
    await loadQueue()
  }

  addBtn.addEventListener('click', () => addQueue().catch(console.error))
  productSearch.addEventListener('input', () => renderProductOptions(productSearch.value))
  productSelect.addEventListener('change', refreshSuggestions)

  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' })
    window.location.href = '/login'
  })

  qtyInput.value = '1'
  statusSelect.value = 'Queued'
  loadProducts().catch(console.error)
  loadQueue().catch(console.error)
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
        <h1 class="title">Production Queue</h1>
        <p class="subtitle">Track what to print and move completed items into stock.</p>
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
      <h2>Add to production</h2>
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
          <label for="statusSelect">Status</label>
          <select id="statusSelect">
            <option value="Queued">Queued</option>
            <option value="Printing">Printing</option>
          </select>
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="addBtn" class="btn" type="button">Add to Queue</button>
      </div>
      <div class="status" id="status"></div>
    </section>

    <section class="card">
      <h2>Queue</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Variation</th>
              <th>Qty</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="queueTableBody"></tbody>
        </table>
        <div class="empty" id="queueEmpty">No production items yet.</div>
      </div>
    </section>
  </main>
</template>
