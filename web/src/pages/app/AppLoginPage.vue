<template>
  <div class="outer">
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
          <div class="auth-tabs">
            <button :class="['auth-tab', { active: !isRegisterRoute }]" @click="switchTab('login')">登录</button>
            <button :class="['auth-tab', { active: isRegisterRoute }]" @click="switchTab('register')">注册</button>
          </div>

          <!-- LOGIN FORM -->
          <div v-if="!isRegisterRoute" class="auth-form active">
            <div class="form-title">欢迎回来</div>
            <div class="form-sub">登录账户，继续管理你的全球资产。</div>
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
            <div class="auth-legal">登录即代表同意 <a href="#">《用户服务协议》</a>与<a href="#">《隐私政策》</a></div>
            <div class="auth-switch">还没有账号？<button @click="switchTab('register')">立即注册</button></div>
          </div>

          <!-- REGISTER FORM -->
          <div v-else class="auth-form active">
            <div class="form-title">创建账户</div>
            <div class="form-sub">内测期间需要邀请码，<a href="#" style="color:var(--gold);text-decoration:none">如何获取？</a></div>
            <div class="input-group">
              <div class="invite-badge"><span class="i-dot"></span>仅限内测用户</div>
              <div class="input-wrap">
                <span class="input-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></span>
                <input v-model.trim="inviteCode" class="form-input invite" type="text" placeholder="XXXXXX" maxlength="8" @input="inviteCode = inviteCode.toUpperCase()"/>
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
          <p class="brand-desc">港股、美股、A股、基金，跨市场统一追踪。实时盈亏、多账户隔离，尽在掌控。</p>
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
          <div class="quote-controls">
            <button class="qc-btn" @click="prevQuote" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            <button class="qc-btn next-btn" @click="nextQuote" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
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
import { useKonaStore } from '../../shared/store'

const REMEMBER_ENABLED_KEY = 'kona_web_remember_enabled'
const REMEMBER_USERNAME_KEY = 'kona_web_remember_username'


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
  router.push(type === 'login' ? '/app/login' : '/app/register')
}

function nextQuote() {
  quoteCardVisible.value = false
  setTimeout(() => {
    currentQuoteIndex.value = (currentQuoteIndex.value + 1) % quotes.length
    quoteCardVisible.value = true
  }, 200)
}

function prevQuote() {
  quoteCardVisible.value = false
  setTimeout(() => {
    currentQuoteIndex.value = (currentQuoteIndex.value - 1 + quotes.length) % quotes.length
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

onMounted(() => {
  if (!isRegisterRoute.value) {
    readRememberFields()
  }
  quoteInterval = setInterval(nextQuote, 5200)
})

onUnmounted(() => {
  if (quoteInterval) clearInterval(quoteInterval)
})

</script>

<style scoped>
.outer {
  min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px;
  background:
    radial-gradient(ellipse 80% 60% at 15% -5%, rgba(91,141,239,0.16) 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 90% 105%, rgba(240,39,158,0.13) 0%, transparent 55%),
    #0d0f15;
  position: relative;
  overflow: hidden;
}
.outer::before {
  content: ''; position: absolute; inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 52px 52px; pointer-events: none; z-index: 0;
}

.card {
  position: relative; z-index: 1; width: 100%; max-width: 1080px; min-height: 660px;
  border-radius: 26px; display: grid; grid-template-columns: 1fr 1fr;
  overflow: hidden;
  background: #12141c;
  box-shadow: 0 40px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06);
  animation: cardIn .55s cubic-bezier(.25,1,.5,1) both;
}
@keyframes cardIn { from { opacity:0; transform:translateY(22px) scale(.985); } to { opacity:1; transform:none; } }

/* ── LEFT: FORM PANEL ── */
.form-panel {
  background: rgba(16,18,26,0.97);
  padding: 44px 52px; display: flex; flex-direction: column; position: relative; overflow: hidden;
}
.form-panel::before {
  content: ''; position: absolute; top: -130px; left: -130px;
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(91,141,239,0.07) 0%, transparent 65%);
  pointer-events: none;
}

.panel-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; margin-bottom: 48px; position: relative; z-index: 1; }
.logo-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #ff7b67, #f24688 55%, #f0279e);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 16px rgba(240,39,158,0.26); flex-shrink: 0;
}
.logo-name { font-size: 15px; font-weight: 700; color: #e4e5ea; line-height: 1.1; }
.logo-tag  { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: .12em; color: #545c72; }

.form-body { flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; z-index: 1; max-width: 370px; }

.auth-tabs {
  display: flex; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 11px; padding: 4px; gap: 4px; margin-bottom: 30px; width: fit-content;
}
.auth-tab {
  border: none; background: transparent; color: #545c72;
  font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600;
  padding: 8px 22px; border-radius: 8px; cursor: pointer; transition: all .17s;
}
.auth-tab.active { background: rgba(255,255,255,0.09); color: #e4e5ea; box-shadow: 0 2px 8px rgba(0,0,0,0.28); }

.auth-form { display: flex; flex-direction: column; }

.form-title { font-size: 25px; font-weight: 800; letter-spacing: -.025em; color: #e4e5ea; margin-bottom: 5px; }
.form-sub { font-size: 13px; color: #545c72; margin-bottom: 26px; line-height: 1.5; }

.input-group { display: flex; flex-direction: column; gap: 5px; margin-bottom: 13px; }
.input-label { font-size: 12px; font-weight: 600; color: #828a9e; letter-spacing: .02em; }
.input-wrap { position: relative; }
.input-icon {
  position: absolute; left: 13px; top: 50%; transform: translateY(-50%);
  color: #545c72; pointer-events: none; display: flex; align-items: center; transition: color .15s;
}
.input-icon svg { width: 15px; height: 15px; }
.form-input {
  width: 100%; height: 46px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.07); border-radius: 11px;
  padding: 0 14px 0 40px; font-family: 'DM Sans', sans-serif; font-size: 14px; color: #e4e5ea;
  outline: none; transition: border-color .15s, background .15s, box-shadow .15s; -webkit-appearance: none;
}
.form-input::placeholder { color: #545c72; }
.form-input:focus { border-color: rgba(91,141,239,0.48); background: rgba(91,141,239,0.05); box-shadow: 0 0 0 3px rgba(91,141,239,0.11); }
.input-wrap:focus-within .input-icon { color: #5b8def; }
.pw-toggle {
  position: absolute; right: 11px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: #545c72;
  padding: 4px; display: flex; align-items: center; transition: color .13s;
}
.pw-toggle:hover { color: #828a9e; }
.pw-toggle svg { width: 15px; height: 15px; }
.form-input.has-pw { padding-right: 40px; }

.pw-strength { display: flex; gap: 4px; margin-top: 5px; }
.pw-bar { flex: 1; height: 3px; border-radius: 2px; background: rgba(255,255,255,0.07); transition: background .28s; }
.pw-bar.weak { background: #f05a55; }
.pw-bar.medium { background: #d4af64; }
.pw-bar.strong { background: #3ecf82; }
.pw-hint { font-size: 11px; color: #545c72; margin-top: 4px; }

.invite-badge {
  display: inline-flex; align-items: center; gap: 5px;
  font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 600; letter-spacing: .08em;
  color: #d4af64; background: rgba(212,175,100,0.1); border: 1px solid rgba(212,175,100,0.25);
  border-radius: 999px; padding: 2px 8px; margin-bottom: 5px;
}
.i-dot { width: 5px; height: 5px; border-radius: 50%; background: #d4af64; }
.form-input.invite { text-transform: uppercase; letter-spacing: .1em; font-family: 'JetBrains Mono', monospace; font-size: 13px; }

.form-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; margin-top: 4px; }
.remember-wrap { display: flex; align-items: center; gap: 7px; cursor: pointer; }
.remember-cb {
  width: 16px; height: 16px; border-radius: 4px; border: 1.5px solid rgba(255,255,255,0.13);
  background: transparent; appearance: none; cursor: pointer; position: relative;
  transition: background .14s, border-color .14s; flex-shrink: 0;
}
.remember-cb:checked { background: #5b8def; border-color: #5b8def; }
.remember-cb:checked::after { content: ''; position: absolute; top: 2px; left: 5px; width: 4px; height: 7px; border: 1.5px solid #fff; border-top: none; border-left: none; transform: rotate(40deg); }
.remember-label { font-size: 12px; color: #545c72; cursor: pointer; }
.forgot-link { font-size: 12px; color: #545c72; text-decoration: none; transition: color .13s; }
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

.auth-legal { font-size: 11px; color: #545c72; line-height: 1.55; text-align: center; }
.auth-legal a { color: #545c72; text-decoration: underline; transition: color .13s; }
.auth-legal a:hover { color: #828a9e; }
.auth-switch { text-align: center; font-size: 13px; color: #545c72; margin-top: 11px; }
.auth-switch button { background: none; border: none; color: #5b8def; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; padding: 0; transition: opacity .13s; }
.auth-switch button:hover { opacity: .75; }

/* ── RIGHT: BRAND PANEL ── */
.brand-panel {
  position: relative; overflow: hidden;
  background: linear-gradient(155deg, #0e1119 0%, #0b0d16 45%, #0d1020 100%);
  border-left: 1px solid rgba(255,255,255,0.055);
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 44px 44px 44px 48px;
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
.brand-title { font-size: clamp(26px, 2.6vw, 38px); font-weight: 800; line-height: 1.1; letter-spacing: -.03em; margin-bottom: 14px; color: #e4e5ea; }
.brand-title-accent { background: linear-gradient(135deg, #5b8def, #a78bfa 50%, #f05a55); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.brand-desc { font-size: 13px; color: #828a9e; line-height: 1.7; max-width: 310px; }

.quote-card {
  position: relative; z-index: 1;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 18px; padding: 22px 24px;
  transition: opacity .28s, transform .28s;
}
.quote-card.fade-out { opacity: 0; transform: translateY(8px); }
.quote-mark { font-size: 32px; line-height: 1; color: #5b8def; font-family: Georgia, serif; margin-bottom: 7px; opacity: .65; }
.quote-text { font-size: 13px; color: #828a9e; line-height: 1.75; margin-bottom: 16px; }
.quote-author { display: flex; align-items: center; gap: 10px; }
.qa-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #5b8def, #4a7be0); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0; }
.qa-name { font-size: 13px; font-weight: 700; color: #e4e5ea; }
.qa-role { font-size: 11px; color: #545c72; }

.quote-controls { display: flex; gap: 8px; margin-top: 16px; }
.qc-btn {
  width: 34px; height: 34px; border-radius: 9px; border: 1px solid rgba(255,255,255,0.13);
  background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #828a9e; transition: all .15s;
}
.qc-btn:hover { background: rgba(255,255,255,0.10); color: #e4e5ea; border-color: rgba(255,255,255,0.2); }
.qc-btn.next-btn { background: #5b8def; border-color: #5b8def; color: #fff; box-shadow: 0 4px 12px rgba(91,141,239,0.32); }
.qc-btn svg { width: 13px; height: 13px; }

.stats-strip {
  position: relative; z-index: 1;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 15px; padding: 15px 20px;
  display: grid; grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: center; gap: 12px;
}
.sc-item { text-align: center; }
.sc-num { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 600; color: #e4e5ea; line-height: 1; margin-bottom: 2px; }
.sc-num em { color: #5b8def; font-style: normal; font-size: 11px; }
.sc-label { font-size: 10px; color: #545c72; }
.sc-div { width: 1px; height: 32px; background: rgba(255,255,255,0.07); }

@media (max-width: 780px) {
  .card { grid-template-columns: 1fr; min-height: auto; }
  .brand-panel { display: none; }
  .form-panel { padding: 36px 28px; }
}
</style>
