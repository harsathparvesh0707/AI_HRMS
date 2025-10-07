"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { User, Mail, Phone, Calendar, Clock, Award, Activity, CheckCircle, Target, Users } from "lucide-react"
import { useEffect, useState } from "react"

export default function EmployeeDisplay({ employee, focusSection = "overview", projectMatches = null }) {
  
  const [activeTab, setActiveTab] = useState(focusSection)
  
  useEffect(() => {
    if (focusSection) {
      setActiveTab(focusSection)
    }
  }, [focusSection])
  
  if (projectMatches && projectMatches.length > 0) {
    return (
      
      <div className="flex-1 p-4 lg:p-6 overflow-y-auto space-y-6">
        
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              Project Matching Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {projectMatches.map((match, index) => {
                const { employee: emp, score, matchDetails } = match
                const getScoreColor = (score) => {
                  if (score >= 80) return "text-green-600 bg-green-50 border-green-200"
                  if (score >= 60) return "text-blue-600 bg-blue-50 border-blue-200"
                  if (score >= 40) return "text-orange-600 bg-orange-50 border-orange-200"
                  return "text-red-600 bg-red-50 border-red-200"
                }

                return (
                  <Card key={emp.id} className={`transition-all hover:shadow-md border-2 ${getScoreColor(score)}`}>
                    <CardContent className="p-4">
                      <div className="flex flex-col sm:flex-row items-start gap-4">
                        <Avatar className="h-12 w-12 mx-auto sm:mx-0">
                          <AvatarImage src={emp.avatar || "/placeholder.svg"} alt={emp.name} />
                          <AvatarFallback className="text-sm font-semibold">
                            {emp.name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")}
                          </AvatarFallback>
                        </Avatar>

                        <div className="flex-1 space-y-2 text-center sm:text-left">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                            <div>
                              <h3 className="font-semibold text-lg">{emp.name}</h3>
                              <p className="text-sm text-muted-foreground">
                                {emp.position} • {emp.department}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge
                                className={`${score >= 80 ? "bg-green-600" : score >= 60 ? "bg-blue-600" : score >= 40 ? "bg-orange-600" : "bg-red-600"} text-white`}
                              >
                                {score}% Match
                              </Badge>
                              <Badge variant={emp.availability === "Free Pool" ? "default" : "secondary"}>
                                {emp.availability}
                              </Badge>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex flex-wrap gap-1 justify-center sm:justify-start">
                              {emp.skills.slice(0, 4).map((skill, skillIndex) => (
                                <Badge key={skillIndex} variant="outline" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                              {emp.skills.length > 4 && (
                                <Badge variant="outline" className="text-xs">
                                  +{emp.skills.length - 4} more
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">{matchDetails.join(" • ")}</p>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                            <div className="text-center sm:text-left">
                              <span className="font-medium">Experience</span>
                              <div className="text-primary">{emp.experience.years} years</div>
                            </div>
                            <div className="text-center sm:text-left">
                              <span className="font-medium">Performance</span>
                              <div className="text-primary">{emp.performance.rating}/5.0</div>
                            </div>
                            <div className="text-center sm:text-left">
                              <span className="font-medium">Attendance</span>
                              <div className="text-primary">{emp.attendance.rate}%</div>
                            </div>
                            <div className="text-center sm:text-left">
                              <span className="font-medium">Projects</span>
                              <div className="text-primary">{emp.experience.projects.length}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!employee) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center space-y-6 max-w-md">
          <div className="w-20 h-20 mx-auto rounded-full bg-muted flex items-center justify-center">
            <User className="h-10 w-10 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-semibold text-balance">No Employee Selected</h3>
            <p className="text-sm text-muted-foreground text-pretty">
              Ask the HR Assistant about an employee to view their detailed information and analytics here
            </p>
          </div>
        </div>
      </div>
    )
  }

  const getStatusColor = (status) => {
    switch (status) {
      case "Active":
        return "bg-primary text-primary-foreground"
      case "On Leave":
        return "bg-secondary text-secondary-foreground"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getAvailabilityColor = (availability) => {
    switch (availability) {
      case "Free Pool":
        return "bg-green-600 text-white"
      case "Assigned":
        return "bg-blue-600 text-white"
      case "On Leave":
        return "bg-orange-600 text-white"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getPerformanceColor = (rating) => {
    if (rating >= 4.5) return "text-primary"
    if (rating >= 4.0) return "text-blue-600"
    if (rating >= 3.5) return "text-secondary"
    return "text-destructive"
  }

  return (
    <div className="flex-1 p-4 lg:p-6 overflow-y-auto space-y-6">
      <Card className="overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-start gap-6">
            <Avatar className="h-20 w-20 sm:h-24 sm:w-24 mx-auto sm:mx-0">
              <AvatarImage src={employee.avatar || "/placeholder.svg"} alt={employee.name} />
              <AvatarFallback className="text-lg font-semibold">
                {employee.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 space-y-4 text-center sm:text-left">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h1 className="text-2xl font-bold text-balance">{employee.name}</h1>
                  <p className="text-lg text-muted-foreground">{employee.position}</p>
                </div>
                <div className="flex gap-2 justify-center sm:justify-end">
                  <Badge className={`${getStatusColor(employee.status)} w-fit`}>{employee.status}</Badge>
                  {employee.availability && (
                    <Badge className={`${getAvailabilityColor(employee.availability)} w-fit`}>
                      {employee.availability}
                    </Badge>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate">{employee.email}</span>
                </div>
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span>{employee.phone}</span>
                </div>
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <Calendar className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span>Joined {employee.startDate}</span>
                </div>
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span>{employee.department}</span>
                </div>
              </div>

              {employee.skills && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-muted-foreground">Skills</h3>
                  <div className="flex flex-wrap gap-1 justify-center sm:justify-start">
                    {employee.skills.map((skill, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-5 h-auto">
          <TabsTrigger
            value="overview"
            className={`text-xs sm:text-sm transition-all ${activeTab === "overview" ? "ring-2 ring-primary/20" : ""}`}
          >
            Overview
          </TabsTrigger>
          <TabsTrigger
            value="attendance"
            className={`text-xs sm:text-sm transition-all ${activeTab === "attendance" ? "ring-2 ring-primary/20" : ""}`}
          >
            Attendance
          </TabsTrigger>
          <TabsTrigger
            value="leave"
            className={`text-xs sm:text-sm transition-all ${activeTab === "leave" ? "ring-2 ring-primary/20" : ""}`}
          >
            Leave
          </TabsTrigger>
          <TabsTrigger
            value="performance"
            className={`text-xs sm:text-sm transition-all ${activeTab === "performance" ? "ring-2 ring-primary/20" : ""}`}
          >
            Performance
          </TabsTrigger>
          <TabsTrigger
            value="skills"
            className={`text-xs sm:text-sm transition-all ${activeTab === "skills" ? "ring-2 ring-primary/20" : ""}`}
          >
            Skills
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="transition-smooth hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Attendance Rate</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">{employee.attendance.rate}%</div>
                <Progress value={employee.attendance.rate} className="mt-2" />
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Leave Balance</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-secondary">{employee.leave.remaining} days</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {employee.leave.used}/{employee.leave.totalAllowed} used this year
                </p>
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Performance</CardTitle>
                <Award className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getPerformanceColor(employee.performance.rating)}`}>
                  {employee.performance.rating}/5.0
                </div>
                <p className="text-xs text-muted-foreground mt-1 text-pretty">{employee.performance.feedback}</p>
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Goals Progress</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">
                  {employee.performance.completed}/{employee.performance.goals}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Goals completed</p>
              </CardContent>
            </Card>
          </div>

          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary" />
                Employee Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-primary flex-shrink-0" />
                  <span>
                    <strong>Department:</strong> {employee.department}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-secondary flex-shrink-0" />
                  <span>
                    <strong>Start Date:</strong> {employee.startDate}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-accent flex-shrink-0" />
                  <span>
                    <strong>Last Review:</strong> {employee.performance.lastReview}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="attendance" className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle className="text-primary">This Month</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">
                  {employee.attendance.thisMonth}/{employee.attendance.totalDays}
                </div>
                <p className="text-sm text-muted-foreground">Days present</p>
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle className="text-secondary">Late Arrivals</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-secondary">{employee.attendance.lateArrivals}</div>
                <p className="text-sm text-muted-foreground">This month</p>
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle className="text-orange-600">Early Departures</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">{employee.attendance.earlyDepartures}</div>
                <p className="text-sm text-muted-foreground">This month</p>
              </CardContent>
            </Card>
          </div>

          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle>Recent Check-ins</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <span className="font-medium">Last Check-in</span>
                  <span className="text-primary font-mono">{employee.attendance.lastCheckIn}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <span className="font-medium">Last Check-out</span>
                  <span className="text-secondary font-mono">{employee.attendance.lastCheckOut}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leave" className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle className="text-primary">Remaining</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">{employee.leave.remaining}</div>
                <p className="text-sm text-muted-foreground">Days available</p>
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle className="text-secondary">Used</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-secondary">{employee.leave.used}</div>
                <p className="text-sm text-muted-foreground">Days this year</p>
              </CardContent>
            </Card>

            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle>Total Allocation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{employee.leave.totalAllowed}</div>
                <p className="text-sm text-muted-foreground">Days per year</p>
              </CardContent>
            </Card>
          </div>

          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle>Leave Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg gap-3">
                  <div>
                    <div className="font-medium">Last Leave Taken</div>
                    <div className="text-sm text-muted-foreground">{employee.leave.lastLeave}</div>
                  </div>
                  <Badge variant="outline">Recent</Badge>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg gap-3">
                  <div>
                    <div className="font-medium">Pending Requests</div>
                    <div className="text-sm text-muted-foreground">Awaiting approval</div>
                  </div>
                  <Badge variant="outline">{employee.leave.pending} days</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5 text-primary" />
                Current Rating
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <div className={`text-4xl font-bold ${getPerformanceColor(employee.performance.rating)}`}>
                  {employee.performance.rating}/5.0
                </div>
                <div className="flex-1 text-center sm:text-left">
                  <div className="font-medium text-pretty">{employee.performance.feedback}</div>
                  <Progress value={employee.performance.rating * 20} className="mt-3 w-full sm:w-48" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle>Performance Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg gap-3">
                  <div>
                    <div className="font-medium">Last Review</div>
                    <div className="text-sm text-muted-foreground">{employee.performance.lastReview}</div>
                  </div>
                  <div className={`text-lg font-bold ${getPerformanceColor(employee.performance.rating)}`}>
                    {employee.performance.rating}/5.0
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg gap-3">
                  <div>
                    <div className="font-medium">Goals Progress</div>
                    <div className="text-sm text-muted-foreground">
                      {employee.performance.completed} of {employee.performance.goals} completed
                    </div>
                  </div>
                  <div className="text-lg font-bold text-primary">
                    {Math.round((employee.performance.completed / employee.performance.goals) * 100)}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle>Manager Feedback</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm italic text-pretty">"{employee.performance.feedback}"</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="skills" className="space-y-4">
          <Card className="transition-smooth hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Technical Skills
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {employee.skills &&
                  employee.skills.map((skill, index) => (
                    <div key={index} className="p-3 border rounded-lg text-center hover:bg-muted/50 transition-colors">
                      <div className="font-medium text-sm">{skill}</div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {employee.experience && (
            <Card className="transition-smooth hover:shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-primary" />
                  Experience & Projects
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium">Years of Experience</div>
                      <div className="text-sm text-muted-foreground">Professional experience</div>
                    </div>
                    <div className="text-2xl font-bold text-primary">{employee.experience.years}</div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium">Recent Projects</h4>
                    <div className="grid gap-2">
                      {employee.experience.projects.map((project, index) => (
                        <div key={index} className="p-3 border rounded-lg">
                          <div className="font-medium text-sm">{project}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
