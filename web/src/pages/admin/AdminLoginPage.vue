<template>
  <div class="admin-login-container">
    <div class="bg-photo"></div>

    <div class="card">
      <!-- LEFT FORM -->
      <div class="left">
        <div class="heading">欢迎回来</div>
        <div class="sub-text">请登录您的管理账号</div>

        <div class="field-group">
          <label class="field-label" for="username">用户名</label>
          <input 
            v-model.trim="username"
            class="field-input" 
            id="username" 
            type="text" 
            placeholder="请输入用户名" 
            autocomplete="username"
            @keyup.enter="submit"
          />
        </div>

        <div class="field-group">
          <label class="field-label" for="password">密码</label>
          <input 
            v-model="password"
            class="field-input" 
            id="password" 
            type="password" 
            placeholder="请输入密码" 
            autocomplete="current-password"
            @keyup.enter="submit"
          />
        </div>

        <div class="remember-row">
          <input type="checkbox" id="remember" v-model="rememberMe" />
          <label for="remember">记住账号</label>
        </div>

        <p class="error-msg" v-if="error">{{ error }}</p>

        <button class="signin-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '验证中...' : '登录' }}
        </button>

        <div class="back-link">
          <RouterLink to="/">返回主页</RouterLink>
        </div>
      </div>

      <!-- RIGHT PHOTO -->
      <div class="right">
        <div class="photo-bg"></div>
        <div class="portrait">
          <svg viewBox="0 0 480 580" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <filter id="motionBlur" x="-20%" y="-5%" width="140%" height="110%">
                <feGaussianBlur stdDeviation="6 0.5"/>
              </filter>
              <filter id="softBlur">
                <feGaussianBlur stdDeviation="2"/>
              </filter>
              <filter id="heavyBlur">
                <feGaussianBlur stdDeviation="10 3"/>
              </filter>
              <filter id="faceBlur">
                <feGaussianBlur stdDeviation="1"/>
              </filter>
              <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#b8dde0"/>
                <stop offset="60%" stop-color="#8ec8cc"/>
                <stop offset="100%" stop-color="#5aa8ae"/>
              </linearGradient>
              <linearGradient id="scarfGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#e85c10"/>
                <stop offset="30%" stop-color="#d4380a"/>
                <stop offset="60%" stop-color="#c87020"/>
                <stop offset="100%" stop-color="#b84808"/>
              </linearGradient>
              <linearGradient id="scarfGrad2" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#c8a830"/>
                <stop offset="50%" stop-color="#a89020"/>
                <stop offset="100%" stop-color="#808018"/>
              </linearGradient>
              <radialGradient id="skinGrad" cx="50%" cy="40%" r="50%">
                <stop offset="0%" stop-color="#f0d0b0"/>
                <stop offset="60%" stop-color="#e0b898"/>
                <stop offset="100%" stop-color="#c89878"/>
              </radialGradient>
              <linearGradient id="hairGrad" x1="0.3" y1="0" x2="0.7" y2="1">
                <stop offset="0%" stop-color="#b09878"/>
                <stop offset="40%" stop-color="#887058"/>
                <stop offset="100%" stop-color="#504030"/>
              </linearGradient>
              <linearGradient id="hatGrad" x1="0" y1="0" x2="1" y2="0.5">
                <stop offset="0%" stop-color="#c83020"/>
                <stop offset="50%" stop-color="#e04030"/>
                <stop offset="100%" stop-color="#b02818"/>
              </linearGradient>
              <linearGradient id="hatTeal" x1="0" y1="0" x2="1" y2="0.3">
                <stop offset="0%" stop-color="#208888"/>
                <stop offset="50%" stop-color="#30a8a0"/>
                <stop offset="100%" stop-color="#188080"/>
              </linearGradient>
            </defs>
            <rect width="480" height="580" fill="url(#skyGrad)"/>
            <g filter="url(#heavyBlur)" opacity="0.6">
              <rect x="-60" y="60" width="600" height="18" fill="#c87828" opacity="0.5"/>
              <rect x="-60" y="95" width="600" height="12" fill="#e04030" opacity="0.45"/>
              <rect x="-60" y="120" width="600" height="22" fill="#208888" opacity="0.5"/>
              <rect x="-60" y="150" width="600" height="8" fill="#d06020" opacity="0.4"/>
              <rect x="-60" y="340" width="600" height="30" fill="#c83020" opacity="0.5"/>
              <rect x="-60" y="390" width="600" height="20" fill="#d88020" opacity="0.45"/>
              <rect x="-60" y="430" width="600" height="40" fill="#c05010" opacity="0.5"/>
              <rect x="-60" y="490" width="600" height="25" fill="#a87010" opacity="0.4"/>
              <rect x="-60" y="530" width="600" height="35" fill="#c08818" opacity="0.5"/>
            </g>
            <g filter="url(#motionBlur)">
              <path d="M-40,480 C60,420 160,400 240,410 C320,400 420,420 520,480 L520,600 L-40,600Z" fill="url(#scarfGrad)"/>
              <path d="M-60,440 C40,390 140,380 240,390 C340,380 440,390 540,440 L540,500 C440,460 340,450 240,455 C140,450 40,460 -60,500Z" fill="#d04010" opacity="0.8"/>
              <path d="M-60,460 C20,410 120,400 240,405 C360,400 460,410 540,460 L540,520 L-60,520Z" fill="#c83820" opacity="0.7"/>
              <path d="M-40,510 C60,475 160,465 240,468 C320,465 420,475 520,510 L520,560 C420,540 320,532 240,534 C160,532 60,540 -40,560Z" fill="url(#scarfGrad2)" opacity="0.85"/>
              <path d="M80,420 C100,390 110,370 115,360" stroke="#f06020" stroke-width="3" fill="none" opacity="0.5"/>
              <path d="M160,430 C175,395 182,372 185,358" stroke="#e85818" stroke-width="2.5" fill="none" opacity="0.4"/>
              <path d="M300,425 C318,390 326,368 330,355" stroke="#f07028" stroke-width="3" fill="none" opacity="0.5"/>
              <path d="M380,435 C395,400 402,378 406,365" stroke="#e06018" stroke-width="2" fill="none" opacity="0.4"/>
            </g>
            <g filter="url(#motionBlur)">
              <path d="M120,180 C100,160 90,130 95,100 C100,75 115,60 130,55 C155,48 195,55 215,75 C235,95 238,125 230,155 C250,130 270,110 290,105 C320,100 350,115 365,140 C375,158 370,180 355,192" fill="url(#hairGrad)" opacity="0.9"/>
              <path d="M220,130 C260,110 300,100 340,102 C380,104 420,120 450,145 C470,162 468,180 455,190 C430,205 390,200 355,192" fill="#907860" opacity="0.75"/>
              <path d="M180,100 C240,85 310,80 380,92 C420,100 450,118 460,138" stroke="#a08868" stroke-width="8" fill="none" opacity="0.6"/>
              <path d="M195,115 C255,98 325,92 390,104 C430,112 455,128 462,148" stroke="#b09878" stroke-width="5" fill="none" opacity="0.5"/>
              <path d="M200,125 C260,108 330,102 400,116" stroke="#987860" stroke-width="4" fill="none" opacity="0.4"/>
              <path d="M140,90 C180,65 240,55 300,62 C350,68 400,88 430,115" stroke="#88685a" stroke-width="6" fill="none" opacity="0.5" filter="url(#motionBlur)"/>
              <path d="M155,75 C200,52 265,45 325,54 C375,62 415,82 440,110" stroke="#a07860" stroke-width="4" fill="none" opacity="0.45" filter="url(#motionBlur)"/>
            </g>
            <g filter="url(#motionBlur)">
              <path d="M118,105 C140,80 175,65 210,62 C250,58 295,68 325,88 C355,108 368,132 362,150 C340,125 305,110 270,108 C235,106 195,115 170,130 C155,120 135,115 118,105Z" fill="url(#hatTeal)" opacity="0.9"/>
              <path d="M122,130 C145,110 180,98 215,96 C255,93 295,104 320,122 C340,136 348,152 340,162 C318,148 285,140 255,140 C220,140 185,150 162,165 C148,156 132,145 122,130Z" fill="url(#hatGrad)" opacity="0.92"/>
              <path d="M130,118 C170,100 215,93 260,95 C295,97 325,108 340,124" stroke="rgba(255,180,160,0.4)" stroke-width="3" fill="none"/>
              <path d="M135,138 C175,120 220,113 265,115 C300,117 328,128 343,144" stroke="rgba(255,200,180,0.3)" stroke-width="2" fill="none"/>
            </g>
            <g filter="url(#faceBlur)" opacity="0.85">
              <path d="M180,310 C175,330 172,360 174,390 C178,330 180,310 180,310Z" fill="#d4a888" opacity="0.3"/>
            </g>
            <g filter="url(#faceBlur)">
              <path d="M200,295 C192,310 188,335 190,365 C205,370 225,370 240,365 C242,335 238,310 230,295Z" fill="#e8c0a0"/>
              <ellipse cx="215" cy="240" rx="68" ry="78" fill="url(#skinGrad)"/>
              <path d="M152,255 C155,290 175,318 215,325 C255,318 275,290 278,255" fill="#e0b898" opacity="0.6"/>
              <ellipse cx="150" cy="248" rx="10" ry="14" fill="#d8ac8a"/>
              <ellipse cx="178" cy="268" rx="22" ry="14" fill="#e8c0a0" opacity="0.4"/>
              <ellipse cx="252" cy="265" rx="20" ry="13" fill="#c89878" opacity="0.3"/>
              <ellipse cx="178" cy="270" rx="18" ry="9" fill="#e8a080" opacity="0.22"/>
              <ellipse cx="250" cy="268" rx="16" ry="8" fill="#e8a080" opacity="0.18"/>
              <path d="M208,248 C206,255 205,262 208,268 C211,272 219,274 225,272 C229,268 228,262 226,255" fill="none" stroke="#c09070" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/>
              <ellipse cx="215" cy="270" rx="10" ry="5" fill="#c89878" opacity="0.25"/>
              <path d="M172,232 C180,225 196,224 205,230 C196,238 180,239 172,232Z" fill="#f5e5d0"/>
              <path d="M174,231 C181,226 197,225 205,230 C197,237 181,238 174,231Z" fill="#6a4830"/>
              <circle cx="191" cy="231" r="7" fill="#3a2818"/>
              <circle cx="191" cy="231" r="5" fill="#1a0e08"/>
              <circle cx="194" cy="228" r="2" fill="rgba(255,255,255,0.7)"/>
              <path d="M172,230 C181,222 198,221 207,228" fill="none" stroke="#b08060" stroke-width="1.2" opacity="0.6"/>
              <path d="M172,231 C178,226 188,224 200,226 C203,227 205,229 205,230" fill="none" stroke="#1a0e08" stroke-width="2" stroke-linecap="round"/>
              <path d="M224,228 C232,222 245,222 252,228 C245,236 232,236 224,228Z" fill="#f0deca"/>
              <path d="M226,227 C233,223 245,223 252,228 C245,235 233,235 226,227Z" fill="#6a4830"/>
              <circle cx="238" cy="228" r="6" fill="#3a2818"/>
              <circle cx="238" cy="228" r="4" fill="#1a0e08"/>
              <circle cx="241" cy="226" r="1.5" fill="rgba(255,255,255,0.7)"/>
              <path d="M224,227 C231,221 244,220 252,226" fill="none" stroke="#1a0e08" stroke-width="1.8" stroke-linecap="round"/>
              <path d="M168,220 C178,213 198,212 208,218" fill="none" stroke="#5a3820" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M222,216 C231,210 246,210 254,216" fill="none" stroke="#5a3820" stroke-width="2.2" stroke-linecap="round"/>
              <path d="M196,296 C203,290 212,288 222,290 C228,292 233,296 234,300 C228,308 220,312 215,312 C210,312 202,308 196,300 C195,298 195,297 196,296Z" fill="#c07860"/>
              <path d="M196,296 C200,292 207,289 215,289 C223,289 230,292 234,296" fill="none" stroke="#a06048" stroke-width="1.5" stroke-linecap="round"/>
              <path d="M204,294 C209,291 220,291 228,294" fill="none" stroke="rgba(255,200,180,0.5)" stroke-width="1.2" stroke-linecap="round"/>
              <path d="M212,276 C213,282 214,287 215,289" fill="none" stroke="#c09070" stroke-width="1" opacity="0.5" stroke-linecap="round"/>
            </g>
            <g filter="url(#heavyBlur)" opacity="0.18">
              <rect x="-60" y="220" width="600" height="6" fill="#e04030"/>
              <rect x="-60" y="245" width="600" height="4" fill="#30a8a0"/>
              <rect x="-60" y="275" width="600" height="5" fill="#d08020"/>
            </g>
            <radialGradient id="vignette" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stop-color="transparent"/>
              <stop offset="100%" stop-color="rgba(0,0,0,0.45)"/>
            </radialGradient>
            <rect width="480" height="580" fill="url(#vignette)"/>
          </svg>
        </div>
        <div class="photo-overlay"></div>
      </div>
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
const rememberMe = ref(true)
const error = ref('')
const submitting = ref(false)

async function submit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  
  error.value = ''
  submitting.value = true
  try {
    await store.login(username.value, password.value)
    // 验证管理员权限
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
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

.admin-login-container {
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a0a05;
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
  position: relative;
}

/* Full-bleed blurred photo background */
.bg-photo {
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse at 15% 50%, rgba(210,80,20,0.55) 0%, transparent 45%),
    radial-gradient(ellipse at 85% 20%, rgba(20,160,155,0.5) 0%, transparent 40%),
    radial-gradient(ellipse at 60% 80%, rgba(180,60,10,0.4) 0%, transparent 40%),
    linear-gradient(135deg, #8b3a10 0%, #1a3a38 50%, #0d1a18 100%);
}

.bg-photo::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.25);
}

/* CARD */
.card {
  position: relative;
  z-index: 1;
  display: flex;
  width: 900px;
  max-width: 97vw;
  min-height: 580px;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 40px 120px rgba(0,0,0,0.55), 0 8px 32px rgba(0,0,0,0.3);
}

/* ── LEFT: FORM ── */
.left {
  width: 52%;
  flex-shrink: 0;
  background: #f4f4f2;
  padding: 64px 58px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.heading {
  font-family: 'Playfair Display', serif;
  font-size: 38px;
  font-weight: 800;
  color: #0f0f0f;
  letter-spacing: -.02em;
  line-height: 1.15;
  margin-bottom: 8px;
}

.sub-text {
  font-size: 14px;
  color: #888;
  font-weight: 400;
  margin-bottom: 40px;
  letter-spacing: .01em;
}

/* Labels */
.field-group {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 7px;
  letter-spacing: .01em;
}

/* Input */
.field-input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  background: #fff;
  border: 1.5px solid #d8d8d8;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: #1a1a1a;
  outline: none;
  transition: border-color .18s, box-shadow .18s;
  letter-spacing: .01em;
}

.field-input::placeholder {
  color: #bbb;
  font-weight: 400;
}

.field-input:focus {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.06);
}

/* Remember row */
.remember-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0 24px;
}

.remember-row input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: #1a1a1a;
  cursor: pointer;
  flex-shrink: 0;
  border-radius: 3px;
}

.remember-row label {
  font-size: 13px;
  color: #555;
  font-weight: 400;
  cursor: pointer;
  user-select: none;
}

.error-msg {
  color: #e04030;
  font-size: 13px;
  margin-bottom: 16px;
  font-weight: 500;
}

/* Sign in button */
.signin-btn {
  width: 100%;
  height: 48px;
  background: #0f0f0f;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: .02em;
  transition: background .15s, transform .12s, box-shadow .15s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.18);
}

.signin-btn:hover:not(:disabled) {
  background: #2a2a2a;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.signin-btn:active:not(:disabled) {
  transform: translateY(0);
}

.signin-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.back-link {
  margin-top: 24px;
  text-align: center;
}

.back-link a {
  font-size: 13px;
  color: #888;
  text-decoration: none;
  transition: color 0.15s;
}

.back-link a:hover {
  color: #1a1a1a;
}

/* ── RIGHT: PHOTO ── */
.right {
  flex: 1;
  position: relative;
  overflow: hidden;
  border-radius: 0 20px 20px 0;
}

.photo-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 55% 35%, rgba(240,200,160,0.95) 0%, rgba(200,130,80,0.7) 25%, transparent 55%),
    radial-gradient(ellipse at 75% 65%, rgba(180,60,20,0.8) 0%, rgba(140,40,10,0.5) 35%, transparent 60%),
    radial-gradient(ellipse at 30% 55%, rgba(230,120,40,0.6) 0%, transparent 45%),
    radial-gradient(ellipse at 80% 20%, rgba(20,155,155,0.7) 0%, rgba(10,100,100,0.4) 30%, transparent 55%),
    radial-gradient(ellipse at 20% 80%, rgba(200,80,20,0.5) 0%, transparent 40%),
    linear-gradient(160deg, #c5e8e6 0%, #7ab8b5 20%, #2a6a68 45%, #1a2a28 80%, #0d1612 100%);
}

.photo-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(85deg,
      transparent 20%,
      rgba(230,180,100,0.15) 28%,
      rgba(220,100,30,0.12) 32%,
      transparent 38%,
      rgba(200,60,20,0.1) 45%,
      transparent 52%,
      rgba(20,140,140,0.12) 60%,
      transparent 68%,
      rgba(210,90,30,0.1) 75%,
      transparent 82%
    );
  filter: blur(3px);
}

.photo-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60px 80px at 52% 30%, rgba(240,215,185,0.9) 0%, rgba(220,180,140,0.5) 50%, transparent 80%),
    radial-gradient(ellipse 30px 40px at 52% 38%, rgba(200,150,110,0.7) 0%, transparent 70%);
  filter: blur(1px);
}

.photo-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(
    to right,
    rgba(244,244,242,0.08) 0%,
    transparent 15%
  );
}

.right::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 3;
  border-radius: 0 20px 20px 0;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
  pointer-events: none;
}

.portrait {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.portrait svg {
  width: 100%;
  height: 100%;
  position: absolute;
  inset: 0;
}

@media (max-width: 920px) {
  .card {
    width: 480px;
    min-height: auto;
  }
  .right {
    display: none;
  }
  .left {
    width: 100%;
    padding: 48px 40px;
  }
}
</style>
