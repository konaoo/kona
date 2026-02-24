<template>
  <section class="auth-page">
    <div class="bg" aria-hidden="true">
      <span class="blob b1"></span>
      <span class="blob b2"></span>
      <span class="blob b3"></span>
      <span class="grid"></span>
      <span class="sparkle s1"></span>
      <span class="sparkle s2"></span>
      <span class="sparkle s3"></span>
    </div>

    <div class="container">
      <header class="topbar">
        <div class="brand">
          <img class="brand-logo" src="/assets/kaka-logo.png" alt="logo" />
          <div class="brand-text">
            <div class="brand-name">咔咔记账</div>
            <div class="brand-sub">GLOBAL ASSET DESK</div>
          </div>
        </div>
      </header>

      <main class="center">
        <div class="card">
          <div class="card-head">
            <h1 class="card-title">{{ isRegisterRoute ? '注册' : '登录' }}</h1>
            <p class="card-sub">{{ isRegisterRoute ? '创建账号' : '欢迎回来' }}</p>
          </div>

          <form class="form" @submit.prevent="submit">
            <label class="field">
              <span class="label">用户名</span>
              <input
                v-model.trim="username"
                class="input"
                type="text"
                placeholder="请输入用户名"
                autocomplete="username"
              />
            </label>

            <label class="field">
              <span class="label">密码</span>
              <input
                v-model="password"
                class="input"
                type="password"
                placeholder="请输入密码"
                :autocomplete="isRegisterRoute ? 'new-password' : 'current-password'"
              />
            </label>

            <label v-if="isRegisterRoute" class="field">
              <span class="label">确认密码</span>
              <input
                v-model="confirmPassword"
                class="input"
                type="password"
                placeholder="请再次输入密码"
                autocomplete="new-password"
              />
            </label>

            <label v-if="isRegisterRoute" class="field">
              <span class="label">邀请码</span>
              <input v-model.trim="inviteCode" class="input" type="text" placeholder="输入邀请码" />
            </label>

            <div v-else class="row">
              <label class="check">
                <input v-model="rememberMe" type="checkbox" />
                <span>记住我</span>
              </label>
            </div>

            <div class="error" v-if="error">{{ error }}</div>

            <button class="auth-btn primary" :disabled="submitting" type="submit">
              {{ submitting ? '提交中...' : (isRegisterRoute ? '注册并登录' : '登录') }}
            </button>

            <div v-if="!isRegisterRoute" class="foot">
              <span class="foot-text">还没有账户？</span>
              <RouterLink class="foot-link" to="/app/register">立即注册</RouterLink>
            </div>

            <div v-else class="foot">
              <span class="foot-text">已有账户？</span>
              <RouterLink class="foot-link" to="/app/login">立即登录</RouterLink>
            </div>
          </form>
        </div>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useRoute, useRouter } from 'vue-router'
import { useKonaStore } from '../../shared/store'

const REMEMBER_ENABLED_KEY = 'kona_web_remember_enabled'
const REMEMBER_USERNAME_KEY = 'kona_web_remember_username'
const REMEMBER_PASSWORD_KEY = 'kona_web_remember_password'
const USERNAME_PATTERN = /^[a-z][a-z0-9_]{3,23}$/
const RESERVED_USERNAMES = new Set([
  'admin',
  'administrator',
  'root',
  'system',
  'support',
  'service',
  'security',
  'owner',
])

const router = useRouter()
const route = useRoute()
const store = useKonaStore()

const submitting = ref(false)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const inviteCode = ref('')
const rememberMe = ref(false)
const error = ref('')
const isRegisterRoute = computed(() => route.path === '/app/register')

function readRememberFields() {
  if (typeof window === 'undefined') return
  rememberMe.value = localStorage.getItem(REMEMBER_ENABLED_KEY) === '1'
  if (!rememberMe.value) return
  username.value = localStorage.getItem(REMEMBER_USERNAME_KEY) || ''
  password.value = localStorage.getItem(REMEMBER_PASSWORD_KEY) || ''
}

function persistRememberFields() {
  if (typeof window === 'undefined') return
  if (rememberMe.value) {
    localStorage.setItem(REMEMBER_ENABLED_KEY, '1')
    localStorage.setItem(REMEMBER_USERNAME_KEY, username.value)
    localStorage.setItem(REMEMBER_PASSWORD_KEY, password.value)
    return
  }
  localStorage.setItem(REMEMBER_ENABLED_KEY, '0')
  localStorage.removeItem(REMEMBER_USERNAME_KEY)
  localStorage.removeItem(REMEMBER_PASSWORD_KEY)
}

function isValidUsername(value: string): boolean {
  const normalized = (value || '').trim().toLowerCase()
  return USERNAME_PATTERN.test(normalized) && !RESERVED_USERNAMES.has(normalized)
}

function isValidPassword(value: string): boolean {
  const text = String(value || '')
  if (text.length < 8 || text.length > 64) return false
  if (!/[A-Za-z]/.test(text)) return false
  if (!/\d/.test(text)) return false
  return true
}

function normalizeErrorText(raw: unknown): string {
  return String(raw || '').trim().toLowerCase()
}

function mapRegisterError(err: unknown): string {
  const status = Number((err as { status?: unknown })?.status || 0)
  const message = normalizeErrorText((err as { message?: unknown })?.message)

  if (status === 409 || message.includes('username already exists')) {
    return '该用户名已被占用，请更换后重试'
  }
  if (message.includes('missing invite code')) {
    return '请填写邀请码'
  }
  if (message.includes('invite code invalid') || message.includes('already used')) {
    return '邀请码无效或已被使用，请核对后重试'
  }
  if (
    message.includes('password') ||
    message.includes('weak') ||
    message.includes('letters') ||
    message.includes('numbers') ||
    message.includes('8-64')
  ) {
    return '密码需为 8-64 位，且同时包含字母和数字'
  }
  if (message.includes('invalid username')) {
    return '用户名需以小写字母开头，仅支持小写字母、数字和下划线，长度 4-24 位'
  }
  return '注册失败，请稍后重试'
}

function mapLoginError(err: unknown): string {
  const status = Number((err as { status?: unknown })?.status || 0)
  const message = normalizeErrorText((err as { message?: unknown })?.message)

  if (message.includes('missing username or password')) {
    return '请输入用户名和密码'
  }
  if (status === 401 || message.includes('invalid username or password')) {
    return '用户名或密码错误'
  }
  if (status === 403 || message.includes('user is disabled')) {
    return '当前账号已被禁用，请联系管理员'
  }
  if (message.includes('password not set')) {
    return '当前账号尚未设置密码，请联系管理员处理'
  }
  if (status >= 500) {
    return '登录失败，请稍后重试'
  }
  return '登录失败，请检查后重试'
}

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    if (isRegisterRoute.value) {
      if (!isValidUsername(username.value)) {
        error.value = '用户名需以小写字母开头，仅支持小写字母、数字和下划线，长度 4-24 位'
        return
      }
      if (!isValidPassword(password.value)) {
        error.value = '密码需为 8-64 位，且同时包含字母和数字'
        return
      }
      if (confirmPassword.value !== password.value) {
        error.value = '两次输入的密码不一致，请重新输入'
        return
      }
      if (!String(inviteCode.value || '').trim()) {
        error.value = '请填写邀请码'
        return
      }
      await store.register(username.value, password.value, inviteCode.value)
    } else {
      if (!String(username.value || '').trim() || !String(password.value || '').trim()) {
        error.value = '请输入用户名和密码'
        return
      }
      await store.login(username.value, password.value)
      persistRememberFields()
    }
    await router.push('/app/home')
  } catch (e) {
    error.value = isRegisterRoute.value ? mapRegisterError(e) : mapLoginError(e)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (isRegisterRoute.value) return
  readRememberFields()
})
</script>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(900px 600px at 18% 18%, rgba(255, 120, 80, 0.2), transparent 60%),
    radial-gradient(860px 640px at 82% 22%, rgba(255, 60, 160, 0.16), transparent 58%),
    radial-gradient(860px 620px at 70% 92%, rgba(99, 102, 241, 0.18), transparent 55%),
    linear-gradient(135deg, #fff7f1 0%, #f2f7ff 55%, #f6f2ff 100%);
}

.bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 999px;
  filter: blur(44px);
  opacity: 0.9;
  animation: float 11s ease-in-out infinite;
  transform: translateZ(0);
}

.b1 {
  width: 520px;
  height: 520px;
  left: -170px;
  top: -170px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 90, 120, 0.7), rgba(255, 180, 80, 0.22));
}

.b2 {
  width: 560px;
  height: 560px;
  right: -200px;
  top: 40px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 70, 170, 0.55), rgba(99, 102, 241, 0.2));
  animation-delay: -3s;
}

.b3 {
  width: 560px;
  height: 560px;
  right: 90px;
  bottom: -260px;
  background: radial-gradient(circle at 30% 30%, rgba(99, 102, 241, 0.55), rgba(56, 189, 248, 0.2));
  animation-delay: -6s;
}

.grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(15, 23, 42, 0.07) 1px, transparent 1px);
  background-size: 18px 18px;
  mask-image: radial-gradient(circle at 40% 25%, #000 0%, transparent 58%);
  opacity: 0.55;
}

.sparkle {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 4px;
  background: linear-gradient(135deg, #ff4d8d, #6366f1);
  box-shadow: 0 12px 26px rgba(99, 102, 241, 0.22);
  opacity: 0.85;
}

.s1 {
  left: 18%;
  top: 24%;
  transform: rotate(18deg);
}

.s2 {
  left: 68%;
  top: 18%;
  transform: rotate(-10deg);
}

.s3 {
  left: 78%;
  top: 66%;
  transform: rotate(22deg);
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(18px);
  }
}

.container {
  position: relative;
  max-width: 1180px;
  margin: 0 auto;
  padding: 26px 28px 34px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 6px 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.1);
  object-fit: contain;
  display: block;
}

.brand-text {
  line-height: 1.05;
}

.brand-name {
  font-weight: 900;
  letter-spacing: 0.2px;
  color: #0f172a;
}

.brand-sub {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.5);
  font-weight: 800;
  letter-spacing: 1.6px;
}

.center {
  min-height: calc(100vh - 88px);
  display: grid;
  place-items: center;
  padding: 10px 6px 26px;
}

.card {
  width: min(520px, 92vw);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 26px 70px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  padding: 22px;
  position: relative;
}

.card::before {
  content: '';
  position: absolute;
  inset: 10px;
  border-radius: 22px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  pointer-events: none;
}

.card-head {
  padding: 6px 8px 14px;
  text-align: center;
}

.card-title {
  margin: 4px 0 0;
  font-size: 22px;
  font-weight: 950;
  letter-spacing: -0.2px;
  color: #0f172a;
}

.card-sub {
  margin: 8px 0 0;
  font-size: 13px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.55);
}

.form {
  padding: 10px 10px 6px;
  display: grid;
  gap: 14px;
}

.field {
  display: grid;
  gap: 8px;
}

.label {
  font-size: 13px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.7);
}

.input {
  width: 100%;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  outline: none;
  font-size: 14px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.88);
  transition: box-shadow 220ms ease, transform 220ms ease, border-color 220ms ease;
}

.input:focus {
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.14), 0 12px 26px rgba(15, 23, 42, 0.1);
  transform: translateY(-1px);
}

.row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  margin-top: 2px;
}

.check {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.7);
}

.check input {
  width: 16px;
  height: 16px;
  accent-color: #ff4d8d;
}

.error {
  color: #ff5d84;
  font-size: 14px;
  line-height: 1.45;
  border: 1px solid rgba(173, 73, 99, 0.45);
  background: rgba(81, 27, 42, 0.26);
  border-radius: 16px;
  padding: 12px 14px;
}

.auth-btn {
  border: none;
  cursor: pointer;
  font-weight: 950;
  letter-spacing: 0.2px;
  border-radius: 18px;
  padding: 14px 18px;
  transition: transform 220ms ease, box-shadow 220ms ease;
  user-select: none;
}

.auth-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #ff4d8d, #6366f1);
  box-shadow: 0 18px 46px rgba(99, 102, 241, 0.26);
  margin-top: 4px;
}

.auth-btn.primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 26px 64px rgba(99, 102, 241, 0.32);
}

.auth-btn:disabled {
  opacity: 0.72;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.foot {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 4px;
  padding-bottom: 6px;
}

.foot-text,
.foot-link {
  font-size: 14px;
  font-weight: 900;
  line-height: 1;
}

.foot-text {
  color: rgba(15, 23, 42, 0.55);
}

.foot-link {
  color: rgba(255, 77, 141, 0.95);
  text-decoration: none;
}

.foot-link:hover {
  text-decoration: underline;
}

@media (max-width: 520px) {
  .container {
    padding: 18px 16px 22px;
  }

  .center {
    min-height: calc(100vh - 78px);
  }

  .card {
    padding: 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .blob {
    animation: none;
  }

  .auth-btn,
  .input {
    transition: none;
  }
}
</style>
