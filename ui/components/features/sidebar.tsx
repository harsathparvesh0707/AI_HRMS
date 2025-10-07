"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Plus, Search, History, Clock, User, Building2 } from "lucide-react"

interface ChatHistoryItem {
  id: string
  title: string
  messages: any[]
  timestamp: Date
}

interface SidebarProps {
  onNewChat: () => void
  chatHistory: ChatHistoryItem[]
  onLoadChat: (chatId: string) => void
}

export function Sidebar({ onNewChat, chatHistory, onLoadChat }: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [activeSection, setActiveSection] = useState<"history" | "search">("history")

  const filteredHistory = chatHistory.filter((chat) => chat.title.toLowerCase().includes(searchQuery.toLowerCase()))

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date()
    const diff = now.getTime() - timestamp.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)

    if (hours < 1) return "Just now"
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return timestamp.toLocaleDateString()
  }

  return (
    <div className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-sidebar-primary rounded-lg flex items-center justify-center">
            <Building2 className="w-5 h-5 text-sidebar-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-sidebar-foreground">HR Assistant</h1>
            <p className="text-sm text-sidebar-foreground/70">Your AI-powered HR companion</p>
          </div>
        </div>

        {/* New Chat Button */}
        <Button
          onClick={onNewChat}
          className="w-full bg-sidebar-primary hover:bg-sidebar-primary/90 text-sidebar-primary-foreground"
          size="lg"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Navigation Tabs */}
      <div className="px-6 py-4">
        <div className="flex gap-2">
          <Button
            variant={activeSection === "history" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveSection("history")}
            className="flex-1"
          >
            <History className="w-4 h-4 mr-2" />
            History
          </Button>
          <Button
            variant={activeSection === "search" ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveSection("search")}
            className="flex-1"
          >
            <Search className="w-4 h-4 mr-2" />
            Search
          </Button>
        </div>
      </div>

      {/* Search Input */}
      {activeSection === "search" && (
        <div className="px-6 pb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-sidebar-foreground/50" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-sidebar-accent border-sidebar-border"
            />
          </div>
        </div>
      )}

      <Separator className="bg-sidebar-border" />

      {/* Chat History */}
      <ScrollArea className="flex-1 px-6">
        <div className="py-4 space-y-2">
          {activeSection === "history" && (
            <>
              <h3 className="text-sm font-medium text-sidebar-foreground/70 mb-3">Recent Conversations</h3>
              {chatHistory.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-sidebar-foreground/30 mx-auto mb-3" />
                  <p className="text-sm text-sidebar-foreground/50">No conversations yet</p>
                  <p className="text-xs text-sidebar-foreground/40 mt-1">Start a new chat to begin</p>
                </div>
              ) : (
                chatHistory.map((chat) => (
                  <div
                    key={chat.id}
                    onClick={() => onLoadChat(chat.id)}
                    className="p-3 rounded-lg bg-sidebar-accent cursor-pointer transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-sidebar-foreground truncate">
                          {chat.title}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Clock className="w-3 h-3 text-sidebar-foreground/50" />
                          <span className="text-xs text-sidebar-foreground/50">{formatTimestamp(chat.timestamp)}</span>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {chat.messages.length}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </>
          )}

          {activeSection === "search" && (
            <>
              <h3 className="text-sm font-medium text-sidebar-foreground/70 mb-3">
                Search Results {searchQuery && `(${filteredHistory.length})`}
              </h3>
              {searchQuery === "" ? (
                <div className="text-center py-8">
                  <Search className="w-12 h-12 text-sidebar-foreground/30 mx-auto mb-3" />
                  <p className="text-sm text-sidebar-foreground/50">Enter a search term</p>
                  <p className="text-xs text-sidebar-foreground/40 mt-1">Find your past conversations</p>
                </div>
              ) : filteredHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Search className="w-12 h-12 text-sidebar-foreground/30 mx-auto mb-3" />
                  <p className="text-sm text-sidebar-foreground/50">No results found</p>
                  <p className="text-xs text-sidebar-foreground/40 mt-1">Try a different search term</p>
                </div>
              ) : (
                filteredHistory.map((chat) => (
                  <div
                    key={chat.id}
                    onClick={() => onLoadChat(chat.id)}
                    className="p-3 rounded-lg bg-sidebar-accent cursor-pointer transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-sidebar-foreground truncate">
                          {chat.title}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Clock className="w-3 h-3 text-sidebar-foreground/50" />
                          <span className="text-xs text-sidebar-foreground/50">{formatTimestamp(chat.timestamp)}</span>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {chat.messages.length}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </>
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-6 border-t border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-sidebar-primary rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-sidebar-primary-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-sidebar-foreground">John Doe</p>
            <p className="text-xs text-sidebar-foreground/70 truncate">Software Engineer</p>
          </div>
        </div>
      </div>
    </div>
  )
}
