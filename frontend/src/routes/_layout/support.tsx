import { createFileRoute } from "@tanstack/react-router"
import { MessageSquare, Clock, CheckCircle2, Wifi, WifiOff, Headphones } from "lucide-react"

import { ChatMessages, ChatInput } from "@/components/Chat"
import { useUserChat } from "@/hooks/useChat"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

export const Route = createFileRoute("/_layout/support")({
  component: UserSupportPage,
  head: () => ({
    meta: [{ title: "Support - AzCity CRM" }],
  }),
})

function UserSupportPage() {
  const {
    isConnected,
    status,
    messages,
    isAdminTyping,
    isLoading,
    isMessagesLoading,
    startChat,
    sendMessage,
    sendTyping,
  } = useUserChat()

  const handleStartChat = async () => {
    try {
      await startChat()
    } catch (error) {
      console.error("Failed to start chat:", error)
    }
  }

  const handleSendMessage = async (content: string) => {
    try {
      await sendMessage({ content })
    } catch (error) {
      console.error("Failed to send message:", error)
    }
  }

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-10rem)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // No active chat - show landing page
  if (!status?.has_chat) {
    return (
      <div className="h-[calc(100vh-10rem)] flex items-center justify-center -mx-8 -my-8">
        <div className="max-w-md w-full mx-auto p-8 text-center">
          <div className="mb-8">
            <div className="relative mx-auto w-24 h-24 mb-6">
              <div className="absolute inset-0 bg-primary/10 rounded-full animate-pulse" />
              <div className="absolute inset-2 bg-primary/20 rounded-full" />
              <Headphones className="absolute inset-0 m-auto h-12 w-12 text-primary" />
            </div>
            <h1 className="text-3xl font-bold mb-2">Need Help?</h1>
            <p className="text-muted-foreground text-lg">
              Our support team is here to assist you with any questions or issues.
            </p>
          </div>

          <div className="space-y-4 mb-8">
            <div className="flex items-center gap-3 text-left p-4 rounded-lg bg-muted/50">
              <Clock className="h-5 w-5 text-primary shrink-0" />
              <div>
                <p className="font-medium">Quick Response</p>
                <p className="text-sm text-muted-foreground">Average response time under 5 minutes</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-left p-4 rounded-lg bg-muted/50">
              <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
              <div>
                <p className="font-medium">Expert Support</p>
                <p className="text-sm text-muted-foreground">Get help from our experienced team</p>
              </div>
            </div>
          </div>

          <Button
            onClick={handleStartChat}
            size="lg"
            className="w-full gap-2 h-12 text-lg"
          >
            <MessageSquare className="h-5 w-5" />
            Start a Conversation
          </Button>

          <p className="text-xs text-muted-foreground mt-4">
            By starting a chat, you agree to our terms of service
          </p>
        </div>
      </div>
    )
  }

  // Chat is pending - show waiting page
  if (status.status === "pending" && !status.admin_assigned) {
    return (
      <div className="h-[calc(100vh-10rem)] flex flex-col -mx-8 -my-8">
        {/* Header */}
        <div className="h-16 border-b flex items-center justify-between px-4 bg-background">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Avatar className="h-10 w-10">
                <AvatarImage src="/assets/images/support-avatar.png" />
                <AvatarFallback className="bg-primary/10 text-primary">
                  <Headphones className="h-5 w-5" />
                </AvatarFallback>
              </Avatar>
              <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-yellow-500 border-2 border-background" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">Support Team</h3>
              <p className="text-xs text-yellow-500">Finding available agent...</p>
            </div>
          </div>
          <Badge variant={isConnected ? "default" : "destructive"} className="gap-1">
            {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {isConnected ? "Connected" : "Offline"}
          </Badge>
        </div>

        {/* Messages area */}
        {isMessagesLoading ? (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            Loading messages...
          </div>
        ) : (
          <ChatMessages
            messages={messages}
            isAdminView={false}
            userName="Support"
            isTyping={false}
          />
        )}

        {/* Waiting indicator */}
        <div className="border-t bg-background p-6">
          <div className="flex flex-col items-center text-center">
            <div className="relative mb-4">
              <div className="h-16 w-16 rounded-full border-4 border-muted flex items-center justify-center">
                <Clock className="h-8 w-8 text-primary animate-pulse" />
              </div>
            </div>
            <h3 className="font-semibold mb-1">Waiting for Support</h3>
            <p className="text-sm text-muted-foreground mb-4">
              An agent will be with you shortly. You can start typing your message below.
            </p>
          </div>
          
          <ChatInput
            onSendMessage={handleSendMessage}
            onTyping={sendTyping}
            placeholder="Type your message while waiting..."
          />
        </div>
      </div>
    )
  }

  // Active chat
  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col -mx-8 -my-8">
      {/* Header */}
      <div className="h-16 border-b flex items-center justify-between px-4 bg-background">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Avatar className="h-10 w-10">
              <AvatarImage src="/assets/images/support-avatar.png" />
              <AvatarFallback className="bg-primary/10 text-primary">
                <Headphones className="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-green-500 border-2 border-background" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Support Team</h3>
            <p className="text-xs text-muted-foreground">
              {isAdminTyping ? (
                <span className="text-primary">typing...</span>
              ) : (
                <span className="text-green-500">Online</span>
              )}
            </p>
          </div>
        </div>
        <Badge variant={isConnected ? "default" : "destructive"} className="gap-1">
          {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
          {isConnected ? "Connected" : "Offline"}
        </Badge>
      </div>

      {/* Messages */}
      {isMessagesLoading ? (
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          Loading messages...
        </div>
      ) : (
        <ChatMessages
          messages={messages}
          isAdminView={false}
          userName="Support"
          isTyping={isAdminTyping}
        />
      )}

      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        onTyping={sendTyping}
        placeholder="Type a message..."
      />
    </div>
  )
}

export default UserSupportPage
