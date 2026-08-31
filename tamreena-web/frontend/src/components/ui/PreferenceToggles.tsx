import { usePreferences } from '../../lib/preferences-context';

/**
 * Theme (dark/light) and language (EN/AR, sets RTL) toggle buttons.
 * Drop into any nav/header — reads/writes the shared preferences context.
 */
function PreferenceToggles() {
  const { theme, language, toggleTheme, toggleLanguage } = usePreferences();

  return (
    <div style={{ display: 'flex', gap: '8px' }}>
      <button
        type="button"
        onClick={toggleTheme}
        className="chrome-toggle-btn"
        aria-label="Toggle dark or light theme"
        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {theme === 'dark' ? '🌙' : '☀️'}
      </button>
      <button
        type="button"
        onClick={toggleLanguage}
        className="chrome-toggle-btn"
        aria-label="Toggle language"
        title={language === 'en' ? 'التبديل إلى العربية' : 'Switch to English'}
      >
        {language === 'en' ? 'العربية' : 'English'}
      </button>
    </div>
  );
}

export default PreferenceToggles;
