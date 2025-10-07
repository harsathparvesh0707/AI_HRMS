"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, MessageCircle, Calendar, Clock, TrendingUp, Users, Code, Briefcase } from "lucide-react"

const employees = [
  {
    id: 1,
    name: "Sanjeev Kumar",
    designation: "Frontend Developer",
    experience: "3 years",
    skills: ["React", "Tailwind", "Redux"],
    status: "Active",
    projects: [
      { name: "HRMS", occupancy: 40 },
      { name: "Task Manager", occupancy: 30 },
    ],
  },
  {
    id: 2,
    name: "Anita Sharma",
    designation: "Full Stack Developer",
    experience: "5 years",
    skills: ["Node.js", "React", "PostgreSQL", "Express"],
    status: "Free Pool",
    projects: [],
    pastProjects: [
      { name: "E-Learning Platform" },
      { name: "Banking Portal" },
      { name: "HRMS" },
    ],
  },
  {
    id: 3,
    name: "Ravi Verma",
    designation: "Backend Developer",
    experience: "6 years",
    skills: ["Java", "Spring Boot", "MySQL"],
    status: "Active",
    projects: [
      { name: "Inventory System", occupancy: 40 },
      { name: "API Gateway", occupancy: 30 },
      { name: "Billing Service", occupancy: 30 },
    ],
  },
  {
    id: 4,
    name: "Meera Iyer",
    designation: "Frontend Developer",
    experience: "2 years",
    skills: ["Vue.js", "JavaScript", "CSS3"],
    status: "Active",
    projects: [{ name: "E-Commerce Website", occupancy: 40 }],
  },
  {
    id: 5,
    name: "Arjun Patel",
    designation: "Mobile App Developer",
    experience: "4 years",
    skills: ["React Native", "Expo", "TypeScript"],
    status: "Active",
    projects: [
      { name: "Delivery App", occupancy: 50 },
      { name: "Chat Messenger", occupancy: 30 },
    ],
  },
  {
    id: 6,
    name: "Neha Gupta",
    designation: "Full Stack Developer",
    experience: "7 years",
    skills: ["Angular", "Node.js", "MongoDB"],
    status: "Active",
    projects: [
      { name: "CRM System", occupancy: 25 },
      { name: "Analytics Dashboard", occupancy: 25 },
      { name: "Booking Portal", occupancy: 25 },
      { name: "IoT Hub", occupancy: 20 },
    ],
  },
  {
    id: 7,
    name: "Karan Mehta",
    designation: "Backend Developer",
    experience: "8 years",
    skills: ["Python", "Django", "PostgreSQL"],
    status: "Active",
    projects: [
      { name: "Payment Gateway", occupancy: 60 },
      { name: "Fraud Detection System", occupancy: 30 },
    ],
  },
  {
    id: 8,
    name: "Priya Nair",
    designation: "Frontend Developer",
    experience: "4 years",
    skills: ["React", "Redux", "Next.js"],
    status: "Free Pool",
    projects: [],
    pastProjects: [
      { name: "Portfolio Builder" },
      { name: "Social Media App" },
    ],
  },
  {
    id: 9,
    name: "Rahul Singh",
    designation: "DevOps Engineer",
    experience: "5 years",
    skills: ["AWS", "Docker", "Kubernetes", "CI/CD"],
    status: "Active",
    projects: [
      { name: "Cloud Migration", occupancy: 50 },
      { name: "Monitoring System", occupancy: 40 },
    ],
  },
  {
    id: 10,
    name: "Sneha Kapoor",
    designation: "Full Stack Developer",
    experience: "6 years",
    skills: ["Node.js", "React", "GraphQL"],
    status: "Free Pool",
    projects: [],
    pastProjects: [
      { name: "Healthcare Portal" },
      { name: "Job Recruitment System" },
      { name: "School ERP" },
    ],
  },
];

interface EmployeeManagementProps {
  selectedEmployee: any
  onSelectEmployee: (employee: any) => void
  onOpenChat: () => void
}

export function EmployeeManagement({ selectedEmployee, onSelectEmployee, onOpenChat }: EmployeeManagementProps) {
  const [searchTerm, setSearchTerm] = useState("")

  const filteredEmployees = employees.filter(
    (employee) =>
      employee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.designation.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const getTotalOccupancy = (projects: any[]) => {
    return projects.reduce((total, project) => total + project.occupancy, 0)
  }

  return (
    <div className="p-6 h-full overflow-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground mb-2">Employee Dashboard</h1>
        <p className="text-muted-foreground">Manage and communicate with your team members</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
        {/* Employee List */}
        <div className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Employees
              </CardTitle>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search employees..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {filteredEmployees.map((employee) => (
                <div
                  key={employee.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedEmployee?.id === employee.id ? "bg-primary/10 border-primary" : "hover:bg-muted/50"
                  }`}
                  onClick={() => onSelectEmployee(employee)}
                >
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={"/placeholder.svg"} alt={employee.name} />
                      <AvatarFallback>
                        {employee.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{employee.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{employee.designation}</p>
                      <Badge variant={employee.status === "Active" ? "default" : "secondary"} className="text-xs mt-1">
                        {employee.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Employee Details */}
        <div className="lg:col-span-2">
          {selectedEmployee ? (
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Avatar className="h-16 w-16">
                      <AvatarImage src={"/placeholder.svg"} alt={selectedEmployee.name} />
                      <AvatarFallback className="text-lg">
                        {selectedEmployee.name
                          .split(" ")
                          .map((n: string) => n[0])
                          .join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <CardTitle className="text-2xl">{selectedEmployee.name}</CardTitle>
                      <p className="text-muted-foreground">{selectedEmployee.designation}</p>
                      <p className="text-sm text-muted-foreground">{selectedEmployee.experience} experience</p>
                    </div>
                  </div>
                  <Button onClick={onOpenChat} className="flex items-center gap-2">
                    <MessageCircle className="h-4 w-4" />
                    Chat
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="overview" className="w-full">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="projects">Projects</TabsTrigger>
                    <TabsTrigger value="skills">Skills</TabsTrigger>
                    <TabsTrigger value="performance">Performance</TabsTrigger>
                  </TabsList>

                  <TabsContent value="overview" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Designation</p>
                        <p className="text-sm text-muted-foreground">{selectedEmployee.designation}</p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Experience</p>
                        <p className="text-sm text-muted-foreground">{selectedEmployee.experience}</p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Status</p>
                        <Badge variant={selectedEmployee.status === "Active" ? "default" : "secondary"}>
                          {selectedEmployee.status}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Current Workload</p>
                        <p className="text-sm text-muted-foreground">
                          {getTotalOccupancy(selectedEmployee.projects)}% occupied
                        </p>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="projects" className="space-y-4">
                    <div className="flex items-center gap-4 mb-4">
                      <Briefcase className="h-8 w-8 text-primary" />
                      <div>
                        <p className="text-2xl font-bold">{selectedEmployee.projects.length}</p>
                        <p className="text-sm text-muted-foreground">Active Projects</p>
                      </div>
                    </div>
                    
                    {selectedEmployee.projects.length > 0 ? (
                      <div className="space-y-3">
                        <p className="text-sm font-medium">Current Projects</p>
                        {selectedEmployee.projects.map((project: any, index: number) => (
                          <div key={index} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                            <p className="text-sm font-medium">{project.name}</p>
                            <Badge variant="outline">{project.occupancy}% occupied</Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-muted-foreground">No active projects</p>
                        <p className="text-sm text-muted-foreground mt-2">Available for new assignments</p>
                      </div>
                    )}

                    {selectedEmployee.pastProjects && selectedEmployee.pastProjects.length > 0 && (
                      <div className="space-y-3">
                        <p className="text-sm font-medium">Past Projects</p>
                        {selectedEmployee.pastProjects.map((project: any, index: number) => (
                          <div key={index} className="p-3 bg-muted/30 rounded-lg">
                            <p className="text-sm">{project.name}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="skills" className="space-y-4">
                    <div className="flex items-center gap-4 mb-4">
                      <Code className="h-8 w-8 text-primary" />
                      <div>
                        <p className="text-2xl font-bold">{selectedEmployee.skills.length}</p>
                        <p className="text-sm text-muted-foreground">Technical Skills</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Skills & Technologies</p>
                      <div className="flex flex-wrap gap-2">
                        {selectedEmployee.skills.map((skill: string, index: number) => (
                          <Badge key={index} variant="outline" className="text-sm">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="performance" className="space-y-4">
                    <div className="flex items-center gap-4">
                      <TrendingUp className="h-8 w-8 text-primary" />
                      <div>
                        <p className="text-2xl font-bold">
                          {selectedEmployee.status === "Free Pool" ? "Available" : "Engaged"}
                        </p>
                        <p className="text-sm text-muted-foreground">Current Status</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Performance Summary</p>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                          • {selectedEmployee.experience} of professional experience
                        </p>
                        <p className="text-sm text-muted-foreground">
                          • Proficient in {selectedEmployee.skills.length} technologies
                        </p>
                        <p className="text-sm text-muted-foreground">
                          • Currently working on {selectedEmployee.projects.length} project(s)
                        </p>
                        {selectedEmployee.pastProjects && (
                          <p className="text-sm text-muted-foreground">
                            • Completed {selectedEmployee.pastProjects.length} past project(s)
                          </p>
                        )}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card className="h-full flex items-center justify-center">
              <CardContent>
                <div className="text-center">
                  <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-lg font-medium">Select an Employee</p>
                  <p className="text-muted-foreground">Choose an employee from the list to view their details</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default EmployeeManagement;