import { ref } from 'vue'

export type WebTheme = 'dark' | 'light'

const STORAGE_KEY = 'kaka_web_theme'

function normalizeTheme(value: unknown): WebTheme {
  return value === 'light' ? 'light' : 'dark'
}

function readStoredTheme(): WebTheme {
  if (typeof window === 'undefined') return 'dark'
  try {
    return normalizeTheme(localStorage.getItem(STORAGE_KEY))
  } catch {
    return 'dark'
  }
}

const theme = ref<WebTheme>(readStoredTheme())

function applyTheme(next: WebTheme) {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', next)
  document.body?.setAttribute('data-theme', next)
}

function persistTheme(next: WebTheme) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // ignore storage errors
  }
}

function setTheme(next: WebTheme) {
  theme.value = normalizeTheme(next)
  persistTheme(theme.value)
  applyTheme(theme.value)
}

applyTheme(theme.value)

function toggleTheme() {
  setTheme(theme.value === 'dark' ? 'light' : 'dark')
}

export function useWebTheme() {
  return {
    theme,
    setTheme,
    toggleTheme,
  }
}
