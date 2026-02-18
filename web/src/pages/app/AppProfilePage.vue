<template>
  <AppShell title="我的" subtitle="账号信息与个人资料">
    <section class="panel" style="padding: 16px; margin-bottom: 16px">
      <h3>当前账号</h3>
      <p>用户名：{{ user?.username || '-' }}</p>
      <p>昵称：{{ user?.nickname || '-' }}</p>
      <p>用户ID：{{ user?.id || '-' }}</p>
    </section>

    <section class="panel" style="padding: 16px">
      <h3>更新资料</h3>
      <div class="grid" style="grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 12px;">
        <label>
          昵称
          <input class="input" v-model.trim="nickname" />
        </label>
        <label>
          手机
          <input class="input" v-model.trim="phone" />
        </label>
      </div>
      <label style="display:block; margin-top: 10px;">
        头像(base64 可选)
        <textarea class="input" rows="4" v-model="avatar"></textarea>
      </label>
      <div style="margin-top: 10px; display: flex; gap: 8px;">
        <button class="btn primary" @click="save">保存</button>
        <button class="btn danger" @click="logout">退出登录</button>
      </div>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
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
label {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
