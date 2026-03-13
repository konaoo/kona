<template>
  <div class="outer" :data-theme="theme">
    <div class="card">
      <!-- LEFT: FORM PANEL -->
      <div class="form-panel">
        <RouterLink to="/" class="panel-logo">
          <div class="logo-icon">
            <svg width="16" height="12" viewBox="0 0 18 14" fill="none">
              <polyline points="1,13 5,5 9,9 13,3 17,7" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <div class="logo-name">咔咔记账</div>
            <div class="logo-tag">GLOBAL ASSET DESK</div>
          </div>
        </RouterLink>

        <div class="form-body">


          <!-- LOGIN FORM -->
          <div v-if="!isRegisterRoute" class="auth-form active">
            <div class="form-title">很高兴见到你。</div>
            <div class="input-group">
              <label class="input-label">账号</label>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
                <input v-model.trim="username" class="form-input" type="text" placeholder="请输入用户名" autocomplete="username"/>
              </div>
            </div>
            <div class="input-group">
              <label class="input-label">密码</label>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
                <input v-model="password" class="form-input has-pw" :type="showPassword ? 'text' : 'password'" placeholder="请输入密码" autocomplete="current-password"/>
                <button class="pw-toggle" @click="showPassword = !showPassword" type="button">
                  <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <div v-if="error && !isRegisterRoute" class="input-error visible">{{ error }}</div>
            </div>
            <div class="form-row">
              <label class="remember-wrap">
                <input v-model="rememberMe" class="remember-cb" type="checkbox"/>
                <span class="remember-label">记住账号</span>
              </label>
              <a href="#" class="forgot-link">忘记密码？</a>
            </div>
            <button class="submit-btn" :class="{ loading: submitting }" @click="submit" :disabled="submitting">
              {{ submitting ? '登录中…' : '登 录' }}
            </button>
            <div class="auth-switch">还没有账号？<button @click="switchTab('register')">立即注册</button></div>
            <div class="auth-legal">登录即代表同意 <a href="#">《用户服务协议》</a>与<a href="#">《隐私政策》</a></div>

          </div>

          <!-- REGISTER FORM -->
          <div v-else class="auth-form active">
            <div class="form-title">创建账户</div>
            <button class="back-to-login" type="button" @click="switchTab('login')">← 返回登录</button>
            <div class="input-group">
              <div class="invite-badge">
                <span class="i-dot"></span>
                目前仅限受邀用户注册，
                <div ref="inviteLinkWrapEl" class="invite-link-wrap" :class="{ open: invitePopoverOpen }">
                  <a href="#" class="invite-link" @click.prevent.stop="toggleInvitePopover">获取邀请码</a>
                  <div class="invite-popover" @click.stop>
                    <div class="pop-content">
                      <p v-if="inviteAcquireText">{{ inviteAcquireText }}</p>
                      <img v-if="inviteAcquireImageUrl" :src="inviteAcquireImageUrl" alt="邀请码获取方式" />
                    </div>
                  </div>
                </div>
	              </div>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></span>
                <input v-model.trim="inviteCode" class="form-input invite" type="text" placeholder="XXXXXXXXXX" maxlength="10" @input="inviteCode = inviteCode.toUpperCase()"/>
              </div>
            </div>
            <div class="input-group">
              <label class="input-label">用户名</label>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
                <input v-model.trim="username" class="form-input" type="text" placeholder="3-20位字符"/>
              </div>
            </div>
            <div class="input-group">
              <label class="input-label">密码</label>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
                <input v-model="password" class="form-input has-pw" :type="showPassword ? 'text' : 'password'" placeholder="至少8位，含字母和数字" @input="checkPasswordStrength(password)"/>
                <button class="pw-toggle" @click="showPassword = !showPassword" type="button">
                  <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <div class="pw-strength">
                <div :class="['pw-bar', { weak: passwordStrength >= 1, medium: passwordStrength >= 3, strong: passwordStrength >= 4 }]"></div>
                <div :class="['pw-bar', { weak: passwordStrength >= 2, medium: passwordStrength >= 3, strong: passwordStrength >= 4 }]"></div>
                <div :class="['pw-bar', { medium: passwordStrength >= 3, strong: passwordStrength >= 4 }]"></div>
                <div :class="['pw-bar', { strong: passwordStrength >= 4 }]"></div>
              </div>
              <div v-if="passwordHint" class="pw-hint" :style="{ color: passwordStrength < 3 ? 'var(--red)' : passwordStrength < 4 ? 'var(--gold)' : 'var(--green)' }">{{ passwordHint }}</div>
            </div>
            <div class="input-group" style="margin-bottom:18px">
              <label class="input-label">确认密码</label>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></span>
                <input v-model="confirmPassword" class="form-input has-pw" :type="showConfirmPassword ? 'text' : 'password'" placeholder="再次输入密码"/>
                <button class="pw-toggle" @click="showConfirmPassword = !showConfirmPassword" type="button">
                  <svg v-if="!showConfirmPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <div v-if="error && isRegisterRoute" class="input-error visible">{{ error }}</div>
            </div>
            <button class="submit-btn" :class="{ loading: submitting }" @click="submit" :disabled="submitting">
              {{ submitting ? '创建中…' : '创建账户' }}
            </button>
            <div class="auth-legal">注册即代表同意 <a href="#">《用户服务协议》</a>与<a href="#">《隐私政策》</a></div>
            <div class="auth-switch">已有账号？<button @click="switchTab('login')">立即登录</button></div>
          </div>
        </div>
      </div>

      <!-- RIGHT: BRAND PANEL -->
      <div class="brand-panel">
        <svg class="star-deco" viewBox="0 0 260 260" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="130" y1="0" x2="130" y2="260" stroke="#5b8def" stroke-width="1.2"/>
          <line x1="0" y1="130" x2="260" y2="130" stroke="#5b8def" stroke-width="1.2"/>
          <line x1="19" y1="19" x2="241" y2="241" stroke="#5b8def" stroke-width="1"/>
          <line x1="241" y1="19" x2="19" y2="241" stroke="#5b8def" stroke-width="1"/>
          <line x1="130" y1="0" x2="241" y2="241" stroke="#a78bfa" stroke-width="0.8"/>
          <line x1="130" y1="0" x2="19" y2="241" stroke="#a78bfa" stroke-width="0.8"/>
          <line x1="0" y1="130" x2="241" y2="19" stroke="#a78bfa" stroke-width="0.8"/>
          <line x1="260" y1="130" x2="19" y2="19" stroke="#a78bfa" stroke-width="0.8"/>
          <line x1="0" y1="130" x2="241" y2="241" stroke="#a78bfa" stroke-width="0.8"/>
          <line x1="260" y1="130" x2="19" y2="241" stroke="#a78bfa" stroke-width="0.8"/>
          <circle cx="130" cy="130" r="22" stroke="#5b8def" stroke-width="0.8" opacity="0.45"/>
          <circle cx="130" cy="130" r="50" stroke="#5b8def" stroke-width="0.5" opacity="0.28"/>
          <circle cx="130" cy="130" r="80" stroke="#5b8def" stroke-width="0.4" opacity="0.15"/>
        </svg>

        <div class="brand-top">
          <div class="brand-eyebrow">GLOBAL ASSET DESK</div>
          <h2 class="brand-title">全球资产<br><span class="brand-title-accent">一站式管理</span></h2>

        </div>

        <div class="quote-card" :class="{ 'fade-out': !quoteCardVisible }">
          <div class="quote-mark">"</div>
          <div class="quote-text">{{ currentQuote?.text }}</div>
          <div class="quote-author">
            <div class="qa-avatar">{{ currentQuote?.avatar }}</div>
            <div>
              <div class="qa-name">{{ currentQuote?.name }}</div>
              <div class="qa-role">{{ currentQuote?.role }}</div>
            </div>
          </div>

        </div>

        <div class="stats-strip">
          <div class="sc-item">
            <div class="sc-num">5<em>个</em></div>
            <div class="sc-label">支持市场</div>
          </div>
          <div class="sc-div"></div>
          <div class="sc-item">
            <div class="sc-num">100%</div>
            <div class="sc-label">实时同步</div>
          </div>
          <div class="sc-div"></div>
          <div class="sc-item">
            <div class="sc-num">∞</div>
            <div class="sc-label">资产上限</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useKonaStore } from '../../stores/composables'
import { api } from '../../shared/http'
import { useWebTheme } from '../../shared/webTheme'

const REMEMBER_ENABLED_KEY = 'kona_web_remember_enabled'
const REMEMBER_USERNAME_KEY = 'kona_web_remember_username'


const router = useRouter()
const route = useRoute()
const store = useKonaStore()
const { theme } = useWebTheme()

const submitting = ref(false)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const inviteCode = ref('')
const rememberMe = ref(false)
const error = ref('')

// Invitation config
	const inviteAcquireText = ref('')
	const inviteAcquireImageUrl = ref('')
	const invitePopoverOpen = ref(false)
	const inviteLinkWrapEl = ref<HTMLElement | null>(null)

// Password UI state
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const passwordStrength = ref(0)
const passwordHint = ref('')

// Quote Carousel
const quotes = [
  { text: '以前要在三四个 App 里反复切换才能看清楚持仓情况，咔咔记账把所有市场统一在一个页面，每天看一眼就够了。', name: '王同学', role: '港股 · 美股投资者', avatar: '王' },
  { text: '收益日历太实用了，一眼就能看到哪天赚了多少，季度表现一目了然，帮我改变了很多交易习惯。', name: 'Leo C.', role: 'A股 · 基金持有人', avatar: 'L' },
  { text: '多账户隔离功能非常好用，长期持仓和短线操作分开管理，各自核算盈亏，思路清晰多了。', name: '张小姐', role: '资深投资者', avatar: '张' },
]
const currentQuoteIndex = ref(0)
const quoteCardVisible = ref(true)
let quoteInterval: ReturnType<typeof setInterval>

const isRegisterRoute = computed(() => route.path === '/app/register')
const currentQuote = computed(() => quotes[currentQuoteIndex.value])

	function switchTab(type: 'login' | 'register') {
	  error.value = ''
	  invitePopoverOpen.value = false
	  router.push(type === 'login' ? '/app/login' : '/app/register')
	}

	function toggleInvitePopover() {
	  invitePopoverOpen.value = !invitePopoverOpen.value
	}

	function handleDocumentClick(e: MouseEvent) {
	  if (!invitePopoverOpen.value) return
	  const el = inviteLinkWrapEl.value
	  const target = e.target as Node | null
	  if (!el || !target) {
	    invitePopoverOpen.value = false
	    return
	  }
	  if (el.contains(target)) return
	  invitePopoverOpen.value = false
	}

function nextQuote() {
  quoteCardVisible.value = false
  setTimeout(() => {
    currentQuoteIndex.value = (currentQuoteIndex.value + 1) % quotes.length
    quoteCardVisible.value = true
  }, 200)
}



function checkPasswordStrength(v: string) {
  if (!v) {
    passwordStrength.value = 0
    passwordHint.value = ''
    return
  }
  let s = 0
  if (v.length >= 8) s++
  if (/[A-Z]/.test(v)) s++
  if (/[0-9]/.test(v)) s++
  if (/[^A-Za-z0-9]/.test(v)) s++
  
  passwordStrength.value = s
  const texts = ['弱', '弱', '中等', '强']
  passwordHint.value = `密码强度：${texts[Math.max(0, s - 1)]}`
}

function readRememberFields() {
  if (typeof window === 'undefined') return
  rememberMe.value = localStorage.getItem(REMEMBER_ENABLED_KEY) === '1'
  if (!rememberMe.value) return
  username.value = localStorage.getItem(REMEMBER_USERNAME_KEY) || ''
}

function persistRememberFields() {
  if (typeof window === 'undefined') return
  if (rememberMe.value) {
    localStorage.setItem(REMEMBER_ENABLED_KEY, '1')
    localStorage.setItem(REMEMBER_USERNAME_KEY, username.value)
    return
  }
  localStorage.setItem(REMEMBER_ENABLED_KEY, '0')
  localStorage.removeItem(REMEMBER_USERNAME_KEY)
}

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    if (isRegisterRoute.value) {
      if (username.value.length < 3) {
        error.value = '用户名至少 3 位'
        return
      }
      if (password.value.length < 8) {
        error.value = '密码至少 8 位'
        return
      }
      if (confirmPassword.value !== password.value) {
        error.value = '两次输入的密码不一致'
        return
      }
      if (!inviteCode.value.trim()) {
        error.value = '请填写邀请码'
        return
      }
      await store.register(username.value, password.value, inviteCode.value)
    } else {
      if (!username.value.trim() || !password.value.trim()) {
        error.value = '请输入用户名和密码'
        return
      }
      await store.login(username.value, password.value)
      persistRememberFields()
    }
    await router.push('/app/home')
  } catch (e: any) {
    error.value = e.message || '操作失败，请重试'
  } finally {
    submitting.value = false
  }
}

async function fetchWebConfig() {
  try {
    const payload = await api.get<{ invite_acquire_text?: string, invite_acquire_image_url?: string }>('/api/web/config', false)
    if (payload.invite_acquire_text) inviteAcquireText.value = payload.invite_acquire_text
    if (payload.invite_acquire_image_url) inviteAcquireImageUrl.value = payload.invite_acquire_image_url
  } catch {
    // fallback
  }
}

	onMounted(() => {
	  if (!isRegisterRoute.value) {
	    readRememberFields()
	  }
	  fetchWebConfig()
	  quoteInterval = setInterval(nextQuote, 5200)
	  document.addEventListener('click', handleDocumentClick, true)
	})

	onUnmounted(() => {
	  if (quoteInterval) clearInterval(quoteInterval)
	  document.removeEventListener('click', handleDocumentClick, true)
	})

</script>

<style scoped>
.outer {
  --auth-shell-bg:
    radial-gradient(ellipse 80% 60% at 15% -5%, rgba(91, 141, 239, 0.16) 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 90% 105%, rgba(240, 39, 158, 0.13) 0%, transparent 55%),
    #0d0f15;
  --auth-grid: linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  --auth-card-bg: #12141c;
  --auth-card-shadow: 0 40px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06);
  --auth-form-bg: rgba(16,18,26,0.97);
  --auth-form-glow: radial-gradient(circle, rgba(91,141,239,0.07) 0%, transparent 65%);
  --auth-form-title: #e4e5ea;
  --auth-text-main: #e4e5ea;
  --auth-text-sub: #828a9e;
  --auth-text-muted: #545c72;
  --auth-input-bg: rgba(255,255,255,0.05);
  --auth-input-border: rgba(255,255,255,0.07);
  --auth-input-focus-bg: rgba(91,141,239,0.05);
  --auth-input-focus-shadow: 0 0 0 3px rgba(91,141,239,0.11);
  --auth-brand-bg: linear-gradient(155deg, #0e1119 0%, #0b0d16 45%, #0d1020 100%);
  --auth-brand-border: rgba(255,255,255,0.055);
  --auth-brand-card: rgba(255,255,255,0.04);
  --auth-brand-card-border: rgba(255,255,255,0.09);
  --auth-invite-bg: rgba(212,175,100,0.08);
  --auth-invite-border: rgba(212,175,100,0.18);
  --auth-pop-bg: rgba(18,20,28,0.95);
  --auth-pop-border: rgba(255,255,255,0.08);
  --auth-pop-shadow: 0 10px 30px rgba(0,0,0,0.4);
  --auth-remember-border: rgba(255,255,255,0.13);
  min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px;
  background: var(--auth-shell-bg);
  position: relative;
  overflow: hidden;
}

.outer[data-theme='light'] {
  --auth-shell-bg:
    radial-gradient(ellipse 72% 56% at 14% -8%, rgba(91, 141, 239, 0.18) 0%, transparent 56%),
    radial-gradient(ellipse 48% 44% at 93% 105%, rgba(240, 39, 158, 0.1) 0%, transparent 58%),
    linear-gradient(145deg, #f7fbff 0%, #eef5ff 48%, #f9f6ff 100%);
  --auth-grid: linear-gradient(rgba(15,23,42,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,0.04) 1px, transparent 1px);
  --auth-card-bg: rgba(255,255,255,0.88);
  --auth-card-shadow: 0 34px 86px rgba(15,23,42,0.12), 0 0 0 1px rgba(255,255,255,0.7);
  --auth-form-bg: rgba(255,255,255,0.84);
  --auth-form-glow: radial-gradient(circle, rgba(91,141,239,0.12) 0%, transparent 68%);
  --auth-form-title: #0f172a;
  --auth-text-main: #10243e;
  --auth-text-sub: #516174;
  --auth-text-muted: #748396;
  --auth-input-bg: rgba(255,255,255,0.9);
  --auth-input-border: rgba(15,23,42,0.08);
  --auth-input-focus-bg: rgba(91,141,239,0.07);
  --auth-input-focus-shadow: 0 0 0 3px rgba(91,141,239,0.13);
  --auth-brand-bg:
    linear-gradient(155deg, rgba(255,255,255,0.52), rgba(239,245,255,0.88)),
    linear-gradient(155deg, #edf4ff 0%, #eef3ff 42%, #f7f9ff 100%);
  --auth-brand-border: rgba(15,23,42,0.08);
  --auth-brand-card: rgba(255,255,255,0.74);
  --auth-brand-card-border: rgba(15,23,42,0.08);
  --auth-invite-bg: rgba(212,175,100,0.1);
  --auth-invite-border: rgba(212,175,100,0.24);
  --auth-pop-bg: rgba(255,255,255,0.97);
  --auth-pop-border: rgba(15,23,42,0.08);
  --auth-pop-shadow: 0 20px 46px rgba(15,23,42,0.12);
  --auth-remember-border: rgba(15,23,42,0.16);
}

.outer::before {
  content: ''; position: absolute; inset: 0;
  background-image: var(--auth-grid);
  background-size: 52px 52px; pointer-events: none; z-index: 0;
}

.card {
  position: relative; z-index: 1; width: 100%; max-width: 940px; min-height: 580px;
  border-radius: 26px; display: grid; grid-template-columns: 1fr 1fr;
  overflow: hidden;
  background: var(--auth-card-bg);
  box-shadow: var(--auth-card-shadow);
  animation: cardIn .55s cubic-bezier(.25,1,.5,1) both;
  backdrop-filter: blur(18px);
}
@keyframes cardIn { from { opacity:0; transform:translateY(22px) scale(.985); } to { opacity:1; transform:none; } }

/* ── LEFT: FORM PANEL ── */
.form-panel {
  background: var(--auth-form-bg);
  padding: 40px 48px; display: flex; flex-direction: column; position: relative; overflow: hidden;
}
.form-panel::before {
  content: ''; position: absolute; top: -130px; left: -130px;
  width: 380px; height: 380px;
  background: var(--auth-form-glow);
  pointer-events: none;
}

.panel-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; margin-bottom: 20px; position: relative; z-index: 1; }
.logo-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #ff7b67, #f24688 55%, #f0279e);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 16px rgba(240,39,158,0.26); flex-shrink: 0;
}
.logo-name { font-size: 15px; font-weight: 700; color: var(--auth-text-main); line-height: 1.1; }
.logo-tag  { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: .12em; color: var(--auth-text-muted); }

.form-body { flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; z-index: 1; max-width: 370px; }

.auth-tabs {
  display: flex; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 11px; padding: 4px; gap: 4px; margin-bottom: 30px; width: fit-content;
}
.auth-tab {
  border: none; background: transparent; color: var(--auth-text-muted);
  font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600;
  padding: 8px 22px; border-radius: 8px; cursor: pointer; transition: all .17s;
}
.auth-tab.active { background: var(--surface-strong); color: var(--auth-text-main); box-shadow: 0 2px 8px rgba(15,23,42,0.12); }

.auth-form { display: flex; flex-direction: column; }

.form-title { font-size: 25px; font-weight: 800; letter-spacing: -.025em; color: var(--auth-form-title); margin-bottom: 28px; }
.back-to-login {
  width: fit-content;
  margin: -18px 0 18px;
  padding: 0;
  border: none;
  background: none;
  color: var(--auth-text-muted);
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: color .15s, opacity .15s;
}
.back-to-login:hover {
  color: var(--auth-text-sub);
  opacity: 0.92;
}
.form-sub { font-size: 13px; color: var(--auth-text-muted); margin-bottom: 26px; line-height: 1.5; }

.input-group { display: flex; flex-direction: column; gap: 5px; margin-bottom: 13px; }
.input-label { font-size: 12px; font-weight: 600; color: var(--auth-text-sub); letter-spacing: .02em; }
.input-wrap { position: relative; }
.input-icon {
  position: absolute; left: 13px; top: 50%; transform: translateY(-50%);
  color: var(--auth-text-muted); pointer-events: none; display: flex; align-items: center; transition: color .15s;
}
.input-icon svg { width: 15px; height: 15px; }
.form-input {
  width: 100%; height: 46px;
  background: var(--auth-input-bg); border: 1px solid var(--auth-input-border); border-radius: 11px;
  padding: 0 14px 0 40px; font-family: 'DM Sans', sans-serif; font-size: 14px; color: var(--auth-text-main);
  outline: none; transition: border-color .15s, background .15s, box-shadow .15s; -webkit-appearance: none;
}
.form-input::placeholder { color: var(--auth-text-muted); }
.form-input:focus { border-color: rgba(91,141,239,0.48); background: var(--auth-input-focus-bg); box-shadow: var(--auth-input-focus-shadow); }
.input-wrap:focus-within .input-icon { color: #5b8def; }
.pw-toggle {
  position: absolute; right: 11px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: var(--auth-text-muted);
  padding: 4px; display: flex; align-items: center; transition: color .13s;
}
.pw-toggle:hover { color: var(--auth-text-sub); }
.pw-toggle svg { width: 15px; height: 15px; }
.form-input.has-pw { padding-right: 40px; }

.pw-strength { display: flex; gap: 4px; margin-top: 5px; }
.pw-bar { flex: 1; height: 3px; border-radius: 2px; background: rgba(255,255,255,0.07); transition: background .28s; }
.pw-bar.weak { background: #f05a55; }
.pw-bar.medium { background: #d4af64; }
.pw-bar.strong { background: #3ecf82; }
.pw-hint { font-size: 11px; color: var(--auth-text-muted); margin-top: 4px; }

.invite-badge {
  display: flex; align-items: center; gap: 8px;
  background: var(--auth-invite-bg); border: 1px solid var(--auth-invite-border);
  padding: 8px 14px; border-radius: 10px; color: var(--gold); font-size: 13px; font-weight: 500;
  margin-bottom: 12px;
}
.i-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--gold); box-shadow: 0 0 8px var(--gold); }

	.invite-link-wrap { position: relative; display: inline-block; }
	.invite-link { color: var(--auth-text-main); text-decoration: none; border-bottom: 1px dashed color-mix(in srgb, var(--auth-text-main) 35%, transparent); cursor: pointer; transition: 0.2s; }
	.invite-link:hover { color: var(--gold); opacity: 0.9; }

.invite-popover {
  position: absolute; top: calc(100% + 12px); left: 50%; transform: translateX(-50%) translateY(-10px);
  width: 240px; background: var(--auth-pop-bg); backdrop-filter: blur(12px);
  border: 1px solid var(--auth-pop-border); border-radius: 14px; padding: 16px;
  box-shadow: var(--auth-pop-shadow);
  visibility: hidden; opacity: 0; transition: 0.25s cubic-bezier(0.19, 1, 0.22, 1);
  pointer-events: none; z-index: 100;
}
.invite-popover::after {
  content: ''; position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%);
  border: 6px solid transparent; border-bottom-color: var(--auth-pop-bg);
}
	.invite-link-wrap:hover .invite-popover {
	  visibility: visible; opacity: 1; transform: translateX(-50%) translateY(0); pointer-events: auto;
	}
	.invite-link-wrap.open .invite-popover {
	  visibility: visible; opacity: 1; transform: translateX(-50%) translateY(0); pointer-events: auto;
	}
	.pop-content { display: flex; flex-direction: column; gap: 10px; text-align: center; }
	.pop-content p { color: var(--auth-text-main); font-size: 13px; line-height: 1.5; margin: 0; }
	.pop-content img { width: 100%; height: auto; object-fit: contain; border-radius: 8px; border: 1px solid var(--auth-input-border); }
	.form-input.invite { text-transform: uppercase; letter-spacing: .1em; font-family: 'JetBrains Mono', monospace; font-size: 13px; }

	/* 修复移动端浏览器自动填充导致的“输入框发白/文字看不清” */
	.form-input:-webkit-autofill,
	.form-input:-webkit-autofill:hover,
	.form-input:-webkit-autofill:focus,
	.form-input:-webkit-autofill:active {
	  -webkit-text-fill-color: var(--auth-text-main);
	  caret-color: var(--auth-text-main);
	  box-shadow: 0 0 0 1000px var(--auth-input-bg) inset;
	  border: 1px solid var(--auth-input-border);
	  transition: background-color 9999s ease-in-out 0s;
	}

.form-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; margin-top: 4px; }
.remember-wrap { display: flex; align-items: center; gap: 7px; cursor: pointer; }
.remember-cb {
  width: 16px; height: 16px; border-radius: 4px; border: 1.5px solid var(--auth-remember-border);
  background: transparent; appearance: none; cursor: pointer; position: relative;
  transition: background .14s, border-color .14s; flex-shrink: 0;
}
.remember-cb:checked { background: #5b8def; border-color: #5b8def; }
.remember-cb:checked::after { content: ''; position: absolute; top: 2px; left: 5px; width: 4px; height: 7px; border: 1.5px solid #fff; border-top: none; border-left: none; transform: rotate(40deg); }
.remember-label { font-size: 12px; color: var(--auth-text-muted); cursor: pointer; }
.forgot-link { font-size: 12px; color: var(--auth-text-muted); text-decoration: none; transition: color .13s; }
.forgot-link:hover { color: #5b8def; }

.submit-btn {
  width: 100%; height: 48px; border-radius: 13px; border: none;
  background: linear-gradient(135deg, #5b8def, #4a7be0);
  color: #fff; font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 700;
  cursor: pointer; position: relative; overflow: hidden; margin-bottom: 16px;
  box-shadow: 0 6px 20px rgba(74,123,224,0.28), inset 0 1px 0 rgba(255,255,255,0.18);
  transition: transform .18s, box-shadow .18s;
  display: flex; align-items: center; justify-content: center;
}
.submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(74,123,224,0.38), inset 0 1px 0 rgba(255,255,255,0.18); }
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.submit-btn::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent); transform: translateX(-100%); }
.submit-btn.loading::after { animation: shimmer 1.2s ease-in-out infinite; }
@keyframes shimmer { to { transform: translateX(100%); } }

.input-error { font-size: 11px; color: #f05a55; margin-top: 3px; display: none; }
.input-error.visible { display: block; }

.auth-legal { font-size: 11px; color: var(--auth-text-muted); line-height: 1.55; text-align: center; margin-top: 24px; }
.auth-legal a { color: var(--auth-text-muted); text-decoration: underline; transition: color .13s; }
.auth-legal a:hover { color: var(--auth-text-sub); }
.auth-switch { text-align: center; font-size: 13px; color: var(--auth-text-muted); margin-top: 11px; }
.auth-switch button { background: none; border: none; color: #5b8def; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; padding: 0; transition: opacity .13s; }
.auth-switch button:hover { opacity: .75; }

/* ── RIGHT: BRAND PANEL ── */
.brand-panel {
  position: relative; overflow: hidden;
  background: var(--auth-brand-bg);
  border-left: 1px solid var(--auth-brand-border);
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 40px 40px 40px 44px;
}
.brand-panel::before {
  content: ''; position: absolute; top: -90px; right: -90px;
  width: 360px; height: 360px;
  background: radial-gradient(circle, rgba(91,141,239,0.17) 0%, transparent 65%);
  filter: blur(44px); pointer-events: none;
}
.brand-panel::after {
  content: ''; position: absolute; bottom: -70px; left: -70px;
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(240,39,158,0.09) 0%, transparent 65%);
  filter: blur(44px); pointer-events: none;
}

.star-deco {
  position: absolute; right: -30px; top: 50%; transform: translateY(-55%);
  width: 260px; height: 260px; opacity: 0.15; pointer-events: none;
}

.brand-top { position: relative; z-index: 1; }
.brand-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500; letter-spacing: .14em; color: #5b8def; margin-bottom: 14px; }
.brand-title { font-size: clamp(26px, 2.6vw, 38px); font-weight: 800; line-height: 1.1; letter-spacing: -.03em; margin-bottom: 14px; color: var(--auth-text-main); }
.brand-title-accent { background: linear-gradient(135deg, #5b8def, #a78bfa 50%, #f05a55); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.brand-desc { font-size: 13px; color: var(--auth-text-sub); line-height: 1.7; max-width: 310px; }

.quote-card {
  position: relative; z-index: 1;
  background: var(--auth-brand-card);
  border: 1px solid var(--auth-brand-card-border);
  border-radius: 18px; padding: 22px 24px;
  transition: opacity .28s, transform .28s;
  box-shadow: 0 16px 38px rgba(15,23,42,0.08);
}
.quote-card.fade-out { opacity: 0; transform: translateY(8px); }
.quote-mark { font-size: 32px; line-height: 1; color: #5b8def; font-family: Georgia, serif; margin-bottom: 7px; opacity: .65; }
.quote-text { font-size: 13px; color: var(--auth-text-sub); line-height: 1.75; margin-bottom: 16px; }
.quote-author { display: flex; align-items: center; gap: 10px; }
.qa-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #5b8def, #4a7be0); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0; }
.qa-name { font-size: 13px; font-weight: 700; color: var(--auth-text-main); }
.qa-role { font-size: 11px; color: var(--auth-text-muted); }

.quote-controls { display: flex; gap: 8px; margin-top: 16px; }
.qc-btn {
  width: 34px; height: 34px; border-radius: 9px; border: 1px solid var(--auth-input-border);
  background: var(--surface-soft); display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: var(--auth-text-sub); transition: all .15s;
}
.qc-btn:hover { background: var(--surface-soft-hover); color: var(--auth-text-main); border-color: var(--auth-brand-card-border); }
.qc-btn.next-btn { background: #5b8def; border-color: #5b8def; color: #fff; box-shadow: 0 4px 12px rgba(91,141,239,0.32); }
.qc-btn svg { width: 13px; height: 13px; }

.stats-strip {
  position: relative; z-index: 1;
  background: var(--auth-brand-card); border: 1px solid var(--auth-brand-card-border);
  border-radius: 15px; padding: 15px 20px;
  display: grid; grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: center; gap: 12px;
}
.sc-item { text-align: center; }
.sc-num { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 600; color: var(--auth-text-main); line-height: 1; margin-bottom: 2px; }
.sc-num em { color: #5b8def; font-style: normal; font-size: 11px; }
.sc-label { font-size: 10px; color: var(--auth-text-muted); }
.sc-div { width: 1px; height: 32px; background: var(--surface-divider); }

	@media (max-width: 780px) {
  .outer {
    padding: 0; /* Remove padding so it fills screen */
    align-items: flex-start; /* Align to top instead of center */
    background: var(--auth-form-bg); /* Use solid or form bg on mobile */
  }
  .card { 
    grid-template-columns: 1fr; 
    min-height: 100vh; /* Full viewport height */
    border-radius: 0; /* No rounded corners */
    box-shadow: none; /* No shadow */
    background: transparent;
    backdrop-filter: none;
    transform: none; /* Remove desktop animation transform */
    animation: none; /* Simple fade in mobile */
  }
  .brand-panel { display: none; }
	  .form-panel { 
	    padding: 60px 32px 32px; /* More top padding for status bar feel */
	    background: transparent;
	    min-height: 100vh;
	    justify-content: flex-start;
	    overflow: visible;
	  }
  .form-body {
    margin-top: 40px; /* Push form down a bit */
  }
  .form-title {
    font-size: 28px; /* Slightly larger title for impact */
    margin-bottom: 32px;
  }
  .input-wrap {
    height: 52px; /* Slightly taller inputs for touch */
  }
  .form-input {
    font-size: 16px; /* Better readability */
  }
  .auth-btn {
    height: 50px;
    font-size: 16px;
    border-radius: 14px;
    margin-top: 16px;
  }
  /* Optional: reposition logo on mobile to be centered or larger */
	  .panel-logo {
	    justify-content: center;
	    margin-bottom: 10px;
	  }

	  /* 移动端：把“获取邀请码”弹层变成居中弹窗，避免被容器 overflow 裁切 */
	  .invite-popover {
	    position: fixed;
	    left: 50%;
	    top: 50%;
	    width: min(92vw, 360px);
	    max-height: min(78vh, 560px);
	    overflow: auto;
	    transform: translate(-50%, -50%);
	  }
	  .invite-link-wrap:hover .invite-popover,
	  .invite-link-wrap.open .invite-popover {
	    transform: translate(-50%, -50%);
	  }
	  .pop-content img {
	    width: auto;
	    max-width: 100%;
	    max-height: 56vh;
	  }
	  .invite-popover::after { display: none; }
	}
</style>
