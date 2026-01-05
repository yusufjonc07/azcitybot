// Telegram WebApp types and utilities

export interface TelegramWebAppUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
  is_premium?: boolean
  photo_url?: string
}

export interface TelegramWebAppInitData {
  query_id?: string
  user?: TelegramWebAppUser
  auth_date: number
  hash: string
}

export interface TelegramWebApp {
  initData: string
  initDataUnsafe: TelegramWebAppInitData
  version: string
  platform: string
  colorScheme: "light" | "dark"
  themeParams: {
    bg_color?: string
    text_color?: string
    hint_color?: string
    link_color?: string
    button_color?: string
    button_text_color?: string
    secondary_bg_color?: string
  }
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
  headerColor: string
  backgroundColor: string
  isClosingConfirmationEnabled: boolean
  ready: () => void
  expand: () => void
  close: () => void
  enableClosingConfirmation: () => void
  disableClosingConfirmation: () => void
  setHeaderColor: (color: string) => void
  setBackgroundColor: (color: string) => void
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp
    }
  }
}

/**
 * Check if running inside Telegram Mini App
 */
export function isTelegramMiniApp(): boolean {
  return !!(
    typeof window !== "undefined" &&
    window.Telegram?.WebApp?.initData &&
    window.Telegram.WebApp.initData.length > 0
  )
}

/**
 * Get Telegram WebApp instance
 */
export function getTelegramWebApp(): TelegramWebApp | null {
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    return window.Telegram.WebApp
  }
  return null
}

/**
 * Get user data from Telegram Mini App
 */
export function getTelegramWebAppUser(): TelegramWebAppUser | null {
  const webApp = getTelegramWebApp()
  if (webApp?.initDataUnsafe?.user) {
    return webApp.initDataUnsafe.user
  }
  return null
}

/**
 * Get init data string for authentication
 */
export function getTelegramInitData(): string | null {
  const webApp = getTelegramWebApp()
  if (webApp?.initData) {
    return webApp.initData
  }
  return null
}
