import { useCallback, useEffect, useRef, useState } from "react"

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface UseWebSocketOptions {
  url: string
  token: string
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectAttempts?: number
  reconnectInterval?: number
}

export function useWebSocket({
  url,
  token,
  onMessage,
  onOpen,
  onClose,
  onError,
  reconnectAttempts = 5,
  reconnectInterval = 3000,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const wsUrl = `${url}?token=${token}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
      reconnectCountRef.current = 0
      onOpen?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage
        setLastMessage(data)
        onMessage?.(data)
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      onClose?.()

      // Attempt to reconnect
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current++
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, reconnectInterval)
      }
    }

    ws.onerror = (error) => {
      onError?.(error)
    }

    wsRef.current = ws
  }, [url, token, onMessage, onOpen, onClose, onError, reconnectAttempts, reconnectInterval])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    reconnectCountRef.current = reconnectAttempts // Prevent reconnection
    wsRef.current?.close()
  }, [reconnectAttempts])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const sendPing = useCallback(() => {
    sendMessage({ type: "ping" })
  }, [sendMessage])

  const sendTyping = useCallback((chatId?: string, userId?: string) => {
    sendMessage({ type: "typing", chat_id: chatId, user_id: userId })
  }, [sendMessage])

  useEffect(() => {
    connect()

    // Ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(sendPing, 30000)

    return () => {
      clearInterval(pingInterval)
      disconnect()
    }
  }, [connect, disconnect, sendPing])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    sendTyping,
    connect,
    disconnect,
  }
}
