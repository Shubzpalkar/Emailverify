export function applyTheme(themeName) {
  let effectiveTheme = themeName;
  if (!themeName || themeName === 'system') {
    effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  if (effectiveTheme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
  }

  if (themeName) {
    localStorage.setItem('app_theme', themeName);
  }
}

export function getSavedTheme() {
  return localStorage.getItem('app_theme') || 'dark';
}
