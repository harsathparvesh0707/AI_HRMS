"use client"

import { useState, useEffect } from "react"
import HRAssistantChat from "@/components/features/hr-assistant-chat"
import EmployeeDisplay from "@/components/features/employee-display"
import ContentContainer from "@/components/features/ContentContainer"
import { Button } from "@/components/ui/button"
import { Bell, LogOut,User } from "lucide-react"
import { Users, MessageCircle } from "lucide-react"
import Login from "@/components/common/Login"

export default function HRDashboard() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [showDashboard, setShowDashboard] = useState(false) // For fade
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [isMobileChatOpen, setIsMobileChatOpen] = useState(false)
  const [focusSection, setFocusSection] = useState("overview")
  const [projectMatches, setProjectMatches] = useState(null)

  // Check login state on mount
  useEffect(() => {
    const savedLoginState = localStorage.getItem('isLoggedIn')
    if (savedLoginState === 'true') {
      setIsLoggedIn(true)
    }
  }, [])

  const handleEmployeeData = (employeeData, section = "overview", matches = null) => {
    if (matches && matches.length > 0) {
      setProjectMatches(matches)
      setSelectedEmployee(null)
      setFocusSection("overview")
    } else if (employeeData && typeof employeeData === "object") {
      setSelectedEmployee(employeeData)
      setFocusSection(section)
      setProjectMatches(null)
    }
  }

  const handleSendMessage = (message) => {
    console.log("[v0] Sending message:", message)
  }

  // Trigger fade-in after login
  useEffect(() => {
    if (isLoggedIn) {
      localStorage.setItem('isLoggedIn', 'true')
      const timeout = setTimeout(() => setShowDashboard(true), 100) // slight delay
      return () => clearTimeout(timeout)
    }
  }, [isLoggedIn])

  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />
  }

  // Dashboard with fade transition
  return (
    <div
      className={`h-screen w-screen transition-opacity overflow-hidden duration-700 ease-in-out ${
        showDashboard ? "opacity-100" : "opacity-0"
      }`}
    >
     <header className="sticky top-0 z-40 border-b bg-indigo-200">
  <div className="flex h-16 items-center justify-between px-4 lg:px-6">
    {/* Left side: Logo and Title */}
    <div className="flex items-center gap-3">
      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-500/50 text-primary-foreground">
        <Users className="h-4 w-4" />
      </div>
      <div>
        <h1 className="text-xl font-bold text-balance">HR Management System</h1>
        <p className="text-xs text-muted-foreground hidden sm:block">
          Employee Information & Analytics
        </p>
      </div>
    </div>

    {/* Right side: Mobile Chat Toggle + User Profile */}
    <div className="flex items-center gap-4">
      {/* Mobile Chat Toggle */}
      <Button
        variant="outline"
        size="sm"
        className="lg:hidden bg-transparent"
        onClick={() => setIsMobileChatOpen(!isMobileChatOpen)}
      >
        <MessageCircle className="h-4 w-4" />
        <span className="sr-only">Toggle chat</span>
      </Button>

      {/* Notifications */}
     <button className="relative p-2 rounded-full hover:bg-indigo-300/50 transition">
  <span className="sr-only">Notifications</span>
  <Bell className="h-5 w-5 text-gray-700" />
  {/* <span className="absolute top-0 right-0 block h-2 w-2"></span> */}
</button>
 <button className="flex items-center justify-center p-2 rounded-full hover:bg-indigo-300/50 transition">
    <span className="sr-only">User Profile</span>
    <User className="h-5 w-5 text-gray-700" />
  </button>
 <button
  className="flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-gray-700 rounded-full hover:bg-indigo-300/50 transition"
  onClick={() => {
    localStorage.removeItem('isLoggedIn'); // clear from localStorage
    setIsLoggedIn(false);   // reset login state
    setShowDashboard(false); // hide dashboard with fade effect
  }}
> 
  <LogOut className="h-5 w-5" />

</button>
      {/* User Profile */}
      <div className="relative">
        {/* <button className="flex items-center gap-2 rounded-full hover:bg-indigo-300/50 p-2 transition">
          <img
            src="/profile.jpg" // Replace with dynamic user image if available
            alt="User"
            className="h-6 w-6 rounded-full object-cover"
          />
          <span className="hidden sm:block font-medium text-sm">John Doe</span>
        </button> */}
        {/* Dropdown menu */}
        <div className="absolute right-0 mt-2 w-40 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 hidden group-hover:block">
          {/* <button
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            onClick={() => console.log("Profile clicked")}
          >
            Profile
          </button> */}
    
        </div>
      </div>
    </div>
  </div>
</header>


      <div className="flex h-[calc(100vh-4rem)] relative">
        <ContentContainer />

        <div
          className={`
            fixed inset-y-16 right-0 z-50 w-full max-w-sm transition-smooth lg:relative lg:inset-y-0 lg:z-auto lg:w-96
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
          <div
            className="fixed inset-0 bg-black/50 z-20 lg:hidden"
            onClick={() => setIsMobileChatOpen(false)}
          />
        )}
      </div>
    </div>
  )
}

