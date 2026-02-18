<template>
  <AppShell title="我的" subtitle="账号信息与个人资料">
    <section class="panel section">
      <h3 class="section-title">当前账号</h3>
      <div class="identity-grid">
        <article class="identity-item">
          <span class="k">用户名</span>
          <strong>{{ user?.username || '-' }}</strong>
        </article>
        <article class="identity-item">
          <span class="k">昵称</span>
          <strong>{{ user?.nickname || '-' }}</strong>
        </article>
        <article class="identity-item">
          <span class="k">用户ID</span>
          <strong class="mono">{{ user?.id || '-' }}</strong>
        </article>
      </div>
    </section>

    <section class="panel section">
      <h3 class="section-title">更新资料</h3>
      <div class="grid profile-grid">
        <label>
          昵称
          <input class="input" v-model.trim="nickname" />
        </label>
        <label>
          手机
          <input class="input" v-model.trim="phone" />
        </label>
      </div>
      <label class="avatar-field">
        头像(base64 可选)
        <textarea class="input" rows="4" v-model="avatar"></textarea>
      </label>
      <div class="actions">
        <button class="btn primary" @click="save">保存</button>
        <button class="btn danger" @click="logout">退出登录</button>
      </div>
      <p v-if="message" class="feedback" :class="ok ? 'value-up' : 'value-down'">{{ message }}</p>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'
import { useKonaStore } from '../../shared/store'

const router = useRouter()
const store = useKonaStore()
const user = computed(() => store.state.user)

const nickname = ref(String(user.value?.nickname || ''))
const phone = ref(String((user.value as any)?.phone || ''))
const avatar = ref(String((user.value as any)?.avatar || ''))
const message = ref('')
const ok = ref(true)

async function save() {
  try {
    const payload = await api.post<{ user?: Record<string, unknown> }>('/api/auth/profile', {
      nickname: nickname.value,
      phone: phone.value,
      avatar: avatar.value,
    })
    if (payload.user) {
      store.state.user = payload.user as any
    }
    message.value = '保存成功'
    ok.value = true
  } catch (e) {
    message.value = e instanceof Error ? e.message : '保存失败'
    ok.value = false
  }
}

async function logout() {
  await store.logout()
  await router.push('/app/login')
}
</script>

<style scoped>
.section {
  padding: 16px;
  margin-bottom: 14px;
}

.identity-grid {
  margin-top: 10px;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.identity-item {
  border: 1px solid rgba(96, 132, 187, 0.28);
  border-radius: 12px;
  background: rgba(13, 25, 44, 0.62);
  padding: 12px;
  display: grid;
  gap: 4px;
}

.k {
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.04em;
}

.identity-item strong {
  font-size: 15px;
  letter-spacing: 0.01em;
}

.mono {
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
}

.profile-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 12px;
}

label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}

.actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.avatar-field {
  display: block;
  margin-top: 10px;
}

.feedback {
  margin-top: 10px;
  width: fit-content;
  border-radius: 10px;
  border: 1px solid rgba(83, 117, 170, 0.34);
  background: rgba(11, 20, 37, 0.5);
  padding: 8px 12px;
}

@media (max-width: 900px) {
  .identity-grid {
    grid-template-columns: 1fr;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .section {
    padding: 14px;
  }
}
</style>
