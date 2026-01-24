<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
  const productSearch = document.getElementById('productSearch')
  const productSelect = document.getElementById('productSelect')
  const colorInput = document.getElementById('colorSelect')
  const sizeInput = document.getElementById('sizeSelect')
  const qtyInput = document.getElementById('qtyInput')
  const addBtn = document.getElementById('addBtn')
  const removeBtn = document.getElementById('removeBtn')
  const statusEl = document.getElementById('status')
  const stockBody = document.getElementById('stockTableBody')
  const stockEmpty = document.getElementById('stockEmpty')
  const productMeta = document.getElementById('productMeta')
  const logoutBtn = document.getElementById('logoutBtn')

  let products = []
  let stockRows = []
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

  const refreshSuggestions = () => {
    const selected = getSelectedProduct()
    const colors = selected ? parseList(selected.Colors) : []
    const sizes = selected ? parseList(selected.Sizes) : []
    if (selected) {
      productMeta.textContent = selected.sku
        ? `${selected.sku} · ${selected.category}`
        : selected.category
    } else {
      productMeta.textContent = 'Select a product to get started.'
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

    renderSelect(colorInput, colors, colors.length ? 'Select color' : 'No colors set')
    renderSelect(sizeInput, sizes, sizes.length ? 'Select size' : 'No sizes set')
  }

  const renderStockTable = () => {
    stockBody.innerHTML = ''
    if (!stockRows.length) {
      stockEmpty.hidden = false
      return
    }
    stockEmpty.hidden = true
    const sorted = [...stockRows].sort((a, b) => {
      const keyA = `${a.category} ${a.product_folder} ${a.color} ${a.size}`.toLowerCase()
      const keyB = `${b.category} ${b.product_folder} ${b.color} ${b.size}`.toLowerCase()
      return keyA.localeCompare(keyB)
    })

    sorted.forEach((row) => {
      const tr = document.createElement('tr')
      const key = buildKey(row.category, row.product_folder)
      const product = productsByKey.get(key)
      const sku = row.sku || product?.sku || ''
      const productLabel = product?.product_folder || row.product_folder

      const productCell = document.createElement('td')
      const productText = document.createElement('div')
      productText.className = 'stock-product'
      productText.innerHTML = `<strong>${sku || 'No SKU'}</strong><span>${productLabel}</span><small>${row.category}</small>`
      productCell.appendChild(productText)

      const colorCell = document.createElement('td')
      colorCell.textContent = row.color || '—'

      const sizeCell = document.createElement('td')
      sizeCell.textContent = row.size || '—'

      const qtyCell = document.createElement('td')
      qtyCell.textContent = row.quantity || '0'

      const actionsCell = document.createElement('td')
      const actions = document.createElement('div')
      actions.className = 'actions'
      const minusBtn = document.createElement('button')
      minusBtn.className = 'btn small ghost'
      minusBtn.type = 'button'
      minusBtn.textContent = '-1'
      minusBtn.addEventListener('click', () => {
        adjustStock({
          category: row.category,
          product_folder: row.product_folder,
          sku: row.sku,
          color: row.color,
          size: row.size,
          delta: -1,
        })
      })
      const plusBtn = document.createElement('button')
      plusBtn.className = 'btn small'
      plusBtn.type = 'button'
      plusBtn.textContent = '+1'
      plusBtn.addEventListener('click', () => {
        adjustStock({
          category: row.category,
          product_folder: row.product_folder,
          sku: row.sku,
          color: row.color,
          size: row.size,
          delta: 1,
        })
      })
      actions.appendChild(minusBtn)
      actions.appendChild(plusBtn)
      actionsCell.appendChild(actions)

      tr.appendChild(productCell)
      tr.appendChild(colorCell)
      tr.appendChild(sizeCell)
      tr.appendChild(qtyCell)
      tr.appendChild(actionsCell)
      stockBody.appendChild(tr)
    })
  }

  const loadStock = async () => {
    const response = await fetch('/api/stock', { cache: 'no-store' })
    if (!response.ok) {
      setStatus('Failed to load stock.')
      return
    }
    const payload = await response.json()
    stockRows = payload.rows || []
    renderStockTable()
    refreshSuggestions()
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

  const renderProductOptions = (filter) => {
    const normalized = (filter || '').trim().toLowerCase()
    const current = productSelect.value
    productSelect.innerHTML = '<option value=\"\">Select a product</option>'
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

  const adjustStock = async (payload) => {
    const response = await fetch('/api/stock_adjust', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      setStatus(data.error || 'Stock update failed.')
      return
    }
    setStatus('Stock updated.')
    await loadStock()
  }

  const handleAdjust = async (direction) => {
    const selected = getSelectedProduct()
    if (!selected) {
      setStatus('Select a product first.')
      return
    }
    const quantity = parseInt(qtyInput.value, 10)
    if (!quantity || quantity <= 0) {
      setStatus('Enter a quantity greater than 0.')
      return
    }
    const payload = {
      category: selected.category,
      product_folder: selected.product_folder,
      sku: selected.sku,
      color: colorInput.value.trim(),
      size: sizeInput.value.trim(),
      delta: direction === 'add' ? quantity : -quantity,
    }
    await adjustStock(payload)
  }

  productSelect.addEventListener('change', () => {
    refreshSuggestions()
  })

  productSearch.addEventListener('input', () => {
    renderProductOptions(productSearch.value)
  })

  addBtn.addEventListener('click', () => handleAdjust('add'))
  removeBtn.addEventListener('click', () => handleAdjust('remove'))

  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' })
    window.location.href = '/login'
  })

  loadProducts()
    .then(loadStock)
    .catch((error) => {
      console.error(error)
      setStatus('Failed to load stock data.')
    })
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
        <h1 class="title">Stock Manager</h1>
        <p class="subtitle">Track live counts for products, colors, and sizes.</p>
        <p class="version">
          Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
        </p>
      </div>
      <div class="nav-links">
        <RouterLink to="/">Products</RouterLink>
        <RouterLink to="/stock">Stock</RouterLink>
        <RouterLink to="/add">Add Product</RouterLink>
        <button class="ghost" id="logoutBtn" type="button">Logout</button>
      </div>
    </nav>
  </header>

  <main>
    <section class="card">
      <h2>Adjust stock</h2>
      <p id="productMeta" class="status">Select a product to get started.</p>
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
      </div>
      <div class="actions stock-actions">
        <button id="addBtn" class="btn" type="button">Add Stock</button>
        <button id="removeBtn" class="btn ghost" type="button">Remove Stock</button>
      </div>
      <div class="status" id="status"></div>
    </section>

    <section class="card">
      <h2>Current stock</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Color</th>
              <th>Size</th>
              <th>Qty</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="stockTableBody"></tbody>
        </table>
        <div class="empty" id="stockEmpty" hidden>No stock entries yet.</div>
      </div>
    </section>
  </main>
</template>
