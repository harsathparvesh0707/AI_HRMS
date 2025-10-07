"use client"

import { useState } from "react"
import HRAssistantChat from "@/components/hr-assistant-chat"
import EmployeeDisplay from "@/components/employee-display"
import { Button } from "@/components/ui/button"
import { Users, MessageCircle } from "lucide-react"

export default function HRDashboard() {
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [isMobileChatOpen, setIsMobileChatOpen] = useState(false)
  const [focusSection, setFocusSection] = useState("overview")
  const [projectMatches, setProjectMatches] = useState(null)

  const handleEmployeeData = (employeeData, section = "overview", matches = null) => {
    console.log("[v0] Received employee data:", employeeData)
    console.log("[v0] Focus section:", section)
    console.log("[v0] Project matches:", matches)

    if (matches && matches.length > 0) {
      // Project matching results
      setProjectMatches(matches)
      setSelectedEmployee(null)
      setFocusSection("overview")
    } else if (employeeData && typeof employeeData === "object") {
      // Individual employee data
      setSelectedEmployee(employeeData)
      setFocusSection(section)
      setProjectMatches(null)
    }
  }

  const handleSendMessage = (message) => {
    console.log("[v0] Sending message:", message)
    // Message handling is done in the chat component
  }

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
        <div className="flex h-16 items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground">
              <Users className="h-4 w-4" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-balance">HR Management System</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">Employee Information & Analytics</p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            className="lg:hidden bg-transparent"
            onClick={() => setIsMobileChatOpen(!isMobileChatOpen)}
          >
            <MessageCircle className="h-4 w-4" />
            <span className="sr-only">Toggle chat</span>
          </Button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-4rem)] relative">
        <div className="flex-1 overflow-auto">
          <EmployeeDisplay employee={selectedEmployee} focusSection={focusSection} projectMatches={projectMatches} />
        </div>

        <div
          className={`
          fixed inset-y-16 right-0 z-30 w-full max-w-sm transition-smooth lg:relative lg:inset-y-0 lg:z-auto lg:w-96
          ${isMobileChatOpen ? "translate-x-0" : "translate-x-full lg:translate-x-0"}
        `}
        >
          <HRAssistantChat
            isOpen={true}
            onClose={() => setIsMobileChatOpen(false)}
            onEmployeeData={handleEmployeeData}
            onSendMessage={handleSendMessage}
            isMobile={isMobileChatOpen}
          />
        </div>

        {isMobileChatOpen && (
          <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setIsMobileChatOpen(false)} />
        )}
      </div>
    </div>
  )
}
