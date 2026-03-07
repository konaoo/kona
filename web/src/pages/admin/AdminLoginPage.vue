<template>
  <div class="auth-wrap page-wrap">
    <div class="auth panel">
      <h1>管理后台登录</h1>
      <p class="tip">登录后将校验管理员权限。</p>

      <label>
        用户名
        <input v-model.trim="username" class="input" />
      </label>
      <label>
        密码
        <input v-model="password" type="password" class="input" />
      </label>

      <p class="error" v-if="error">{{ error }}</p>

      <button class="btn primary" :disabled="submitting" @click="submit">
        {{ submitting ? '验证中...' : '登录管理后台' }}
      </button>
      <RouterLink class="btn" to="/">返回主页</RouterLink>
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
const error = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    await store.login(username.value, password.value)
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
.auth-wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
}

.auth {
  width: min(520px, 100%);
  padding: 24px;
  display: grid;
  gap: 12px;
}

.tip {
  margin: 0;
  color: var(--muted);
}

label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}

.error {
  color: var(--danger);
}
</style>
