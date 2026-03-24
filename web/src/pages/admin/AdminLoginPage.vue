<template>
  <div class="admin-login-container" @mousemove="handleMousemove">
    <div class="card" :class="{ 
      'email-focus': usernameFocused, 
      'pw-focus': passwordFocused,
      'error-state': errorState 
    }" id="card">

      <!-- LEFT: CHARACTERS -->
      <div class="left">
        <div class="stage">
          <!-- Orange semicircle -->
          <div class="char-orange">
            <div class="face">
              <div class="eye"></div>
              <div class="eye"></div>
              <div class="mouth"></div>
            </div>
          </div>

          <!-- Purple tall -->
          <div class="char-purple">
            <div class="hand-l"></div>
            <div class="hand-r"></div>
            <div class="face">
              <div class="eyes-row">
                <div class="eye"><div class="pupil" :style="pupilStyle"></div></div>
                <div class="eye"><div class="pupil" :style="pupilStyle"></div></div>
              </div>
              <div class="mouth-line"></div>
            </div>
            <div class="arm-l"></div>
            <div class="arm-r"></div>
          </div>

          <!-- Black rectangle -->
          <div class="char-black">
            <div class="face">
              <div class="eyes-row">
                <div class="eye">
                  <div class="eyebrow"></div>
                  <div class="pupil" :style="pupilStyle"></div>
                </div>
                <div class="eye">
                  <div class="eyebrow"></div>
                  <div class="pupil" :style="pupilStyle"></div>
                </div>
              </div>
              <div class="mouth-w"></div>
            </div>
          </div>

          <!-- Yellow droplet -->
          <div class="char-yellow">
            <div class="face">
              <div class="dot"></div>
              <div class="mouth-y"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: FORM -->
      <div class="right">
        <!-- Star logo -->
        <div class="logo">
          <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2 L15.5 12 L24 14 L15.5 16 L14 26 L12.5 16 L4 14 L12.5 12 Z" fill="#1a1a1f"/>
          </svg>
        </div>

        <div class="heading">登录账号</div>

        <!-- Username -->
        <div class="field-group" :class="{ 'active': usernameFocused, 'filled': !!username, 'error': !!error && !username }">
          <label class="field-label" for="username">用户名</label>
          <div class="field-wrap">
            <input
              class="field-input"
              id="username"
              type="text"
              v-model.trim="username"
              placeholder="请输入用户名"
              autocomplete="username"
              @focus="usernameFocused = true"
              @blur="usernameFocused = false"
              @keyup.enter="submit"
            />
          </div>
          <div class="err-msg" v-if="!username && error">请输入有效的用户名</div>
        </div>

        <!-- Password -->
        <div class="field-group" :class="{ 'active': passwordFocused, 'filled': !!password, 'error': !!error && !password }">
          <label class="field-label" for="password">密码</label>
          <div class="field-wrap">
            <input
              class="field-input"
              id="password"
              :type="eyeVisible ? 'text' : 'password'"
              v-model="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              @focus="passwordFocused = true"
              @blur="passwordFocused = false"
              @keyup.enter="submit"
            />
            <button class="eye-toggle" type="button" tabindex="-1" @click="eyeVisible = !eyeVisible">
              <svg v-if="!eyeVisible" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
          <div class="err-msg" v-if="!password && error">请输入您的密码</div>
        </div>

        <!-- Options -->
        <div class="options-row">
          <label class="remember">
            <input type="checkbox" v-model="rememberMe" />
            <span>记住登录状态</span>
          </label>
        </div>

        <p class="error-summary" v-if="error && username && password">{{ error }}</p>

        <!-- Log In -->
        <button class="login-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '验证中...' : '登录' }}
        </button>

        <div class="bottom-text">
          <RouterLink to="/" style="color: #999; text-decoration: none;">返回主页</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
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

// Animation states
const usernameFocused = ref(false)
const passwordFocused = ref(false)
const errorState = ref(false)
const eyeVisible = ref(false)
const pupilX = ref(0)
const pupilY = ref(0)

const pupilStyle = computed(() => {
  if (passwordFocused.value) return {}
  return { transform: `translate(${pupilX.value}px, ${pupilY.value}px)` }
})

function handleMousemove(e: MouseEvent) {
  if (passwordFocused.value) return

  // Loosely track cursor for pupils
  const cx = window.innerWidth * 0.4
  const cy = window.innerHeight * 0.5
  const dx = (e.clientX - cx) / 200
  const dy = (e.clientY - cy) / 200

  const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v))
  pupilX.value = clamp(dx, -2.5, 2.5)
  pupilY.value = clamp(dy, -2.5, 2.5)
}

async function submit() {
  if (!username.value || !password.value) {
    triggerError('请输入用户名和密码')
    return
  }

  error.value = ''
  submitting.value = true
  try {
    await store.login(username.value, password.value)
    // Verify admin permission
    await api.get('/api/admin/overview')
    await router.push('/admin/overview')
  } catch (e) {
    await store.logout()
    triggerError(e instanceof Error ? e.message : '登录失败')
  } finally {
    submitting.value = false
  }
}

function triggerError(msg: string) {
  error.value = msg
  errorState.value = true
  setTimeout(() => {
    errorState.value = false
  }, 1200)
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.admin-login-container {
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
  position: relative;
  /* 恢复富有层次感的深色渐变背景 */
  background: 
    radial-gradient(ellipse at 15% 50%, rgba(107, 62, 245, 0.15) 0%, transparent 45%),
    radial-gradient(ellipse at 85% 20%, rgba(244, 128, 42, 0.15) 0%, transparent 40%),
    linear-gradient(135deg, #0d0d10 0%, #1a1a1f 100%);
}

/* CARD */
.card {
  display: flex !important;
  flex-direction: row !important;
  align-items: stretch !important;
  width: 900px !important;
  max-width: 98vw !important;
  height: 580px !important;
  border-radius: 20px !important;
  overflow: hidden !important;
  background: #fff !important;
  box-shadow: 0 40px 100px rgba(0,0,0,0.6) !important;
  position: relative !important;
  z-index: 10 !important;
  padding: 0 !important; /* 强制清除任何注入的内边距 */
  margin: 0 !important;
}

/* ── LEFT: CHARACTERS ── */
.left {
  width: 44% !important;
  height: 100% !important; 
  flex-shrink: 0 !important;
  background: #ebebeb !important;
  position: relative !important;
  display: flex !important;
  align-items: flex-end !important;
  justify-content: center !important;
  overflow: hidden !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
}

.stage {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* ORANGE semicircle */
.char-orange {
  position: absolute;
  bottom: 0;
  left: 30px;
  width: 130px;
  height: 80px;
  background: #F4802A;
  border-radius: 80px 80px 0 0;
  transition: transform .46s cubic-bezier(.34,1.4,.64,1);
  z-index: 1;
}
.char-orange .face {
  position: absolute;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
}
.char-orange .eye {
  width: 6px;
  height: 6px;
  background: #1a1a1f;
  border-radius: 50%;
}
.char-orange .mouth {
  position: absolute;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 18px;
  height: 9px;
  border: 3px solid #1a1a1f;
  border-top: none;
  border-radius: 0 0 12px 12px;
  transition: all .3s;
}

/* PURPLE tall rectangle */
.char-purple {
  position: absolute;
  bottom: 0;
  left: 110px;
  width: 90px;
  height: 220px;
  background: #6B3EF5;
  border-radius: 8px 8px 0 0;
  transition: transform .5s cubic-bezier(.34,1.3,.64,1), height .4s ease;
  z-index: 2;
  transform-origin: bottom center;
}
.char-purple .face {
  position: absolute;
  top: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.char-purple .eyes-row {
  display: flex;
  gap: 12px;
}
.char-purple .eye {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  position: relative;
  overflow: hidden;
}
.char-purple .pupil {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #1a1a1f;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform .15s ease-out;
}
.char-purple .mouth-line {
  width: 16px;
  height: 3px;
  background: #1a1a1f;
  border-radius: 2px;
}
.char-purple .arm-l, .char-purple .arm-r {
  position: absolute;
  bottom: 30px;
  width: 30px;
  height: 14px;
  background: #5530d4;
  border-radius: 7px;
  opacity: 0;
  transition: transform .45s cubic-bezier(.34,1.4,.64,1), opacity .3s;
}
.char-purple .arm-l { left: -22px; transform-origin: right center; }
.char-purple .arm-r { right: -22px; transform-origin: left center; }

.char-purple .hand-l, .char-purple .hand-r {
  position: absolute;
  top: 26px;
  width: 22px;
  height: 18px;
  background: #5530d4;
  border-radius: 5px;
  opacity: 0;
  transition: opacity .3s, top .4s cubic-bezier(.34,1.4,.64,1);
}
.char-purple .hand-l { left: -6px; }
.char-purple .hand-r { right: -6px; }

/* BLACK rectangle */
.char-black {
  position: absolute;
  bottom: 0;
  left: 180px;
  width: 80px;
  height: 190px;
  background: #1a1a1f;
  border-radius: 8px 8px 0 0;
  transition: transform .5s cubic-bezier(.34,1.3,.64,1);
  z-index: 3;
  transform-origin: bottom center;
}
.char-black .face {
  position: absolute;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.char-black .eyes-row {
  display: flex;
  gap: 8px;
}
.char-black .eye {
  width: 10px;
  height: 10px;
  background: #fff;
  border-radius: 50%;
  position: relative;
  overflow: hidden;
  transition: all .3s;
}
.char-black .pupil {
  position: absolute;
  width: 5px;
  height: 5px;
  background: #1a1a1f;
  border-radius: 50%;
  top: 2.5px;
  left: 2.5px;
  transition: transform .15s ease-out;
}
.char-black .eyebrow {
  width: 10px;
  height: 3px;
  background: #fff;
  border-radius: 2px;
  position: absolute;
  top: -7px;
  left: 0;
  transition: transform .3s, top .3s;
}
.char-black .mouth-w {
  width: 14px;
  height: 4px;
  background: #fff;
  border-radius: 2px;
}

/* YELLOW droplet shape */
.char-yellow {
  position: absolute;
  bottom: 0;
  left: 238px;
  width: 85px;
  height: 170px;
  background: #F5C842;
  border-radius: 50% 50% 0 0 / 40% 40% 0 0;
  transition: transform .5s cubic-bezier(.34,1.3,.64,1);
  z-index: 2;
  transform-origin: bottom center;
}
.char-yellow .face {
  position: absolute;
  top: 55px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.char-yellow .dot {
  width: 5px;
  height: 5px;
  background: #1a1a1f;
  border-radius: 50%;
}
.char-yellow .mouth-y {
  width: 14px;
  height: 2px;
  background: #1a1a1f;
  border-radius: 1px;
}

/* ── RIGHT: FORM ── */
.right {
  flex: 1;
  background: #fff;
  padding: 48px 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.logo {
  text-align: center;
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 900;
  color: #1a1a1f;
}
.logo svg { width: 28px; height: 28px; vertical-align: middle; }

.heading {
  text-align: center;
  font-size: 26px;
  font-weight: 800;
  color: #1a1a1f;
  letter-spacing: -.02em;
  margin-bottom: 4px;
}
.sub {
  text-align: center;
  font-size: 13px;
  color: #999;
  font-weight: 400;
  margin-bottom: 28px;
}

/* Field */
.field-group { margin-bottom: 14px; position: relative; }
.field-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #999;
  margin-bottom: 4px;
  transition: color .2s;
}
.field-group.active .field-label,
.field-group.filled .field-label { color: #1a1a1f; }

.field-wrap { position: relative; }
.field-input {
  width: 100%;
  height: 42px;
  padding: 0 36px 0 0;
  background: transparent;
  border: none;
  border-bottom: 1.5px solid #e0e0e0;
  font-family: inherit;
  font-size: 14px;
  color: #1a1a1f;
  outline: none;
  transition: border-color .2s;
}
.field-input::placeholder { color: transparent; }
.field-input:focus { border-color: #1a1a1f; }

.eye-toggle {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #bbb;
  padding: 4px;
  transition: color .2s;
}
.eye-toggle:hover { color: #1a1a1f; }
.eye-toggle svg { width: 18px; height: 18px; display: block; }

.options-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0 20px;
}
.remember { display: flex; align-items: center; gap: 7px; cursor: pointer; }
.remember input { width: 14px; height: 14px; accent-color: #1a1a1f; cursor: pointer; }
.remember span { font-size: 12px; color: #666; }

.error-summary {
  font-size: 11px;
  color: #F4802A;
  margin-bottom: 10px;
  text-align: center;
}

.login-btn {
  width: 100%;
  height: 46px;
  background: #1a1a1f;
  color: #fff;
  border: none;
  border-radius: 999px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s, transform .12s;
  margin-bottom: 10px;
}
.login-btn:hover:not(:disabled) { background: #333; transform: translateY(-1px); }
.login-btn:active:not(:disabled) { transform: translateY(0); }
.login-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.err-msg {
  font-size: 11px;
  color: #F4802A;
  margin-top: 3px;
}

.bottom-text {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-top: 16px;
}

/* ── STATE: PASSWORD FOCUS — characters cover eyes ── */
.card.pw-focus .char-purple .hand-l,
.card.pw-focus .char-purple .hand-r { opacity: 1; top: 24px; }

.card.pw-focus .char-black .eye {
  height: 5px;
  border-radius: 3px;
}
.card.pw-focus .char-black .eyebrow { top: -10px; }

.card.pw-focus .char-yellow { transform: rotate(12deg) translateX(8px); }

.card.pw-focus .char-orange .mouth {
  border-radius: 12px 12px 0 0;
  border-top: 3px solid #1a1a1f;
  border-bottom: none;
  bottom: 18px;
}

/* ── STATE: EMAIL FOCUS ── */
.card.email-focus .char-purple { transform: rotate(-6deg) translateY(-12px); }
.card.email-focus .char-black { transform: rotate(4deg) translateY(-8px); }
.card.email-focus .char-yellow { transform: translateY(-10px); }
.card.email-focus .char-orange { transform: translateY(-8px); }

/* ── STATE: ERROR ── */
.card.error-state .char-purple { transform: rotate(-15deg) translateY(-5px); }
.card.error-state .char-black { transform: rotate(12deg) translateY(-10px); }
.card.error-state .char-yellow { transform: rotate(-8deg) translateY(-5px); }
.card.error-state .char-orange { transform: translateY(-5px); }
.card.error-state .char-orange .mouth {
  border-radius: 12px 12px 0 0;
  border-top: 3px solid #1a1a1f;
  border-bottom: none;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-8px); }
  40% { transform: translateX(8px); }
  60% { transform: translateX(-6px); }
  80% { transform: translateX(6px); }
}
.card.error-state {
  animation: shake 0.4s ease;
}

/* Entrance animation */
.char-orange, .char-purple, .char-black, .char-yellow {
  animation: slideUp 0.6s cubic-bezier(.34,1.4,.64,1) backwards;
}
.char-orange { animation-delay: 0.1s; }
.char-purple { animation-delay: 0.18s; }
.char-black { animation-delay: 0.26s; }
.char-yellow { animation-delay: 0.34s; }

@keyframes slideUp {
  from { transform: translateY(80px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@media (max-width: 920px) {
  .left {
    display: none;
  }
  .right {
    width: 100%;
    padding: 32px 24px;
  }
}
</style>
