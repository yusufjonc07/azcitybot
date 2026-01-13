import { createFileRoute } from "@tanstack/react-router"
import { useState, useMemo } from "react"
import { MessageSquare, Users, Clock, Wifi, WifiOff } from "lucide-react"

import { ChatUserList, ChatMessages, ChatInput, ChatHeader } from "@/components/Chat"
import { useAdminChat } from "@/hooks/useChat"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"

export const Route = createFileRoute("/_layout/chat")({
  component: AdminChatPage,
  head: () => ({
    meta: [{ title: "Chat - AzCity CRM" }],
  }),
})

function AdminChatPage() {
  const [activeTab, setActiveTab] = useState<"pending" | "active">("pending")
  
  const {
    isConnected,
    selectedChatId,
    setSelectedChatId,
    pendingChats,
    activeChats,
    messages,
    typingUsers,
    isLoading,
    isMessagesLoading,
    claimChat,
    closeChat,
    sendMessage,
    sendTyping,
  } = useAdminChat()

  // Find selected chat
  const selectedChat = useMemo(() => {
    return [...pendingChats, ...activeChats].find((chat) => chat.id === selectedChatId) || null
  }, [pendingChats, activeChats, selectedChatId])

  const handleSendMessage = async (content: string) => {
    if (!selectedChatId) return
    
    try {
      await sendMessage({ chatId: selectedChatId, content })
    } catch (error) {
      console.error("Failed to send message:", error)
    }
  }

  const handleClaimChat = async () => {
    if (!selectedChatId) return
    
    try {
      await claimChat(selectedChatId)
    } catch (error) {
      console.error("Failed to claim chat:", error)
    }
  }

  const handleCloseChat = async (cancelled: boolean = false) => {
    if (!selectedChatId) return
    
    try {
      await closeChat({ chatId: selectedChatId, cancelled })
      setSelectedChatId(null)
    } catch (error) {
      console.error("Failed to close chat:", error)
    }
  }

  const isUserTyping = selectedChat ? typingUsers.has(selectedChat.user_id) : false
  const canSendMessage = selectedChat?.status === "active" && selectedChat.admin_id != null

  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col -mx-8 -my-8 md:-mx-8 md:-my-8">
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar - Chat list */}
        <div className="w-80 border-r flex flex-col bg-background">
          {/* Connection status */}
          <div className="p-3 border-b flex items-center justify-between">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              Support Chats
            </h2>
            <Badge variant={isConnected ? "default" : "destructive"} className="gap-1">
              {isConnected ? (
                <>
                  <Wifi className="h-3 w-3" />
                  Live
                </>
              ) : (
                <>
                  <WifiOff className="h-3 w-3" />
                  Offline
                </>
              )}
            </Badge>
          </div>

          {/* Tabs for pending/active */}
          <div className="p-2 border-b">
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "pending" | "active")}>
              <TabsList className="w-full">
                <TabsTrigger value="pending" className="flex-1 gap-1">
                  <Clock className="h-4 w-4" />
                  Pending
                  {pendingChats.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5">
                      {pendingChats.length}
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="active" className="flex-1 gap-1">
                  <Users className="h-4 w-4" />
                  Active
                  {activeChats.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5">
                      {activeChats.length}
                    </Badge>
                  )}
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Chat list */}
          <ScrollArea className="flex-1">
            {isLoading ? (
              <div className="p-4 text-center text-muted-foreground">Loading...</div>
            ) : activeTab === "pending" ? (
              <ChatUserList
                title=""
                chats={pendingChats}
                selectedChatId={selectedChatId}
                onSelectChat={setSelectedChatId}
                emptyMessage="No pending chats"
                showBadge={false}
              />
            ) : (
              <ChatUserList
                title=""
                chats={activeChats}
                selectedChatId={selectedChatId}
                onSelectChat={setSelectedChatId}
                emptyMessage="No active chats"
                showBadge={false}
              />
            )}
          </ScrollArea>
        </div>

        {/* Right side - Chat area */}
        <div className="flex-1 flex flex-col bg-muted/30">
          {selectedChat ? (
            <>
              {/* Chat header */}
              <ChatHeader
                chat={selectedChat}
                isTyping={isUserTyping}
                onClose={() => setSelectedChatId(null)}
                onCloseChat={handleCloseChat}
                onClaim={handleClaimChat}
                showClaimButton={selectedChat.status === "pending"}
              />

              {/* Messages area */}
              {isMessagesLoading ? (
                <div className="flex-1 flex items-center justify-center text-muted-foreground">
                  Loading messages...
                </div>
              ) : (
                <ChatMessages
                  messages={messages}
                  isAdminView={true}
                  userPhoto={selectedChat.user_photo_url}
                  userName={selectedChat.user_full_name || selectedChat.user_username}
                  isTyping={isUserTyping}
                />
              )}

              {/* Input area */}
              <ChatInput
                onSendMessage={handleSendMessage}
                onTyping={() => sendTyping(selectedChat.user_id)}
                disabled={!canSendMessage}
                placeholder={
                  !canSendMessage
                    ? "Claim this chat to send messages"
                    : "Type a message..."
                }
              />
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
              <MessageSquare className="h-16 w-16 mb-4 opacity-20" />
              <h3 className="text-lg font-medium">No chat selected</h3>
              <p className="text-sm">Select a chat from the list to start messaging</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminChatPage
