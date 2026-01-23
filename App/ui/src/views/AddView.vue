<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
const categorySelect = document.getElementById("category");
      const descriptionInput = document.getElementById("description");
      const createDialog = document.getElementById("createDialog");
      const openDialogBtn = null;
      const cancelBtn = document.getElementById("cancelBtn");
      const createBtn = document.getElementById("createBtn");
      const statusEl = document.getElementById("status");

      const loadCategories = async () => {
        const response = await fetch("/api/rows", { cache: "no-store" });
        if (!response.ok) return;
        const data = await response.json();
        const headers = data.headers || [];
        const rows = data.rows || [];
        const categoryIndex = headers.indexOf("category");
        const categories = new Set();
        rows.forEach((row) => {
          const value = row["category"] ?? (categoryIndex > -1 ? row[categoryIndex] : "");
          if (value) categories.add(value);
        });
        categorySelect.innerHTML = "";
        [...categories].sort().forEach((category) => {
          const option = document.createElement("option");
          option.value = category;
          option.textContent = category;
          categorySelect.appendChild(option);
        });
        if (!categories.has("B2B")) {
          const option = document.createElement("option");
          option.value = "B2B";
          option.textContent = "B2B";
          categorySelect.appendChild(option);
        }
      };

      const createProduct = async () => {
        const category = categorySelect.value;
        const description = descriptionInput.value.trim();
        const tags = "";
        const requiresUkca = false;
        const notes = "";
        if (!category || !description) {
          statusEl.textContent = "Category and description are required.";
          return;
        }
        createBtn.disabled = true;
        statusEl.textContent = "Creating product...";
        try {
          const response = await fetch("/api/add_product", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              category,
              description,
              tags,
              requires_ukca: requiresUkca,
              notes,
            }),
          });
          const payload = await response.json();
          if (!response.ok) {
            statusEl.textContent = payload.error || "Create failed.";
            return;
          }
          statusEl.textContent = `Created ${payload.row?.product_folder || "product"}.`;
          const folder = payload.row?.product_folder || "";
          if (createDialog.close) {
            createDialog.close();
          } else {
            createDialog.removeAttribute("open");
          }
          if (folder) {
            const url = `/product?category=${encodeURIComponent(category)}&folder=${encodeURIComponent(folder)}&status=draft`;
            window.location.href = url;
          }
        } catch (error) {
          console.error(error);
          statusEl.textContent = "Create failed.";
        } finally {
          createBtn.disabled = false;
        }
      };

      const openDialog = () => {
        if (createDialog.showModal) {
          createDialog.showModal();
        } else {
          createDialog.setAttribute("open", "true");
        }
        descriptionInput.focus();
      };
      cancelBtn.addEventListener("click", () => {
        if (createDialog.close) {
          createDialog.close();
        } else {
          createDialog.removeAttribute("open");
        }
      });
      createBtn.addEventListener("click", () => createProduct().catch(console.error));
      loadCategories()
        .then(() => openDialog())
        .catch(console.error);
})
</script>

<template>
<header>
      <nav class="nav">
        <div class="nav-brand">
          <img src="/logo.png" alt="Geeky Things logo" />
          <strong>GeekyThings</strong>
        </div>
        <div class="nav-links">
          <RouterLink to="/">Products</RouterLink>
          <RouterLink to="/add">Add Product</RouterLink>
        </div>
      </nav>
    </header>
    <img src="/logo.png" alt="Geeky Things logo" class="logo" />
    <h1>Add New Product</h1>
    <div class="version">
      Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
    </div>
    <p>Create a draft product by entering a category and name.</p>

    <div class="card">
      <div class="status" id="status"></div>
    </div>

    <dialog id="createDialog">
      <div class="dialog-header">
        <h2>New Draft Product</h2>
      </div>
      <div class="dialog-body">
        <div>
          <label for="category">Category</label>
          <select id="category"></select>
        </div>
        <div>
          <label for="description">Product name</label>
          <input id="description" type="text" placeholder="e.g. Dragon Bookmark" />
        </div>
      </div>
      <div class="dialog-actions">
        <button id="cancelBtn" class="btn ghost" type="button">Cancel</button>
        <button id="createBtn" class="btn" type="button">Create</button>
      </div>
    </dialog>
</template>
