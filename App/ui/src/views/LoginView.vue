<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
  const form = document.getElementById('loginForm')
  const statusEl = document.getElementById('loginStatus')
  const usernameInput = document.getElementById('username')
  const passwordInput = document.getElementById('password')

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    statusEl.textContent = 'Signing in...'
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: usernameInput.value.trim(),
          password: passwordInput.value,
        }),
      })
      if (!response.ok) {
        statusEl.textContent = 'Invalid credentials.'
        return
      }
      window.location.href = '/'
    } catch (error) {
      console.error(error)
      statusEl.textContent = 'Login failed.'
    }
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
    </nav>
  </header>

  <main>
    <section class="card" style="max-width: 420px; margin: 40px auto;">
      <h1 class="title" style="margin-bottom: 8px;">Sign in</h1>
      <p class="subtitle">Enter your credentials to access the product manager.</p>
      <form id="loginForm" style="margin-top: 16px; display: grid; gap: 12px;">
        <div>
          <label for="username">Username</label>
          <input id="username" type="text" autocomplete="username" required />
        </div>
        <div>
          <label for="password">Password</label>
          <input id="password" type="password" autocomplete="current-password" required />
        </div>
        <button class="btn" type="submit">Sign in</button>
      </form>
      <div class="status" id="loginStatus" style="margin-top: 10px;"></div>
      <div class="version" style="margin-top: 18px;">
        Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
      </div>
    </section>
  </main>
</template>
