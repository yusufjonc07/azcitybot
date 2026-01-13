import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Check, CheckCheck } from "lucide-react"
import type { ChatMessage } from "@/hooks/useChat"

interface ChatMessagesProps {
  messages: ChatMessage[]
  isAdminView?: boolean
  userPhoto?: string | null
  userName?: string | null
  isTyping?: boolean
}

export function ChatMessages({
  messages,
  isAdminView = false,
  userPhoto,
  userName,
  isTyping = false,
}: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return "Today"
    }
    if (date.toDateString() === yesterday.toDateString()) {
      return "Yesterday"
    }
    return date.toLocaleDateString([], {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const getInitials = (name: string | null | undefined) => {
    if (!name) return "?"
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const isOwnMessage = (message: ChatMessage) => {
    if (isAdminView) {
      return !message.is_from_user
    }
    return message.is_from_user
  }

  // Group messages by date
  const groupedMessages: { date: string; messages: ChatMessage[] }[] = []
  let currentDate = ""

  messages.forEach((message) => {
    const messageDate = new Date(message.created_at).toDateString()
    if (messageDate !== currentDate) {
      currentDate = messageDate
      groupedMessages.push({ date: message.created_at, messages: [message] })
    } else {
      groupedMessages[groupedMessages.length - 1].messages.push(message)
    }
  })

  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <p>No messages yet. Start the conversation!</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {groupedMessages.map((group, groupIndex) => (
        <div key={groupIndex}>
          {/* Date separator */}
          <div className="flex justify-center mb-4">
            <span className="bg-muted px-3 py-1 rounded-full text-xs text-muted-foreground">
              {formatDate(group.date)}
            </span>
          </div>

          {/* Messages for this date */}
          <div className="space-y-2">
            {group.messages.map((message, messageIndex) => {
              const own = isOwnMessage(message)
              const showAvatar =
                !own &&
                (messageIndex === 0 ||
                  isOwnMessage(group.messages[messageIndex - 1]) !== isOwnMessage(message))

              return (
                <div
                  key={message.id}
                  className={cn(
                    "flex items-end gap-2",
                    own ? "justify-end" : "justify-start"
                  )}
                >
                  {/* Avatar for other user's messages */}
                  {!own && (
                    <div className="w-8 h-8 shrink-0">
                      {showAvatar && (
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={userPhoto || undefined} />
                          <AvatarFallback className="text-xs bg-primary/10 text-primary">
                            {getInitials(userName)}
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  )}

                  {/* Message bubble - Telegram style */}
                  <div
                    className={cn(
                      "max-w-[70%] rounded-2xl px-4 py-2 relative",
                      own
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-muted rounded-bl-md"
                    )}
                  >
                    <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                      {message.content}
                    </p>
                    <div
                      className={cn(
                        "flex items-center gap-1 mt-1",
                        own ? "justify-end" : "justify-start"
                      )}
                    >
                      <span
                        className={cn(
                          "text-[10px]",
                          own ? "text-primary-foreground/70" : "text-muted-foreground"
                        )}
                      >
                        {formatTime(message.created_at)}
                      </span>
                      {own && (
                        <span className="text-primary-foreground/70">
                          {message.is_read ? (
                            <CheckCheck className="h-3 w-3" />
                          ) : (
                            <Check className="h-3 w-3" />
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {/* Typing indicator */}
      {isTyping && (
        <div className="flex items-end gap-2 justify-start">
          <Avatar className="h-8 w-8">
            <AvatarImage src={userPhoto || undefined} />
            <AvatarFallback className="text-xs bg-primary/10 text-primary">
              {getInitials(userName)}
            </AvatarFallback>
          </Avatar>
          <div className="bg-muted rounded-2xl rounded-bl-md px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
