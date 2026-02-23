<template>
  <div class="auth-wrap page-wrap">
    <div class="auth-shell panel">
      <div class="auth-brand">咔咔记账</div>
      <section class="auth">
        <div class="auth-topbar">
          <button class="back-arrow-btn" type="button" aria-label="返回" @click="goBack">←</button>
        </div>

        <label>
          用户名
          <input
            v-model.trim="username"
            class="input"
            placeholder="小写字母开头，4-24位"
            autocomplete="username"
          />
        </label>

        <label>
          密码
          <input
            v-model="password"
            class="input"
            type="password"
            placeholder="8-64位，包含字母和数字"
            :autocomplete="isRegisterRoute ? 'new-password' : 'current-password'"
          />
        </label>

        <label v-if="isRegisterRoute">
          邀请码
          <input v-model.trim="inviteCode" class="input" placeholder="输入邀请码" />
        </label>

        <label v-else class="remember-row">
          <input v-model="rememberMe" type="checkbox" class="remember-check" />
          <span>记住我</span>
        </label>

        <div class="error" v-if="error">{{ error }}</div>

        <button class="btn primary submit-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中...' : (isRegisterRoute ? '注册并登录' : '登录') }}
        </button>

        <p v-if="!isRegisterRoute" class="register-hint">
          <span>还没有账户？</span>
          <RouterLink class="register-hint-link" to="/app/register">立即注册</RouterLink>
        </p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { useKonaStore } from '../../shared/store'

const REMEMBER_ENABLED_KEY = 'kona_web_remember_enabled'
const REMEMBER_USERNAME_KEY = 'kona_web_remember_username'
const REMEMBER_PASSWORD_KEY = 'kona_web_remember_password'

const router = useRouter()
const route = useRoute()
const store = useKonaStore()

const submitting = ref(false)
const username = ref('')
const password = ref('')
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

function goBack() {
  if (typeof window !== 'undefined' && window.history.length > 1) {
    router.back()
    return
  }
  void router.push('/')
}

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    if (isRegisterRoute.value) {
      await store.register(username.value, password.value, inviteCode.value)
    } else {
      await store.login(username.value, password.value)
      persistRememberFields()
    }
    await router.push('/app/home')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '请求失败'
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
.auth-wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  max-width: 640px;
}

.auth-shell {
  width: min(460px, 100%);
  padding: 18px;
}

.auth-brand {
  margin: 0 0 10px;
  text-align: center;
  font-size: 22px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: rgba(226, 235, 255, 0.9);
}

.auth {
  border-radius: 14px;
  border: 1px solid rgba(98, 130, 182, 0.24);
  background: linear-gradient(150deg, rgba(16, 27, 47, 0.93), rgba(11, 20, 37, 0.93));
  padding: clamp(20px, 3vw, 30px);
  display: grid;
  gap: 12px;
}

.auth-topbar {
  display: flex;
  align-items: center;
  margin-bottom: 2px;
}

.back-arrow-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid rgba(89, 116, 165, 0.22);
  background: rgba(8, 17, 31, 0.22);
  color: rgba(177, 195, 224, 0.78);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  opacity: 0.86;
}

.back-arrow-btn:hover {
  border-color: rgba(126, 158, 214, 0.34);
  color: rgba(233, 241, 255, 0.94);
  opacity: 1;
}

label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  letter-spacing: 0.04em;
  color: var(--muted);
  text-transform: uppercase;
}

.error {
  color: var(--danger);
  font-size: 13px;
  line-height: 1.4;
  border: 1px solid rgba(173, 73, 99, 0.4);
  background: rgba(81, 27, 42, 0.45);
  border-radius: 12px;
  padding: 10px 12px;
}

.submit-btn {
  margin-top: 4px;
}

.register-hint {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 13px;
  justify-self: center;
}

.register-hint-link {
  margin-left: 4px;
  color: rgba(210, 224, 250, 0.95);
  font-weight: 600;
}

.register-hint-link:hover {
  color: #fff;
}

.remember-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: -2px;
  font-size: 13px;
  text-transform: none;
  letter-spacing: 0;
  color: var(--text-soft);
}

.remember-check {
  width: 16px;
  height: 16px;
  margin: 0;
  accent-color: #7ba8ff;
}
</style>
