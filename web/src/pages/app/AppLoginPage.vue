<template>
  <div class="auth-wrap page-wrap">
    <div class="auth-shell panel">
      <aside class="auth-info">
        <p class="kicker">GLOBAL ASSET CONSOLE</p>
        <h1>欢迎回到咔咔记账</h1>
        <p class="tip">一处登录，联动网页端投资、分析与资产管理工作台。</p>
        <ul class="points">
          <li>实时行情与收益口径同步</li>
          <li>休市逻辑统一覆盖 A/HK/US/Fund</li>
          <li>投资与分析数据同源展示</li>
        </ul>
      </aside>

      <section class="auth">
        <div class="toggle" role="tablist" aria-label="登录注册切换">
          <button class="btn" :class="{ primary: !isRegister }" type="button" @click="isRegister = false">登录</button>
          <button class="btn" :class="{ primary: isRegister }" type="button" @click="isRegister = true">注册</button>
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

        <button class="btn primary submit-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中...' : (isRegister ? '注册并登录' : '登录') }}
        </button>

        <RouterLink class="back-link" to="/">返回主页</RouterLink>
      </section>
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
  max-width: 1120px;
}

.auth-shell {
  width: min(980px, 100%);
  padding: 18px;
  display: grid;
  gap: 18px;
  grid-template-columns: 1fr 1fr;
}

.auth-info {
  border-radius: 14px;
  border: 1px solid rgba(96, 129, 181, 0.24);
  background:
    radial-gradient(460px 240px at 100% -16%, rgba(124, 162, 244, 0.3), rgba(124, 162, 244, 0)),
    linear-gradient(150deg, rgba(23, 41, 71, 0.96), rgba(11, 22, 41, 0.9));
  padding: clamp(20px, 3vw, 34px);
}

.kicker {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--muted);
}

h1 {
  margin: 14px 0 0;
  line-height: 1.1;
  font-size: clamp(28px, 3.6vw, 42px);
  letter-spacing: -0.02em;
}

.tip {
  margin: 16px 0 0;
  color: var(--text-soft);
  line-height: 1.6;
  max-width: 28ch;
}

.points {
  margin: 22px 0 0;
  padding-left: 18px;
  color: var(--text-soft);
  display: grid;
  gap: 9px;
  font-size: 14px;
}

.auth {
  border-radius: 14px;
  border: 1px solid rgba(98, 130, 182, 0.24);
  background: linear-gradient(150deg, rgba(16, 27, 47, 0.93), rgba(11, 20, 37, 0.93));
  padding: clamp(20px, 3vw, 30px);
  display: grid;
  gap: 12px;
}

.toggle {
  display: flex;
  gap: 8px;
  padding: 4px;
  border-radius: 999px;
  border: 1px solid rgba(89, 116, 165, 0.32);
  background: rgba(8, 17, 31, 0.5);
}

.toggle .btn {
  flex: 1;
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

.back-link {
  color: var(--muted);
  font-size: 13px;
  justify-self: center;
}

.back-link:hover {
  color: var(--text-soft);
}

@media (max-width: 900px) {
  .auth-wrap {
    padding: 12px;
  }

  .auth-shell {
    grid-template-columns: 1fr;
  }

  .tip {
    max-width: 100%;
  }
}
</style>
