import { useEffect, useRef } from "react"
import type { TelegramLoginData } from "@/client"

interface TelegramLoginButtonProps {
  botName: string
  onAuth: (data: TelegramLoginData) => void
  buttonSize?: "large" | "medium" | "small"
  cornerRadius?: number
  requestAccess?: "write"
  usePic?: boolean
  lang?: string
}

declare global {
  interface Window {
    TelegramLoginWidget: {
      dataOnauth: (user: TelegramLoginData) => void
    }
  }
}

export function TelegramLoginButton({
  botName,
  onAuth,
  buttonSize = "large",
  cornerRadius,
  requestAccess = "write",
  usePic = true,
  lang = "en",
}: TelegramLoginButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Set up the callback function
    window.TelegramLoginWidget = {
      dataOnauth: (user: TelegramLoginData) => {
        onAuth(user)
      },
    }

    // Create script element
    const script = document.createElement("script")
    script.src = "https://telegram.org/js/telegram-widget.js?22"
    script.async = true
    script.setAttribute("data-telegram-login", botName)
    script.setAttribute("data-size", buttonSize)
    script.setAttribute("data-onauth", "TelegramLoginWidget.dataOnauth(user)")
    script.setAttribute("data-request-access", requestAccess)
    
    if (cornerRadius !== undefined) {
      script.setAttribute("data-radius", cornerRadius.toString())
    }
    if (!usePic) {
      script.setAttribute("data-userpic", "false")
    }
    if (lang) {
      script.setAttribute("data-lang", lang)
    }

    // Clear container and append script
    if (containerRef.current) {
      containerRef.current.innerHTML = ""
      containerRef.current.appendChild(script)
    }

    return () => {
      // Cleanup
      if (containerRef.current) {
        containerRef.current.innerHTML = ""
      }
    }
  }, [botName, buttonSize, cornerRadius, requestAccess, usePic, lang, onAuth])

  return <div ref={containerRef} className="flex justify-center" />
}
