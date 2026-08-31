import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export type Theme = 'dark' | 'light';
export type Language = 'en' | 'ar';

interface PreferencesContextValue {
  theme: Theme;
  language: Language;
  toggleTheme: () => void;
  toggleLanguage: () => void;
}

const PreferencesContext = createContext<PreferencesContextValue>({
  theme: 'dark',
  language: 'en',
  toggleTheme: () => {},
  toggleLanguage: () => {},
});

const THEME_KEY = 'tamrena_theme';
const LANG_KEY = 'tamrena_language';

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem(THEME_KEY) as Theme) || 'dark');
  const [language, setLanguage] = useState<Language>(() => (localStorage.getItem(LANG_KEY) as Language) || 'en');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute('lang', language);
    document.documentElement.setAttribute('dir', language === 'ar' ? 'rtl' : 'ltr');
    localStorage.setItem(LANG_KEY, language);
  }, [language]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  const toggleLanguage = () => setLanguage((l) => (l === 'en' ? 'ar' : 'en'));

  return (
    <PreferencesContext.Provider value={{ theme, language, toggleTheme, toggleLanguage }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences(): PreferencesContextValue {
  return useContext(PreferencesContext);
}
