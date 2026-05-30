<script setup>
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <div class="app-shell">
    <Sidebar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Rajdhani:wght@400;600;700&display=swap');

:root {
  --bg:        #0a0a1a;
  --panel:     rgba(17, 24, 39, 0.85);
  --border:    rgba(96, 165, 250, 0.25);
  --blue:      #60a5fa;
  --purple:    #a78bfa;
  --cyan:      #06b6d4;
  --pink:      #f472b6;
  --blue-dim:  rgba(96, 165, 250, 0.15);
  --sidebar-w: 64px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  background: var(--bg);
  color: #e0e0e0;
  font-family: 'Inter', sans-serif;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--blue), var(--purple));
  border-radius: 10px;
}
* { scrollbar-width: thin; scrollbar-color: var(--blue-dim) transparent; }

/* ── layout ── */
.app-shell {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a1a 0%, #050510 100%);
}

.main-content {
  flex: 1;
  min-width: 0;
  padding: 24px;
  overflow-y: auto;
}

/* ── shared card / panel primitives ── */
.glass-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  backdrop-filter: blur(12px);
  transition: border-color .3s, box-shadow .3s, transform .3s;
}
.glass-card:hover {
  border-color: rgba(96, 165, 250, .5);
  box-shadow: 0 0 30px rgba(96, 165, 250, .15);
}

/* ── section label ── */
.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .15em;
  color: var(--blue);
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 14px;
}
.section-label::before {
  content: '';
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, var(--blue), var(--purple));
  border-radius: 2px;
  flex-shrink: 0;
}

/* ── stat card ── */
.stat-card {
  position: relative;
  overflow: hidden;
  padding: 22px 24px;
}
.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--blue), var(--purple), var(--pink));
  opacity: .65;
}
.stat-card:hover { transform: translateY(-3px); }
.card-label {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: .1em;
  color: #9ca3af;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.card-value {
  font-family: 'Rajdhani', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 6px;
}
.card-sub { font-size: 11px; color: #6b7280; }

/* ── game list item ── */
.game-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  background: rgba(0,0,0,.3);
  border: 1px solid transparent;
  border-left: 3px solid transparent;
  border-radius: 12px;
  color: #d1d5db;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: all .2s;
  gap: 10px;
  margin-bottom: 6px;
}
.game-item:hover {
  background: rgba(96,165,250,.08);
  border-color: rgba(96,165,250,.3);
  color: #e0e0e0;
  transform: translateX(3px);
}
.game-item--active {
  border-left-color: var(--blue);
  background: linear-gradient(135deg, rgba(96,165,250,.15), rgba(167,139,250,.1));
  border-color: rgba(96,165,250,.5);
  color: var(--blue);
  box-shadow: 0 0 15px rgba(96,165,250,.2);
}
.game-item .game-ccu { font-size:11px; color:#6b7280; white-space:nowrap; font-weight:600; }
.game-item--active .game-ccu { color: var(--blue); }

/* ── range slider ── */
.terminal-range {
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: linear-gradient(90deg, var(--blue-dim), rgba(167,139,250,.2));
  outline: none;
  border-radius: 2px;
  width: 100%;
}
.terminal-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px; height: 16px;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(96,165,250,.5);
  transition: transform .2s, box-shadow .2s;
}
.terminal-range::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 0 15px rgba(96,165,250,.8);
}

/* ── badge helpers ── */
.badge-up   { background: rgba(34,197,94,.15);  color: #4ade80; border: 1px solid rgba(34,197,94,.3); }
.badge-down { background: rgba(239,68,68,.15);  color: #f87171; border: 1px solid rgba(239,68,68,.3); }
.badge-flat { background: rgba(156,163,175,.1); color: #9ca3af; border: 1px solid rgba(156,163,175,.2); }
.badge { padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }

/* ── status dot animation ── */
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .6; transform: scale(.95); }
}
.status-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--blue);
  box-shadow: 0 0 10px var(--blue), 0 0 20px rgba(96,165,250,.5);
  animation: pulse 2s ease-in-out infinite;
}

/* ── page heading ── */
.page-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.6rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: .05em;
}
.page-sub {
  font-size: 12px;
  color: #6b7280;
  letter-spacing: .05em;
  margin-top: 2px;
}

/* ── btn-primary ── */
.btn-primary {
  background: transparent;
  border: 1.5px solid var(--blue);
  color: var(--blue);
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .08em;
  cursor: pointer;
  transition: all .25s;
}
.btn-primary:hover:not(:disabled) {
  background: rgba(96,165,250,.12);
  box-shadow: 0 0 16px rgba(96,165,250,.4);
  transform: translateY(-1px);
}
.btn-primary:disabled { opacity:.4; cursor:not-allowed; }
</style>
