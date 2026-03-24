import { ref } from 'vue'

const STORAGE_KEY = 'privacy_mode'

function normalizePrivacy(value: unknown): boolean {
  return value === true || value === 'true' || value === '1'
}

function readStoredPrivacy(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return normalizePrivacy(localStorage.getItem(STORAGE_KEY))
  } catch {
    return false
  }
}

const isPrivacyMode = ref<boolean>(readStoredPrivacy())
let storageListenerAttached = false

function persistPrivacy(value: boolean) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, value ? 'true' : 'false')
  } catch {
    // ignore storage errors
  }
}

function ensureStorageSync() {
  if (storageListenerAttached || typeof window === 'undefined') return
  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY) return
    isPrivacyMode.value = normalizePrivacy(event.newValue)
  })
  storageListenerAttached = true
}

function setPrivacyMode(next: boolean) {
  const value = Boolean(next)
  isPrivacyMode.value = value
  persistPrivacy(value)
}

function togglePrivacy() {
  setPrivacyMode(!isPrivacyMode.value)
}

function maskValue(text: string): string {
  return isPrivacyMode.value ? '***' : text
}

export function usePrivacyMode() {
  ensureStorageSync()
  return {
    isPrivacyMode,
    setPrivacyMode,
    togglePrivacy,
    maskValue,
  }
}
