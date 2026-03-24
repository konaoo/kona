<template>
  <nav>
    <a href="#" class="nav-brand">
      <img class="nav-logo" src="/assets/logo.svg" alt="logo" />
      <div>
        <div class="nav-name">咔咔记账</div>
      </div>
    </a>
  </nav>
</template>

<style scoped>
nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 58px;
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 190;
  background: rgba(10,11,14,0.75);
  backdrop-filter: blur(16px);
}

.nav-brand {
  display: flex; align-items: center; gap: 10px; text-decoration: none;
}

.nav-logo {
  width: 34px; height: 34px; border-radius: 10px;
  object-fit: cover; display: block;
  box-shadow: 0 6px 16px rgba(240,39,158,0.3);
}

.nav-name { font-size: 15px; font-weight: 700; color: var(--text); line-height: 1.1; }
.nav-tag { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.12em; color: var(--text-muted); }

@media (max-width: 900px) {
  nav { padding: 0 20px; }
}
</style>
