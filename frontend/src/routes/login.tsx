import { useQuery } from "@tanstack/react-query"
import {
  createFileRoute,
  redirect,
} from "@tanstack/react-router"

import { LoginService, type TelegramLoginData } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import { TelegramLoginButton } from "@/components/Common/TelegramLoginButton"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Log In - AzCity CRM",
      },
    ],
  }),
})

function Login() {
  const { loginMutation, isAutoLoggingIn, isMiniApp } = useAuth()

  const { data: telegramConfig, isLoading } = useQuery({
    queryKey: ["telegramConfig"],
    queryFn: LoginService.getTelegramConfig,
  })

  const handleTelegramAuth = (data: TelegramLoginData) => {
    if (loginMutation.isPending) return
    loginMutation.mutate(data)
  }

  // Show loading state for Mini App auto-login
  if (isAutoLoggingIn || (isMiniApp && !isLoggedIn())) {
    return (
      <AuthLayout>
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-2xl font-bold">Signing in...</h1>
            <p className="text-muted-foreground text-sm">
              Connecting with Telegram...
            </p>
          </div>
          <div className="flex justify-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-bold">Login to your account</h1>
          <p className="text-muted-foreground text-sm">
            Use your Telegram account to sign in
          </p>
        </div>

        <div className="flex flex-col items-center gap-4 py-4">
          {isLoading ? (
            <div className="text-muted-foreground text-sm">Loading...</div>
          ) : telegramConfig?.bot_username ? (
            <TelegramLoginButton
              botName={telegramConfig.bot_username}
              onAuth={handleTelegramAuth}
              buttonSize="large"
              cornerRadius={8}
            />
          ) : (
            <div className="text-destructive text-sm">
              Telegram bot not configured
            </div>
          )}

          {loginMutation.isPending && (
            <div className="text-muted-foreground text-sm">Signing in...</div>
          )}
        </div>
      </div>
    </AuthLayout>
  )
}
