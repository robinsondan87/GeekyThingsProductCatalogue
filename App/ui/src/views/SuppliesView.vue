<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
  const supplyNameInput = document.getElementById('supplyName')
  const supplyCategoryInput = document.getElementById('supplyCategory')
  const supplyUnitInput = document.getElementById('supplyUnit')
  const supplyQtyInput = document.getElementById('supplyQty')
  const supplyReorderInput = document.getElementById('supplyReorder')
  const supplyVendorInput = document.getElementById('supplyVendor')
  const supplyLeadTimeInput = document.getElementById('supplyLeadTime')
  const supplyLocationInput = document.getElementById('supplyLocation')
  const supplyNotesInput = document.getElementById('supplyNotes')
  const supplySaveBtn = document.getElementById('supplySaveBtn')
  const supplyCancelBtn = document.getElementById('supplyCancelBtn')
  const supplyStatus = document.getElementById('supplyStatus')
  const supplySearchInput = document.getElementById('supplySearch')
  const supplyTableBody = document.getElementById('supplyTableBody')
  const supplyEmpty = document.getElementById('supplyEmpty')

  const expenseDateInput = document.getElementById('expenseDate')
  const expenseVendorInput = document.getElementById('expenseVendor')
  const expenseCategoryInput = document.getElementById('expenseCategory')
  const expenseAmountInput = document.getElementById('expenseAmount')
  const expensePaymentInput = document.getElementById('expensePayment')
  const expenseReferenceInput = document.getElementById('expenseReference')
  const expenseDescriptionInput = document.getElementById('expenseDescription')
  const expenseReceiptInput = document.getElementById('expenseReceipt')
  const expenseSaveBtn = document.getElementById('expenseSaveBtn')
  const expenseCancelBtn = document.getElementById('expenseCancelBtn')
  const expenseStatus = document.getElementById('expenseStatus')
  const expenseTableBody = document.getElementById('expenseTableBody')
  const expenseEmpty = document.getElementById('expenseEmpty')
  const exportExpensesBtn = document.getElementById('exportExpensesBtn')
  const exportTotalsBtn = document.getElementById('exportTotalsBtn')
  const totalsYearSelect = document.getElementById('totalsYearSelect')
  const totalsAmount = document.getElementById('totalsAmount')
  const logoutBtn = document.getElementById('logoutBtn')

  let supplies = []
  let expenses = []
  let editingSupplyId = null
  let editingExpenseId = null

  const setStatus = (el, message) => {
    el.textContent = message
  }

  const resetSupplyForm = () => {
    editingSupplyId = null
    supplyNameInput.value = ''
    supplyCategoryInput.value = ''
    supplyUnitInput.value = ''
    supplyQtyInput.value = '0'
    supplyReorderInput.value = '0'
    supplyVendorInput.value = ''
    supplyLeadTimeInput.value = '0'
    supplyLocationInput.value = ''
    supplyNotesInput.value = ''
    supplySaveBtn.textContent = 'Save Supply'
    supplyCancelBtn.hidden = true
  }

  const resetExpenseForm = () => {
    editingExpenseId = null
    expenseDateInput.value = ''
    expenseVendorInput.value = ''
    expenseCategoryInput.value = ''
    expenseAmountInput.value = ''
    expensePaymentInput.value = 'Card'
    expenseReferenceInput.value = ''
    expenseDescriptionInput.value = ''
    expenseReceiptInput.value = ''
    expenseSaveBtn.textContent = 'Save Expense'
    expenseCancelBtn.hidden = true
  }

  const renderSupplies = (rows) => {
    supplyTableBody.innerHTML = ''
    if (!rows.length) {
      supplyEmpty.hidden = false
      return
    }
    supplyEmpty.hidden = true
    rows.forEach((row) => {
      const tr = document.createElement('tr')
      if (row.quantity <= row.reorder_point && row.reorder_point > 0) {
        tr.style.background = 'rgba(245, 158, 11, 0.08)'
      }

      const nameCell = document.createElement('td')
      nameCell.textContent = row.name
      const categoryCell = document.createElement('td')
      categoryCell.textContent = row.category || '—'
      const qtyCell = document.createElement('td')
      qtyCell.textContent = row.quantity
      const reorderCell = document.createElement('td')
      reorderCell.textContent = row.reorder_point || '0'
      const vendorCell = document.createElement('td')
      vendorCell.textContent = row.vendor || '—'
      const leadCell = document.createElement('td')
      leadCell.textContent = row.lead_time_days ? `${row.lead_time_days}d` : '—'
      const locationCell = document.createElement('td')
      locationCell.textContent = row.location || '—'
      const notesCell = document.createElement('td')
      notesCell.textContent = row.notes || '—'

      const actionsCell = document.createElement('td')
      const actions = document.createElement('div')
      actions.className = 'row-actions'
      const minusBtn = document.createElement('button')
      minusBtn.type = 'button'
      minusBtn.textContent = '-1'
      minusBtn.addEventListener('click', () => adjustSupply(row.id, -1))
      const plusBtn = document.createElement('button')
      plusBtn.type = 'button'
      plusBtn.textContent = '+1'
      plusBtn.addEventListener('click', () => adjustSupply(row.id, 1))
      const editBtn = document.createElement('button')
      editBtn.type = 'button'
      editBtn.textContent = 'Edit'
      editBtn.addEventListener('click', () => {
        fillSupplyForm(row)
      })
      const deleteBtn = document.createElement('button')
      deleteBtn.type = 'button'
      deleteBtn.textContent = 'Delete'
      deleteBtn.addEventListener('click', () => {
        if (!confirm('Delete this supply?')) return
        deleteSupply(row.id).catch(console.error)
      })
      actions.appendChild(minusBtn)
      actions.appendChild(plusBtn)
      actions.appendChild(editBtn)
      actions.appendChild(deleteBtn)
      actionsCell.appendChild(actions)

      tr.appendChild(nameCell)
      tr.appendChild(categoryCell)
      tr.appendChild(qtyCell)
      tr.appendChild(reorderCell)
      tr.appendChild(vendorCell)
      tr.appendChild(leadCell)
      tr.appendChild(locationCell)
      tr.appendChild(notesCell)
      tr.appendChild(actionsCell)
      supplyTableBody.appendChild(tr)
    })
  }

  const loadSupplies = async () => {
    const response = await fetch('/api/supplies', { cache: 'no-store' })
    if (!response.ok) {
      setStatus(supplyStatus, 'Failed to load supplies.')
      return
    }
    const payload = await response.json()
    supplies = payload.rows || []
    applySupplyFilter()
  }

  const applySupplyFilter = () => {
    const query = supplySearchInput.value.trim().toLowerCase()
    if (!query) {
      renderSupplies(supplies)
      return
    }
    const filtered = supplies.filter((row) => {
      const haystack = `${row.name} ${row.category} ${row.vendor} ${row.location}`.toLowerCase()
      return haystack.includes(query)
    })
    renderSupplies(filtered)
  }

  const fillSupplyForm = (row) => {
    editingSupplyId = row.id
    supplyNameInput.value = row.name || ''
    supplyCategoryInput.value = row.category || ''
    supplyUnitInput.value = row.unit || ''
    supplyQtyInput.value = String(row.quantity ?? 0)
    supplyReorderInput.value = String(row.reorder_point ?? 0)
    supplyVendorInput.value = row.vendor || ''
    supplyLeadTimeInput.value = String(row.lead_time_days ?? 0)
    supplyLocationInput.value = row.location || ''
    supplyNotesInput.value = row.notes || ''
    supplySaveBtn.textContent = 'Update Supply'
    supplyCancelBtn.hidden = false
  }

  const saveSupply = async () => {
    const payload = {
      name: supplyNameInput.value.trim(),
      category: supplyCategoryInput.value.trim(),
      unit: supplyUnitInput.value.trim(),
      quantity: parseInt(supplyQtyInput.value, 10) || 0,
      reorder_point: parseInt(supplyReorderInput.value, 10) || 0,
      vendor: supplyVendorInput.value.trim(),
      lead_time_days: parseInt(supplyLeadTimeInput.value, 10) || 0,
      location: supplyLocationInput.value.trim(),
      notes: supplyNotesInput.value.trim(),
    }
    if (!payload.name) {
      setStatus(supplyStatus, 'Supply name is required.')
      return
    }
    const body = editingSupplyId
      ? { action: 'update', id: editingSupplyId, supply: payload }
      : { action: 'create', supply: payload }
    const response = await fetch('/api/supplies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(supplyStatus, data.error || 'Failed to save supply.')
      return
    }
    setStatus(supplyStatus, editingSupplyId ? 'Supply updated.' : 'Supply saved.')
    resetSupplyForm()
    await loadSupplies()
  }

  const deleteSupply = async (supplyId) => {
    const response = await fetch('/api/supplies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id: supplyId }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(supplyStatus, data.error || 'Failed to delete supply.')
      return
    }
    await loadSupplies()
  }

  const adjustSupply = async (supplyId, delta) => {
    const response = await fetch('/api/supply_adjust', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: supplyId, delta }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(supplyStatus, data.error || 'Failed to adjust supply.')
      return
    }
    await loadSupplies()
  }

  const uploadReceipt = async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch('/api/expense_upload', {
      method: 'POST',
      body: formData,
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.error || 'Upload failed')
    }
    return data.receipt_path || ''
  }

  const loadExpenses = async () => {
    const response = await fetch('/api/expenses', { cache: 'no-store' })
    if (!response.ok) {
      setStatus(expenseStatus, 'Failed to load expenses.')
      return
    }
    const payload = await response.json()
    expenses = payload.rows || []
    renderExpenses(expenses)
    updateTotals()
  }

  const renderExpenses = (rows) => {
    expenseTableBody.innerHTML = ''
    if (!rows.length) {
      expenseEmpty.hidden = false
      return
    }
    expenseEmpty.hidden = true
    rows.forEach((row) => {
      const tr = document.createElement('tr')

      const dateCell = document.createElement('td')
      dateCell.textContent = row.expense_date || ''
      const vendorCell = document.createElement('td')
      vendorCell.textContent = row.vendor || '—'
      const categoryCell = document.createElement('td')
      categoryCell.textContent = row.category || '—'
      const amountCell = document.createElement('td')
      const amountValue = parseFloat(row.amount || 0)
      amountCell.textContent = `${amountValue.toFixed(2)} GBP`
      const paymentCell = document.createElement('td')
      paymentCell.textContent = row.payment_method || '—'
      const referenceCell = document.createElement('td')
      referenceCell.textContent = row.reference || '—'
      const descriptionCell = document.createElement('td')
      descriptionCell.textContent = row.description || '—'
      const receiptCell = document.createElement('td')
      if (row.receipt_path) {
        const link = document.createElement('a')
        link.href = `/files-records/${encodeURI(row.receipt_path)}`
        link.textContent = 'Receipt'
        link.target = '_blank'
        link.rel = 'noopener noreferrer'
        receiptCell.appendChild(link)
      } else {
        receiptCell.textContent = '—'
      }

      const actionsCell = document.createElement('td')
      const actions = document.createElement('div')
      actions.className = 'row-actions'
      const editBtn = document.createElement('button')
      editBtn.type = 'button'
      editBtn.textContent = 'Edit'
      editBtn.addEventListener('click', () => {
        fillExpenseForm(row)
      })
      const deleteBtn = document.createElement('button')
      deleteBtn.type = 'button'
      deleteBtn.textContent = 'Delete'
      deleteBtn.addEventListener('click', () => {
        if (!confirm('Delete this expense?')) return
        deleteExpense(row.id).catch(console.error)
      })
      actions.appendChild(editBtn)
      actions.appendChild(deleteBtn)
      actionsCell.appendChild(actions)

      tr.appendChild(dateCell)
      tr.appendChild(vendorCell)
      tr.appendChild(categoryCell)
      tr.appendChild(amountCell)
      tr.appendChild(paymentCell)
      tr.appendChild(referenceCell)
      tr.appendChild(descriptionCell)
      tr.appendChild(receiptCell)
      tr.appendChild(actionsCell)
      expenseTableBody.appendChild(tr)
    })
  }

  const fillExpenseForm = (row) => {
    editingExpenseId = row.id
    expenseDateInput.value = row.expense_date || ''
    expenseVendorInput.value = row.vendor || ''
    expenseCategoryInput.value = row.category || ''
    expenseAmountInput.value = row.amount || ''
    expensePaymentInput.value = row.payment_method || 'Card'
    expenseReferenceInput.value = row.reference || ''
    expenseDescriptionInput.value = row.description || ''
    expenseReceiptInput.value = ''
    expenseSaveBtn.textContent = 'Update Expense'
    expenseCancelBtn.hidden = false
  }

  const saveExpense = async () => {
    const payload = {
      expense_date: expenseDateInput.value.trim(),
      vendor: expenseVendorInput.value.trim(),
      category: expenseCategoryInput.value.trim(),
      amount: expenseAmountInput.value.trim(),
      payment_method: expensePaymentInput.value,
      reference: expenseReferenceInput.value.trim(),
      description: expenseDescriptionInput.value.trim(),
      receipt_path: '',
    }
    if (!payload.expense_date || !payload.amount) {
      setStatus(expenseStatus, 'Date and amount are required.')
      return
    }
    if (editingExpenseId) {
      const existing = expenses.find((row) => row.id === editingExpenseId)
      payload.receipt_path = existing?.receipt_path || ''
    }
    if (expenseReceiptInput.files && expenseReceiptInput.files[0]) {
      try {
        payload.receipt_path = await uploadReceipt(expenseReceiptInput.files[0])
      } catch (error) {
        setStatus(expenseStatus, error.message)
        return
      }
    }
    const body = editingExpenseId
      ? { action: 'update', id: editingExpenseId, expense: payload }
      : { action: 'create', expense: payload }
    const response = await fetch('/api/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(expenseStatus, data.error || 'Failed to save expense.')
      return
    }
    setStatus(expenseStatus, editingExpenseId ? 'Expense updated.' : 'Expense saved.')
    resetExpenseForm()
    await loadExpenses()
  }

  const deleteExpense = async (expenseId) => {
    const response = await fetch('/api/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id: expenseId }),
    })
    const data = await response.json()
    if (!response.ok) {
      setStatus(expenseStatus, data.error || 'Failed to delete expense.')
      return
    }
    await loadExpenses()
  }

  const toCsv = (rows) => {
    const escapeValue = (value) => {
      const stringValue = value == null ? '' : String(value)
      if (/["]|,|\n|\r/.test(stringValue)) {
        return `"${stringValue.replace(/"/g, '""')}"`
      }
      return stringValue
    }
    const header = ['date', 'vendor', 'category', 'amount', 'payment_method', 'reference', 'description', 'receipt_path']
    const lines = [
      header.map(escapeValue).join(','),
      ...rows.map((row) =>
        [
          row.expense_date,
          row.vendor,
          row.category,
          row.amount,
          row.payment_method,
          row.reference,
          row.description,
          row.receipt_path,
        ]
          .map(escapeValue)
          .join(',')
      ),
    ]
    return lines.join('\n')
  }

  const downloadCsv = (filename, content) => {
    const blob = new Blob([content], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  const updateTotals = () => {
    const totals = new Map()
    expenses.forEach((row) => {
      const year = (row.expense_date || '').slice(0, 4)
      if (!year) return
      const amount = parseFloat(row.amount || 0) || 0
      totals.set(year, (totals.get(year) || 0) + amount)
    })
    const years = Array.from(totals.keys()).sort((a, b) => b.localeCompare(a))
    totalsYearSelect.innerHTML = ''
    years.forEach((year) => {
      const option = document.createElement('option')
      option.value = year
      option.textContent = year
      totalsYearSelect.appendChild(option)
    })
    if (years.length) {
      const currentYear = String(new Date().getFullYear())
      totalsYearSelect.value = years.includes(currentYear) ? currentYear : years[0]
      const totalValue = totals.get(totalsYearSelect.value) || 0
      totalsAmount.textContent = `${totalValue.toFixed(2)} GBP`
    } else {
      totalsAmount.textContent = '0.00 GBP'
    }
  }

  const exportExpenses = () => {
    if (!expenses.length) {
      setStatus(expenseStatus, 'No expenses to export.')
      return
    }
    downloadCsv('expenses.csv', toCsv(expenses))
  }

  const exportTotals = () => {
    const totals = {}
    expenses.forEach((row) => {
      const year = (row.expense_date || '').slice(0, 4)
      if (!year) return
      const amount = parseFloat(row.amount || 0) || 0
      totals[year] = (totals[year] || 0) + amount
    })
    const lines = ['year,total']
    Object.keys(totals)
      .sort()
      .forEach((year) => {
        lines.push(`${year},${totals[year].toFixed(2)}`)
      })
    downloadCsv('expense_totals.csv', lines.join('\n'))
  }

  supplySaveBtn.addEventListener('click', () => saveSupply().catch(console.error))
  supplyCancelBtn.addEventListener('click', () => {
    resetSupplyForm()
    setStatus(supplyStatus, '')
  })
  supplySearchInput.addEventListener('input', applySupplyFilter)

  expenseSaveBtn.addEventListener('click', () => saveExpense().catch(console.error))
  expenseCancelBtn.addEventListener('click', () => {
    resetExpenseForm()
    setStatus(expenseStatus, '')
  })
  totalsYearSelect.addEventListener('change', () => {
    const year = totalsYearSelect.value
    const totalValue = expenses.reduce((sum, row) => {
      if ((row.expense_date || '').startsWith(year)) {
        return sum + (parseFloat(row.amount || 0) || 0)
      }
      return sum
    }, 0)
    totalsAmount.textContent = `${totalValue.toFixed(2)} GBP`
  })
  exportExpensesBtn.addEventListener('click', exportExpenses)
  exportTotalsBtn.addEventListener('click', exportTotals)

  logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' })
    window.location.href = '/login'
  })

  resetSupplyForm()
  resetExpenseForm()
  loadSupplies().catch(console.error)
  loadExpenses().catch(console.error)
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
        <h1 class="title">Supplies & Expenses</h1>
        <p class="subtitle">Track materials, packaging, and business expenses.</p>
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
      <h2>Supplies inventory</h2>
      <div class="grid">
        <div>
          <label for="supplyName">Supply name</label>
          <input id="supplyName" type="text" placeholder="PLA Black" />
        </div>
        <div>
          <label for="supplyCategory">Category</label>
          <input id="supplyCategory" type="text" placeholder="Filament, Boxes, Bags" />
        </div>
        <div>
          <label for="supplyUnit">Unit</label>
          <input id="supplyUnit" type="text" placeholder="spool, pack, roll" />
        </div>
        <div>
          <label for="supplyQty">Quantity</label>
          <input id="supplyQty" type="number" min="0" value="0" />
        </div>
        <div>
          <label for="supplyReorder">Reorder point</label>
          <input id="supplyReorder" type="number" min="0" value="0" />
        </div>
        <div>
          <label for="supplyVendor">Vendor</label>
          <input id="supplyVendor" type="text" placeholder="Supplier name" />
        </div>
        <div>
          <label for="supplyLeadTime">Lead time (days)</label>
          <input id="supplyLeadTime" type="number" min="0" value="0" />
        </div>
        <div>
          <label for="supplyLocation">Location</label>
          <input id="supplyLocation" type="text" placeholder="Shelf A" />
        </div>
        <div>
          <label for="supplyNotes">Notes</label>
          <input id="supplyNotes" type="text" placeholder="Colour, batch, etc." />
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="supplySaveBtn" class="btn" type="button">Save Supply</button>
        <button id="supplyCancelBtn" class="btn ghost" type="button" hidden>Cancel edit</button>
      </div>
      <div class="status" id="supplyStatus"></div>
    </section>

    <section class="card">
      <h2>Supplies list</h2>
      <div class="controls" style="margin-bottom: 12px;">
        <input id="supplySearch" type="search" placeholder="Search supplies..." />
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Qty</th>
              <th>Reorder</th>
              <th>Vendor</th>
              <th>Lead</th>
              <th>Location</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="supplyTableBody"></tbody>
        </table>
        <div class="empty" id="supplyEmpty">No supplies yet.</div>
      </div>
    </section>

    <section class="card">
      <h2>Expenses</h2>
      <div class="grid">
        <div>
          <label for="expenseDate">Date</label>
          <input id="expenseDate" type="date" />
        </div>
        <div>
          <label for="expenseVendor">Vendor</label>
          <input id="expenseVendor" type="text" placeholder="Supplier name" />
        </div>
        <div>
          <label for="expenseCategory">Tax category</label>
          <input id="expenseCategory" type="text" placeholder="Materials, Shipping, Equipment" />
        </div>
        <div>
          <label for="expenseAmount">Amount (GBP)</label>
          <input id="expenseAmount" type="number" min="0" step="0.01" placeholder="0.00" />
        </div>
        <div>
          <label for="expensePayment">Payment method</label>
          <select id="expensePayment">
            <option value="Card">Card</option>
            <option value="Cash">Cash</option>
            <option value="Bank Transfer">Bank Transfer</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label for="expenseReference">Invoice/Reference</label>
          <input id="expenseReference" type="text" placeholder="Invoice # or reference" />
        </div>
        <div>
          <label for="expenseDescription">Description</label>
          <input id="expenseDescription" type="text" placeholder="What was purchased" />
        </div>
        <div>
          <label for="expenseReceipt">Receipt upload</label>
          <input id="expenseReceipt" type="file" />
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="expenseSaveBtn" class="btn secondary" type="button">Save Expense</button>
        <button id="expenseCancelBtn" class="btn ghost" type="button" hidden>Cancel edit</button>
      </div>
      <div class="status" id="expenseStatus"></div>
    </section>

    <section class="card">
      <h2>Expense totals</h2>
      <div class="grid">
        <div>
          <label for="totalsYearSelect">Year</label>
          <select id="totalsYearSelect"></select>
        </div>
        <div>
          <label>Total spend</label>
          <div class="status" id="totalsAmount">0.00 GBP</div>
        </div>
      </div>
      <div class="actions" style="margin-top: 12px;">
        <button id="exportExpensesBtn" class="btn ghost" type="button">Export Expenses CSV</button>
        <button id="exportTotalsBtn" class="btn ghost" type="button">Export Totals CSV</button>
      </div>
    </section>

    <section class="card">
      <h2>Expense ledger</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Vendor</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Payment</th>
              <th>Reference</th>
              <th>Description</th>
              <th>Receipt</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="expenseTableBody"></tbody>
        </table>
        <div class="empty" id="expenseEmpty">No expenses yet.</div>
      </div>
    </section>
  </main>
</template>
