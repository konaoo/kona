<template>
  <div class="auth-wrap page-wrap">
    <div class="auth panel">
      <h1>业务端登录</h1>
      <p class="tip">使用你的账号密码登录，或使用邀请码注册新账号。</p>

      <div class="toggle">
        <button class="btn" :class="{ primary: !isRegister }" @click="isRegister = false">登录</button>
        <button class="btn" :class="{ primary: isRegister }" @click="isRegister = true">注册</button>
      </div>

      <label>
        用户名
        <input v-model.trim="username" class="input" placeholder="小写字母开头，4-24位" />
      </label>

      <label>
        密码
        <input v-model="password" class="input" type="password" placeholder="8-64位，包含字母和数字" />
      </label>

      <label v-if="isRegister">
        邀请码
        <input v-model.trim="inviteCode" class="input" placeholder="输入邀请码" />
      </label>

      <div class="error" v-if="error">{{ error }}</div>

      <button class="btn primary" :disabled="submitting" @click="submit">
        {{ submitting ? '提交中...' : (isRegister ? '注册并登录' : '登录') }}
      </button>

      <RouterLink class="btn" to="/">返回主页</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useKonaStore } from '../../shared/store'

const router = useRouter()
const store = useKonaStore()

const isRegister = ref(false)
const submitting = ref(false)
const username = ref('')
const password = ref('')
const inviteCode = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    if (isRegister.value) {
      await store.register(username.value, password.value, inviteCode.value)
    } else {
      await store.login(username.value, password.value)
    }
    await store.refreshAll()
    await router.push('/app/home')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '请求失败'
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

h1 {
  margin: 0;
}

.tip {
  margin: 0;
  color: var(--muted);
}

.toggle {
  display: flex;
  gap: 8px;
}

label {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
}

.error {
  color: var(--danger);
  font-size: 13px;
}
</style>
