<template>
  <footer>
    <div class="footer-brand">
      <img class="footer-logo" src="/assets/logo.png" alt="logo" />
      <div>
        <div class="footer-name">咔咔记账</div>
        <div class="footer-copy">2026 kaka wallet</div>
      </div>
    </div>
    <div class="footer-links">
      <a href="#" class="footer-link">用户协议</a>
      <a href="#" class="footer-link">隐私政策</a>
      <a href="#" class="footer-link">联系我们</a>
    </div>
  </footer>
</template>

<style scoped>
footer {
  border-top: 1px solid var(--border);
  max-width: 1200px; margin: 0 auto;
  padding: 32px 40px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
}

.footer-brand { display: flex; align-items: center; gap: 8px; }
.footer-logo { width: 26px; height: 26px; border-radius: 7px; object-fit: cover; display: block; }
.footer-name { font-size: 13px; font-weight: 700; color: var(--text); }
.footer-copy { font-size: 11px; color: var(--text-muted); margin-top: 3px; }
.footer-links { display: flex; gap: 18px; }
.footer-link { font-size: 11px; color: var(--text-muted); text-decoration: none; transition: color .14s; }
.footer-link:hover { color: var(--text-sub); }

@media (max-width: 900px) {
  footer { padding: 28px 24px; flex-direction: column; align-items: flex-start; }
}
</style>
