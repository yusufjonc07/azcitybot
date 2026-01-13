import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import type { SupportChat } from "@/hooks/useChat"

interface ChatUserListProps {
  title: string
  chats: SupportChat[]
  selectedChatId: string | null
  onSelectChat: (chatId: string) => void
  emptyMessage?: string
  showBadge?: boolean
}

export function ChatUserList({
  title,
  chats,
  selectedChatId,
  onSelectChat,
  emptyMessage = "No chats",
  showBadge = false,
}: ChatUserListProps) {
  const getInitials = (name: string | null, username: string | null) => {
    if (name) {
      return name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    }
    if (username) {
      return username.slice(0, 2).toUpperCase()
    }
    return "?"
  }

  const formatTime = (dateString: string | null) => {
    if (!dateString) return ""
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
    if (days === 1) {
      return "Yesterday"
    }
    if (days < 7) {
      return date.toLocaleDateString([], { weekday: "short" })
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" })
  }

  return (
    <div className="flex flex-col">
      <h3 className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        {title}
        {showBadge && chats.length > 0 && (
          <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-primary rounded-full">
            {chats.length}
          </span>
        )}
      </h3>
      {chats.length === 0 ? (
        <p className="px-3 py-4 text-sm text-muted-foreground text-center">{emptyMessage}</p>
      ) : (
        <div className="space-y-1 px-2">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => onSelectChat(chat.id)}
              className={cn(
                "w-full flex items-center gap-3 p-2 rounded-lg transition-colors text-left",
                "hover:bg-accent",
                selectedChatId === chat.id && "bg-accent"
              )}
            >
              <div className="relative">
                <Avatar className="h-12 w-12 border-2 border-background">
                  <AvatarImage src={chat.user_photo_url || undefined} />
                  <AvatarFallback className="bg-primary/10 text-primary font-medium">
                    {getInitials(chat.user_full_name, chat.user_username)}
                  </AvatarFallback>
                </Avatar>
                {chat.unread_count > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                    {chat.unread_count > 9 ? "9+" : chat.unread_count}
                  </span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-medium truncate">
                    {chat.user_full_name || (chat.user_username ? `@${chat.user_username}` : "User")}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatTime(chat.last_message_time || chat.created_at)}
                  </span>
                </div>
                {chat.last_message && (
                  <p className="text-sm text-muted-foreground truncate mt-0.5">
                    {chat.last_message}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
