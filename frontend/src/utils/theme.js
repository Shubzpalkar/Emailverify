let systemThemeListenerAttached = false;

function resolveTheme(themeName) {
  if (themeName === 'system' || !themeName) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return themeName === 'dark' ? 'dark' : 'light';
}

function handleSystemThemeChange() {
  if (getSavedTheme() === 'system') {
    applyTheme('system', false);
  }
}

export function applyTheme(themeName, persist = true) {
  const effectiveTheme = resolveTheme(themeName);
  document.documentElement.setAttribute('data-theme', effectiveTheme);
  document.documentElement.style.colorScheme = effectiveTheme;

  if (persist && themeName) {
    localStorage.setItem('app_theme', themeName);
  }

  if (!systemThemeListenerAttached && window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', handleSystemThemeChange);
    systemThemeListenerAttached = true;
  }
}

export function getSavedTheme() {
  return localStorage.getItem('app_theme') || 'system';
}
