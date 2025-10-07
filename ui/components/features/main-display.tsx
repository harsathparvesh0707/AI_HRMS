  "use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  User,
  Calendar,
  Clock,
  TrendingUp,
  MessageSquare,
  Send,
  CheckCircle,
  XCircle,
  AlertCircle,
  Award,
  Users,
} from "lucide-react"

interface MainDisplayProps {
  currentView: "dashboard" | "profile" | "attendance" | "leave" | "performance"
  onSendMessage: (message: string) => void
  isChatOpen: boolean
}

export function MainDisplay({ currentView, onSendMessage, isChatOpen }: MainDisplayProps) {
  const [quickMessage, setQuickMessage] = useState("")

  const handleQuickMessage = (message: string) => {
    onSendMessage(message)
    setQuickMessage("")
  }

  const handleSendQuickMessage = () => {
    if (quickMessage.trim()) {
      handleQuickMessage(quickMessage)
    }
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back, John!</h1>
        <p className="text-muted-foreground">Here's your HR dashboard overview for today.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Attendance Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">95%</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Leave Balance</CardTitle>
            <Calendar className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">15</div>
            <p className="text-xs text-muted-foreground">Days remaining</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2/5</div>
            <p className="text-xs text-muted-foreground">Latest review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Next Review</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">30</div>
            <p className="text-xs text-muted-foreground">Days away</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common HR tasks and queries</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button variant="outline" onClick={() => handleQuickMessage("Show my attendance record")}>
              <Calendar className="w-4 h-4 mr-2" />
              Attendance
            </Button>
            <Button variant="outline" onClick={() => handleQuickMessage("Check my leave balance")}>
              <Clock className="w-4 h-4 mr-2" />
              Leave Balance
            </Button>
            <Button variant="outline" onClick={() => handleQuickMessage("Show my profile")}>
              <User className="w-4 h-4 mr-2" />
              My Profile
            </Button>
            <Button variant="outline" onClick={() => handleQuickMessage("Show performance review")}>
              <Award className="w-4 h-4 mr-2" />
              Performance
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest HR interactions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm font-medium">Leave request approved</p>
                <p className="text-xs text-muted-foreground">2 days ago</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <div className="flex-1">
                <p className="text-sm font-medium">Performance review scheduled</p>
                <p className="text-xs text-muted-foreground">1 week ago</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-blue-600" />
              <div className="flex-1">
                <p className="text-sm font-medium">Team meeting attended</p>
                <p className="text-xs text-muted-foreground">1 week ago</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderProfile = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Employee Profile</h1>
        <p className="text-muted-foreground">Your personal and professional information</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
                <User className="w-8 h-8 text-primary-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">John Doe</h3>
                <p className="text-muted-foreground">Software Engineer</p>
              </div>
            </div>
            <Separator />
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Employee ID:</span>
                <span className="text-sm font-medium">EMP001</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Email:</span>
                <span className="text-sm font-medium">john.doe@company.com</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Phone:</span>
                <span className="text-sm font-medium">+1 (555) 123-4567</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Join Date:</span>
                <span className="text-sm font-medium">January 15, 2022</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Work Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Department:</span>
                <span className="text-sm font-medium">Engineering</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Team:</span>
                <span className="text-sm font-medium">Frontend Development</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Manager:</span>
                <span className="text-sm font-medium">Sarah Johnson</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Location:</span>
                <span className="text-sm font-medium">New York Office</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Employment Type:</span>
                <span className="text-sm font-medium">Full-time</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderAttendance = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Attendance Records</h1>
        <p className="text-muted-foreground">Your attendance history and statistics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">This Month</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600 mb-2">95%</div>
            <Progress value={95} className="mb-2" />
            <p className="text-sm text-muted-foreground">20 of 21 working days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Present Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 mb-2">20</div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm text-muted-foreground">Days attended</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Absent Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600 mb-2">1</div>
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm text-muted-foreground">Days missed</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Attendance</CardTitle>
          <CardDescription>Last 7 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { date: "Dec 15, 2024", status: "Present", time: "9:00 AM - 6:00 PM" },
              { date: "Dec 14, 2024", status: "Present", time: "9:15 AM - 6:15 PM" },
              { date: "Dec 13, 2024", status: "Present", time: "8:45 AM - 5:45 PM" },
              { date: "Dec 12, 2024", status: "Absent", time: "Sick Leave" },
              { date: "Dec 11, 2024", status: "Present", time: "9:00 AM - 6:00 PM" },
            ].map((record, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  {record.status === "Present" ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium">{record.date}</p>
                    <p className="text-sm text-muted-foreground">{record.time}</p>
                  </div>
                </div>
                <Badge variant={record.status === "Present" ? "default" : "destructive"}>{record.status}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderLeave = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Leave Management</h1>
        <p className="text-muted-foreground">Your leave balance and history</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Annual Leave</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 mb-2">15</div>
            <Progress value={60} className="mb-2" />
            <p className="text-sm text-muted-foreground">15 of 25 days remaining</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sick Leave</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600 mb-2">8</div>
            <Progress value={80} className="mb-2" />
            <p className="text-sm text-muted-foreground">8 of 10 days remaining</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Personal Leave</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600 mb-2">3</div>
            <Progress value={60} className="mb-2" />
            <p className="text-sm text-muted-foreground">3 of 5 days remaining</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Leave History</CardTitle>
          <CardDescription>Recent leave applications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { type: "Annual Leave", dates: "Dec 20-22, 2024", status: "Approved", days: 3 },
              { type: "Sick Leave", dates: "Dec 12, 2024", status: "Approved", days: 1 },
              { type: "Personal Leave", dates: "Nov 28, 2024", status: "Approved", days: 1 },
              { type: "Annual Leave", dates: "Nov 15-16, 2024", status: "Approved", days: 2 },
            ].map((leave, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div>
                  <p className="font-medium">{leave.type}</p>
                  <p className="text-sm text-muted-foreground">{leave.dates}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">
                    {leave.days} day{leave.days > 1 ? "s" : ""}
                  </span>
                  <Badge variant="default">{leave.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderPerformance = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Performance Review</h1>
        <p className="text-muted-foreground">Your performance metrics and feedback</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Overall Rating</CardTitle>
            <CardDescription>Latest performance review</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-5xl font-bold text-primary mb-2">4.2</div>
              <div className="text-lg text-muted-foreground mb-4">out of 5.0</div>
              <Progress value={84} className="mb-2" />
              <p className="text-sm text-muted-foreground">Exceeds Expectations</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Goals Progress</CardTitle>
            <CardDescription>Quarterly objectives</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Technical Skills</span>
                  <span className="text-sm text-muted-foreground">90%</span>
                </div>
                <Progress value={90} />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Project Delivery</span>
                  <span className="text-sm text-muted-foreground">85%</span>
                </div>
                <Progress value={85} />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Team Collaboration</span>
                  <span className="text-sm text-muted-foreground">95%</span>
                </div>
                <Progress value={95} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Achievements</CardTitle>
          <CardDescription>Your accomplishments this quarter</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { title: "Led successful product launch", date: "Dec 2024", impact: "High" },
              { title: "Mentored 2 junior developers", date: "Nov 2024", impact: "Medium" },
              { title: "Improved code quality metrics by 15%", date: "Oct 2024", impact: "High" },
              { title: "Completed advanced React certification", date: "Oct 2024", impact: "Medium" },
            ].map((achievement, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <Award className="w-5 h-5 text-primary" />
                  <div>
                    <p className="font-medium">{achievement.title}</p>
                    <p className="text-sm text-muted-foreground">{achievement.date}</p>
                  </div>
                </div>
                <Badge variant={achievement.impact === "High" ? "default" : "secondary"}>{achievement.impact}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderContent = () => {
    switch (currentView) {
      case "profile":
        return renderProfile()
      case "attendance":
        return renderAttendance()
      case "leave":
        return renderLeave()
      case "performance":
        return renderPerformance()
      default:
        return renderDashboard()
    }
  }

  return (
    <div className={`flex-1 flex flex-col transition-all duration-300 ${isChatOpen ? "mr-96" : ""}`}>
      <div className="flex-1 overflow-auto p-6">{renderContent()}</div>

      {/* Quick Message Input */}
      {!isChatOpen && (
        <div className="border-t border-border p-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Ask HR Assistant
              </CardTitle>
              <CardDescription>Type your question to get started with the HR chatbot</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Ask about attendance, leave, performance, or any HR topic..."
                  value={quickMessage}
                  onChange={(e) => setQuickMessage(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSendQuickMessage()}
                  className="flex-1"
                />
                <Button onClick={handleSendQuickMessage} disabled={!quickMessage.trim()}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
