<template>
  <div class="admin-login-container">
    <div class="bg-photo"></div>

    <div class="card">
      <!-- LEFT FORM -->
      <div class="left">
        <div class="heading">欢迎回来</div>
        <div class="sub-text">请登录您的管理账号</div>

        <div class="field-group">
          <label class="field-label" for="username">用户名</label>
          <input 
            v-model.trim="username"
            class="field-input" 
            id="username" 
            type="text" 
            placeholder="请输入用户名" 
            autocomplete="username"
            @keyup.enter="submit"
          />
        </div>

        <div class="field-group">
          <label class="field-label" for="password">密码</label>
          <input 
            v-model="password"
            class="field-input" 
            id="password" 
            type="password" 
            placeholder="请输入密码" 
            autocomplete="current-password"
            @keyup.enter="submit"
          />
        </div>

        <div class="remember-row">
          <input type="checkbox" id="remember" v-model="rememberMe" />
          <label for="remember">记住账号</label>
        </div>

        <p class="error-msg" v-if="error">{{ error }}</p>

        <button class="signin-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '验证中...' : '登录' }}
        </button>

        <div class="back-link">
          <RouterLink to="/">返回主页</RouterLink>
        </div>
      </div>

      <!-- RIGHT PHOTO -->
      <div class="right">
        <div class="photo-bg"></div>
        <div class="portrait">
          <img src="/assets/admin_login_cat.png" alt="Login Visual" class="login-cat-img" />
        </div>
        <div class="photo-overlay"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '../../shared/http'
import { useKonaStore } from '../../stores/composables'

const router = useRouter()
const store = useKonaStore()

const username = ref('')
const password = ref('')
const rememberMe = ref(true)
const error = ref('')
const submitting = ref(false)

async function submit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  
  error.value = ''
  submitting.value = true
  try {
    await store.login(username.value, password.value)
    // 验证管理员权限
    await api.get('/api/admin/overview')
    await router.push('/admin/overview')
  } catch (e) {
    await store.logout()
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

.admin-login-container {
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a0a05;
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
  position: relative;
}

/* Full-bleed blurred photo background */
.bg-photo {
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse at 15% 50%, rgba(210,80,20,0.55) 0%, transparent 45%),
    radial-gradient(ellipse at 85% 20%, rgba(20,160,155,0.5) 0%, transparent 40%),
    radial-gradient(ellipse at 60% 80%, rgba(180,60,10,0.4) 0%, transparent 40%),
    linear-gradient(135deg, #8b3a10 0%, #1a3a38 50%, #0d1a18 100%);
}

.bg-photo::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.25);
}

/* CARD */
.card {
  position: relative;
  z-index: 1;
  display: flex;
  width: 900px;
  max-width: 97vw;
  min-height: 580px;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 40px 120px rgba(0,0,0,0.55), 0 8px 32px rgba(0,0,0,0.3);
}

/* ── LEFT: FORM ── */
.left {
  width: 52%;
  flex-shrink: 0;
  background: #f4f4f2;
  padding: 64px 58px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.heading {
  font-family: 'Playfair Display', serif;
  font-size: 38px;
  font-weight: 800;
  color: #0f0f0f;
  letter-spacing: -.02em;
  line-height: 1.15;
  margin-bottom: 8px;
}

.sub-text {
  font-size: 14px;
  color: #888;
  font-weight: 400;
  margin-bottom: 40px;
  letter-spacing: .01em;
}

/* Labels */
.field-group {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 7px;
  letter-spacing: .01em;
}

/* Input */
.field-input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  background: #fff;
  border: 1.5px solid #d8d8d8;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: #1a1a1a;
  outline: none;
  transition: border-color .18s, box-shadow .18s;
  letter-spacing: .01em;
}

.field-input::placeholder {
  color: #bbb;
  font-weight: 400;
}

.field-input:focus {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.06);
}

/* Remember row */
.remember-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0 24px;
}

.remember-row input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: #1a1a1a;
  cursor: pointer;
  flex-shrink: 0;
  border-radius: 3px;
}

.remember-row label {
  font-size: 13px;
  color: #555;
  font-weight: 400;
  cursor: pointer;
  user-select: none;
}

.error-msg {
  color: #e04030;
  font-size: 13px;
  margin-bottom: 16px;
  font-weight: 500;
}

/* Sign in button */
.signin-btn {
  width: 100%;
  height: 48px;
  background: #0f0f0f;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: .02em;
  transition: background .15s, transform .12s, box-shadow .15s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.18);
}

.signin-btn:hover:not(:disabled) {
  background: #2a2a2a;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.signin-btn:active:not(:disabled) {
  transform: translateY(0);
}

.signin-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.back-link {
  margin-top: 24px;
  text-align: center;
}

.back-link a {
  font-size: 13px;
  color: #888;
  text-decoration: none;
  transition: color 0.15s;
}

.back-link a:hover {
  color: #1a1a1a;
}

/* ── RIGHT: PHOTO ── */
.right {
  flex: 1;
  position: relative;
  overflow: hidden;
  border-radius: 0 20px 20px 0;
}

.photo-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 55% 35%, rgba(240,200,160,0.95) 0%, rgba(200,130,80,0.7) 25%, transparent 55%),
    radial-gradient(ellipse at 75% 65%, rgba(180,60,20,0.8) 0%, rgba(140,40,10,0.5) 35%, transparent 60%),
    radial-gradient(ellipse at 30% 55%, rgba(230,120,40,0.6) 0%, transparent 45%),
    radial-gradient(ellipse at 80% 20%, rgba(20,155,155,0.7) 0%, rgba(10,100,100,0.4) 30%, transparent 55%),
    radial-gradient(ellipse at 20% 80%, rgba(200,80,20,0.5) 0%, transparent 40%),
    linear-gradient(160deg, #c5e8e6 0%, #7ab8b5 20%, #2a6a68 45%, #1a2a28 80%, #0d1612 100%);
}

.photo-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(85deg,
      transparent 20%,
      rgba(230,180,100,0.15) 28%,
      rgba(220,100,30,0.12) 32%,
      transparent 38%,
      rgba(200,60,20,0.1) 45%,
      transparent 52%,
      rgba(20,140,140,0.12) 60%,
      transparent 68%,
      rgba(210,90,30,0.1) 75%,
      transparent 82%
    );
  filter: blur(3px);
}

.photo-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60px 80px at 52% 30%, rgba(240,215,185,0.9) 0%, rgba(220,180,140,0.5) 50%, transparent 80%),
    radial-gradient(ellipse 30px 40px at 52% 38%, rgba(200,150,110,0.7) 0%, transparent 70%);
  filter: blur(1px);
}

.photo-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(
    to right,
    rgba(244,244,242,0.08) 0%,
    transparent 15%
  );
}

.right::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 3;
  border-radius: 0 20px 20px 0;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
  pointer-events: none;
}

.portrait {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-cat-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

@media (max-width: 920px) {
  .card {
    width: 480px;
    min-height: auto;
  }
  .right {
    display: none;
  }
  .left {
    width: 100%;
    padding: 48px 40px;
  }
}
</style>
