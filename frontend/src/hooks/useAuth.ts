import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import {
  LoginService,
  type TelegramLoginData,
  type UserPublic,
  UsersService,
} from "@/client"
import { isTelegramMiniApp, getTelegramInitData, getTelegramWebApp } from "@/lib/telegram"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  const [isAutoLoggingIn, setIsAutoLoggingIn] = useState(false)
  const [autoLoginAttempted, setAutoLoginAttempted] = useState(false)

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const loginWithTelegram = async (data: TelegramLoginData) => {
    const response = await LoginService.loginWithTelegram({
      requestBody: data,
    })
    localStorage.setItem("access_token", response.access_token)
  }

  const loginWithWebApp = async (initData: string) => {
    const response = await LoginService.loginWithWebApp({
      requestBody: { init_data: initData },
    })
    localStorage.setItem("access_token", response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: loginWithTelegram,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const webAppLoginMutation = useMutation({
    mutationFn: loginWithWebApp,
    onSuccess: () => {
      // Notify Telegram WebApp that we're ready
      const webApp = getTelegramWebApp()
      if (webApp) {
        webApp.ready()
        webApp.expand()
      }
      navigate({ to: "/" })
    },
    onError: (error) => {
      console.error("WebApp auto-login failed:", error)
      setIsAutoLoggingIn(false)
    },
  })

  // Auto-login for Telegram Mini App
  useEffect(() => {
    const attemptWebAppLogin = async () => {
      if (autoLoginAttempted || isLoggedIn()) {
        return
      }

      setAutoLoginAttempted(true)

      if (isTelegramMiniApp()) {
        const initData = getTelegramInitData()
        if (initData) {
          setIsAutoLoggingIn(true)
          webAppLoginMutation.mutate(initData)
        }
      }
    }

    attemptWebAppLogin()
  }, [autoLoginAttempted])

  const logout = () => {
    localStorage.removeItem("access_token")
    queryClient.clear()
    navigate({ to: "/login" })
  }

  return {
    loginMutation,
    webAppLoginMutation,
    logout,
    user,
    isAutoLoggingIn,
    isMiniApp: isTelegramMiniApp(),
  }
}

export { isLoggedIn }
export default useAuth
