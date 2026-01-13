import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Phone, Video, MoreVertical, X, UserPlus } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { SupportChat } from "@/hooks/useChat"

interface ChatHeaderProps {
  chat: SupportChat | null
  isTyping?: boolean
  onClose?: () => void
  onCloseChat?: (cancelled?: boolean) => void
  onClaim?: () => void
  showClaimButton?: boolean
}

export function ChatHeader({
  chat,
  isTyping = false,
  onClose,
  onCloseChat,
  onClaim,
  showClaimButton = false,
}: ChatHeaderProps) {
  if (!chat) {
    return (
      <div className="h-16 border-b flex items-center justify-center text-muted-foreground">
        Select a chat to start messaging
      </div>
    )
  }

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

  const displayName = chat.user_full_name || (chat.user_username ? `@${chat.user_username}` : "User")

  return (
    <div className="h-16 border-b flex items-center justify-between px-4 bg-background">
      <div className="flex items-center gap-3">
        <Avatar className="h-10 w-10">
          <AvatarImage src={chat.user_photo_url || undefined} />
          <AvatarFallback className="bg-primary/10 text-primary font-medium">
            {getInitials(chat.user_full_name, chat.user_username)}
          </AvatarFallback>
        </Avatar>
        <div>
          <h3 className="font-semibold text-sm">{displayName}</h3>
          <p className="text-xs text-muted-foreground">
            {isTyping ? (
              <span className="text-primary">typing...</span>
            ) : chat.status === "pending" ? (
              <span className="text-yellow-500">Waiting for support</span>
            ) : (
              <span className="text-green-500">Active chat</span>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {showClaimButton && chat.status === "pending" && (
          <Button
            variant="default"
            size="sm"
            onClick={onClaim}
            className="mr-2"
          >
            <UserPlus className="h-4 w-4 mr-1" />
            Claim Chat
          </Button>
        )}

        <Button variant="ghost" size="icon" className="text-muted-foreground">
          <Phone className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" className="text-muted-foreground">
          <Video className="h-5 w-5" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="text-muted-foreground">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>View Profile</DropdownMenuItem>
            <DropdownMenuItem>Search in Chat</DropdownMenuItem>
            <DropdownMenuSeparator />
            {onCloseChat && chat.status === "active" && (
              <>
                <DropdownMenuItem onClick={() => onCloseChat(false)}>
                  Close Chat
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => onCloseChat(true)}
                  className="text-destructive"
                >
                  Cancel Chat
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {onClose && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-muted-foreground ml-2"
          >
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>
    </div>
  )
}
