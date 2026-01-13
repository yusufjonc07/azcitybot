import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useState } from "react"
import { useWebSocket, type WebSocketMessage } from "./useWebSocket"

const API_BASE = import.meta.env.VITE_API_URL

// Types
export interface ChatUser {
  id: string
  telegram_id: number
  full_name: string | null
  username: string | null
  photo_url: string | null
}

export interface ChatMessage {
  id: string
  support_chat_id: string
  sender_id: string | null
  content: string
  message_type: string
  file_url: string | null
  file_name: string | null
  is_from_user: boolean
  is_read: boolean
  created_at: string
}

export interface SupportChat {
  id: string
  status: string
  created_at: string
  updated_at: string | null
  claimed_at: string | null
  user_id: string
  admin_id: string | null
  user_telegram_id: number
  user_full_name: string | null
  user_username: string | null
  user_photo_url: string | null
  last_message: string | null
  last_message_time: string | null
  unread_count: number
}

export interface ChatStatus {
  has_chat: boolean
  status: string | null
  chat_id: string | null
  admin_assigned?: boolean
}

// API functions
async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem("access_token") || ""
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }
  
  return response.json()
}

// User hooks
export function useMyChatStatus() {
  return useQuery<ChatStatus>({
    queryKey: ["chat", "my-status"],
    queryFn: () => fetchWithAuth("/chat/my-status"),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useMyMessages() {
  return useQuery<{ data: ChatMessage[]; count: number }>({
    queryKey: ["chat", "my-messages"],
    queryFn: () => fetchWithAuth("/chat/my-messages"),
  })
}

export function useStartChat() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => fetchWithAuth("/chat/start", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat"] })
    },
  })
}

export function useSendUserMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ content, messageType = "text" }: { content: string; messageType?: string }) =>
      fetchWithAuth(`/chat/my-messages/send?content=${encodeURIComponent(content)}&message_type=${messageType}`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", "my-messages"] })
    },
  })
}

// Admin hooks
export function usePendingChats() {
  return useQuery<{ data: SupportChat[]; count: number }>({
    queryKey: ["chat", "pending"],
    queryFn: () => fetchWithAuth("/chat/pending"),
  })
}

export function useActiveChats() {
  return useQuery<{ data: SupportChat[]; count: number }>({
    queryKey: ["chat", "active"],
    queryFn: () => fetchWithAuth("/chat/active"),
  })
}

export function useChatMessages(chatId: string | null) {
  return useQuery<{ data: ChatMessage[]; count: number }>({
    queryKey: ["chat", "messages", chatId],
    queryFn: () => fetchWithAuth(`/chat/${chatId}/messages`),
    enabled: !!chatId,
  })
}

export function useClaimChat() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (chatId: string) =>
      fetchWithAuth(`/chat/${chatId}/claim`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat"] })
    },
  })
}

export function useCloseChat() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ chatId, cancelled = false }: { chatId: string; cancelled?: boolean }) =>
      fetchWithAuth(`/chat/${chatId}/close?cancelled=${cancelled}`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat"] })
    },
  })
}

export function useSendAdminMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ chatId, content, messageType = "text" }: { chatId: string; content: string; messageType?: string }) =>
      fetchWithAuth(`/chat/${chatId}/messages/send?content=${encodeURIComponent(content)}&message_type=${messageType}`, {
        method: "POST",
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["chat", "messages", variables.chatId] })
    },
  })
}

export function useMarkMessagesRead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (chatId: string) =>
      fetchWithAuth(`/chat/${chatId}/messages/read`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat"] })
    },
  })
}

// Combined hook for admin chat with WebSocket
export function useAdminChat() {
  const queryClient = useQueryClient()
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set())
  
  const token = localStorage.getItem("access_token") || ""
  const wsUrl = API_BASE.replace("http", "ws").replace("/api/v1", "") + "/api/v1/ws/admin"
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case "new_pending_chat":
      case "chat_claimed":
        queryClient.invalidateQueries({ queryKey: ["chat", "pending"] })
        queryClient.invalidateQueries({ queryKey: ["chat", "active"] })
        break
      
      case "new_message":
      case "pending_chat_update":
        queryClient.invalidateQueries({ queryKey: ["chat", "messages", message.chat_id] })
        queryClient.invalidateQueries({ queryKey: ["chat", "pending"] })
        queryClient.invalidateQueries({ queryKey: ["chat", "active"] })
        break
      
      case "user_typing":
        setTypingUsers((prev) => {
          const next = new Set(prev)
          next.add(message.user_id)
          return next
        })
        // Clear typing indicator after 3 seconds
        setTimeout(() => {
          setTypingUsers((prev) => {
            const next = new Set(prev)
            next.delete(message.user_id)
            return next
          })
        }, 3000)
        break
    }
  }, [queryClient])
  
  const { isConnected, sendTyping } = useWebSocket({
    url: wsUrl,
    token,
    onMessage: handleMessage,
  })
  
  const pendingChats = usePendingChats()
  const activeChats = useActiveChats()
  const messages = useChatMessages(selectedChatId)
  const claimChat = useClaimChat()
  const closeChat = useCloseChat()
  const sendMessage = useSendAdminMessage()
  const markRead = useMarkMessagesRead()
  
  // Mark messages as read when selecting a chat
  useEffect(() => {
    if (selectedChatId) {
      markRead.mutate(selectedChatId)
    }
  }, [selectedChatId])
  
  return {
    isConnected,
    selectedChatId,
    setSelectedChatId,
    pendingChats: pendingChats.data?.data || [],
    activeChats: activeChats.data?.data || [],
    messages: messages.data?.data || [],
    typingUsers,
    isLoading: pendingChats.isLoading || activeChats.isLoading,
    isMessagesLoading: messages.isLoading,
    claimChat: claimChat.mutateAsync,
    closeChat: closeChat.mutateAsync,
    sendMessage: sendMessage.mutateAsync,
    sendTyping: (userId: string) => sendTyping(selectedChatId || undefined, userId),
    refetch: () => {
      pendingChats.refetch()
      activeChats.refetch()
    },
  }
}

// Combined hook for user chat with WebSocket
export function useUserChat() {
  const queryClient = useQueryClient()
  const [isAdminTyping, setIsAdminTyping] = useState(false)
  
  const token = localStorage.getItem("access_token") || ""
  const wsUrl = API_BASE.replace("http", "ws").replace("/api/v1", "") + "/api/v1/ws/user"
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case "new_message":
        queryClient.invalidateQueries({ queryKey: ["chat", "my-messages"] })
        break
      
      case "admin_joined":
        queryClient.invalidateQueries({ queryKey: ["chat", "my-status"] })
        break
      
      case "chat_closed":
        queryClient.invalidateQueries({ queryKey: ["chat"] })
        break
      
      case "admin_typing":
        setIsAdminTyping(true)
        setTimeout(() => setIsAdminTyping(false), 3000)
        break
      
      case "messages_read":
        queryClient.invalidateQueries({ queryKey: ["chat", "my-messages"] })
        break
    }
  }, [queryClient])
  
  const { isConnected, sendTyping } = useWebSocket({
    url: wsUrl,
    token,
    onMessage: handleMessage,
  })
  
  const status = useMyChatStatus()
  const messages = useMyMessages()
  const startChat = useStartChat()
  const sendMessage = useSendUserMessage()
  
  return {
    isConnected,
    status: status.data,
    messages: messages.data?.data || [],
    isAdminTyping,
    isLoading: status.isLoading,
    isMessagesLoading: messages.isLoading,
    startChat: startChat.mutateAsync,
    sendMessage: sendMessage.mutateAsync,
    sendTyping: () => sendTyping(),
    refetch: () => {
      status.refetch()
      messages.refetch()
    },
  }
}
