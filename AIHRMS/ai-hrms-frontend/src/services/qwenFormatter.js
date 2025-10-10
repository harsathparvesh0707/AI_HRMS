class QwenFormatter {
  constructor() {
    this.modelEndpoint = "http://172.25.243.122:1234/v1/chat/completions";
    this.cache = new Map();
    this.systemPrompt = `You are an expert AI assistant specialized in HR management systems and data visualization. 
Your role is to generate realistic mock data and create optimal UI layouts for HR applications.

Key Responsibilities:
1. Generate structured, realistic HR data that matches user queries
2. Create clean, professional UI layouts that highlight important information
3. Ensure data consistency and appropriate component selection
4. Provide actionable insights through well-organized interfaces

Guidelines:
- Always return valid JSON in the specified format
- Make data realistic and context-appropriate
- Prioritize user experience in layout design
- Include relevant metrics and actions
- Maintain professional HR system standards`;
  }

  async searchAndGenerateLayout(query) {
    try {
      console.log("Generating mock data via LLM for query:", query);

      const mockData = await this.generateMockDataWithLLM(query);
      console.log("LLM Generated Mock Data:", mockData);

      const layout = await this.generateDynamicLayoutWithLLM(mockData, query);
      return { data: mockData, layout };
    } catch (error) {
      console.error("Layout generation failed:", error);
      throw error;
    }
  }

  // Generate structured mock data optimized for LLM understanding
  generateStructuredMockData(query) {
    const queryLower = query.toLowerCase();

    // Map queries to specific data types for better LLM understanding
    const dataMap = {
      employee: this.generateEmployeeProfileData(),
      department: this.generateDepartmentOverviewData(),
      attendance: this.generateAttendanceReportData(),
      salary: this.generateSalarySummaryData(),
      project: this.generateProjectPortfolioData(),
      analytics: this.generateHRAnalyticsData(),
      default: this.generateDashboardOverviewData(),
    };

    // Find the best matching data type
    for (const [key, generator] of Object.entries(dataMap)) {
      if (queryLower.includes(key)) {
        return generator;
      }
    }

    return dataMap.default;
  }

  generateEmployeeProfileData() {
    return {
      data_type: "employee_profile",
      query_context: "Employee details and profile information",
      primary_data: {
        employee: {
          id: 1001,
          personal_info: {
            first_name: "Sarah",
            last_name: "Johnson",
            email: "sarah.johnson@company.com",
            phone: "+1-555-0123",
            date_of_birth: "1990-08-15",
          },
          employment_info: {
            employee_id: "EMP-2021-006",
            date_of_joining: "2021-03-10",
            department: "Engineering",
            position: "Senior Software Engineer",
            manager: "Michael Chen",
            employment_status: "Active",
            work_location: "New York Office",
          },
          professional_info: {
            skills: ["JavaScript", "React", "Node.js", "Python", "AWS"],
            certifications: ["AWS Certified", "React Professional"],
            years_of_experience: 8,
          },
        },
      },
      summary_metrics: {
        total_projects: 12,
        completed_projects: 9,
        current_projects: 3,
        performance_rating: 4.7,
      },
      recent_activity: [
        {
          date: "2024-01-20",
          activity: "Completed Project Alpha",
          type: "project_completion",
        },
        {
          date: "2024-01-18",
          activity: "Attended AWS Training",
          type: "training",
        },
      ],
      available_actions: [
        {
          action: "view_full_profile",
          label: "View Complete Profile",
          icon: "👤",
        },
        { action: "contact_employee", label: "Send Message", icon: "📧" },
        { action: "view_projects", label: "View Projects", icon: "📂" },
        { action: "view_attendance", label: "Attendance Record", icon: "📊" },
        { action: "view_salary", label: "Salary Details", icon: "💰" },
        { action: "schedule_meeting", label: "Schedule Meeting", icon: "📅" },
      ],
    };
  }

  generateDepartmentOverviewData() {
    return {
      data_type: "department_overview",
      query_context: "Department structure and team information",
      primary_data: {
        departments: [
          {
            id: "DEPT-001",
            name: "Engineering",
            manager: "Michael Chen",
            team_size: 24,
            budget: 2500000,
            active_projects: 8,
            headcount_utilization: 92,
            key_metrics: {
              project_success_rate: 88,
              employee_satisfaction: 4.5,
              budget_utilization: 78,
            },
          },
          {
            id: "DEPT-002",
            name: "Sales",
            manager: "Lisa Wang",
            team_size: 18,
            budget: 1200000,
            active_projects: 5,
            headcount_utilization: 85,
            key_metrics: {
              quota_achievement: 112,
              deal_conversion_rate: 24,
              customer_satisfaction: 4.3,
            },
          },
          {
            id: "DEPT-003",
            name: "Marketing",
            manager: "David Kim",
            team_size: 12,
            budget: 800000,
            active_projects: 4,
            headcount_utilization: 88,
            key_metrics: {
              lead_generation: 2450,
              campaign_roi: 320,
              brand_awareness: 78,
            },
          },
        ],
      },
      summary_metrics: {
        total_departments: 8,
        total_employees: 156,
        total_budget: 8500000,
        average_utilization: 88,
      },
      available_actions: [
        { action: "view_employees", label: "View Team Members", icon: "👥" },
        { action: "view_budget", label: "Budget Details", icon: "📈" },
        { action: "add_department", label: "Add Department", icon: "➕" },
        { action: "export_data", label: "Export Report", icon: "📤" },
        {
          action: "compare_departments",
          label: "Compare Departments",
          icon: "⚖️",
        },
      ],
    };
  }

  generateAttendanceReportData() {
    return {
      data_type: "attendance_report",
      query_context: "Employee attendance and time tracking",
      primary_data: {
        attendance_records: [
          {
            employee_id: 1001,
            employee_name: "Sarah Johnson",
            date: "2024-01-22",
            check_in: "08:55:00",
            check_out: "17:30:00",
            hours_worked: 8.6,
            status: "Present",
            breaks_taken: 1,
            overtime_hours: 0.5,
          },
          {
            employee_id: 1002,
            employee_name: "Mike Brown",
            date: "2024-01-22",
            check_in: "09:05:00",
            check_out: "17:25:00",
            hours_worked: 8.3,
            status: "Present",
            breaks_taken: 1,
            overtime_hours: 0,
          },
          {
            employee_id: 1003,
            employee_name: "Anna Davis",
            date: "2024-01-22",
            check_in: null,
            check_out: null,
            hours_worked: 0,
            status: "Sick Leave",
            breaks_taken: 0,
            overtime_hours: 0,
          },
        ],
      },
      summary_metrics: {
        total_employees: 156,
        present_today: 142,
        absent_today: 8,
        late_arrivals: 6,
        average_hours_worked: 8.4,
        attendance_rate: 94.2,
      },
      trends: {
        weekly_attendance: [92, 94, 95, 93, 94, 96, 94],
        common_absence_reasons: [
          "Sick Leave",
          "Vacation",
          "Personal",
          "Training",
        ],
      },
      available_actions: [
        { action: "view_monthly_report", label: "Monthly Report", icon: "📅" },
        { action: "export_data", label: "Export Data", icon: "📤" },
        { action: "mark_attendance", label: "Mark Attendance", icon: "✅" },
        { action: "view_analytics", label: "Analytics", icon: "📊" },
        { action: "set_reminders", label: "Set Reminders", icon: "⏰" },
      ],
    };
  }

  generateSalarySummaryData() {
    return {
      data_type: "salary_summary",
      query_context: "Employee compensation and payroll information",
      primary_data: {
        salary_records: [
          {
            employee_id: 1001,
            employee_name: "Sarah Johnson",
            position: "Senior Software Engineer",
            base_salary: 95000,
            bonus: 15000,
            allowances: 8000,
            deductions: 12000,
            net_salary: 106000,
            pay_period: "January 2024",
            currency: "USD",
          },
          {
            employee_id: 1002,
            employee_name: "Mike Brown",
            position: "Software Engineer",
            base_salary: 75000,
            bonus: 10000,
            allowances: 6000,
            deductions: 9000,
            net_salary: 82000,
            pay_period: "January 2024",
            currency: "USD",
          },
        ],
      },
      summary_metrics: {
        total_payroll: 1250000,
        average_salary: 78500,
        highest_salary: 145000,
        lowest_salary: 45000,
        tax_contributions: 285000,
        bonus_payout: 185000,
      },
      distribution: {
        by_department: {
          Engineering: 685000,
          Sales: 285000,
          Marketing: 185000,
          HR: 95000,
        },
        by_level: {
          Executive: 245000,
          Senior: 485000,
          "Mid-level": 385000,
          Junior: 135000,
        },
      },
      available_actions: [
        { action: "view_payslip", label: "View Payslip", icon: "📄" },
        { action: "run_payroll", label: "Run Payroll", icon: "💰" },
        { action: "salary_report", label: "Generate Report", icon: "📈" },
        { action: "export_data", label: "Export Data", icon: "📤" },
        { action: "adjust_salary", label: "Adjust Salary", icon: "⚙️" },
      ],
    };
  }

  generateProjectPortfolioData() {
    return {
      data_type: "project_portfolio",
      query_context: "Project management and team assignments",
      primary_data: {
        projects: [
          {
            project_id: "PROJ-2024-001",
            name: "AI HRMS Implementation",
            description: "Implement AI-powered HR management system",
            manager: "Sarah Johnson",
            team_size: 8,
            start_date: "2024-01-15",
            end_date: "2024-06-30",
            status: "In Progress",
            progress: 65,
            budget: 500000,
            risks: ["Technical dependencies", "Resource allocation"],
            milestones: [
              { name: "Requirement Analysis", completed: true },
              { name: "Design Phase", completed: true },
              { name: "Development", completed: false },
              { name: "Testing", completed: false },
            ],
          },
        ],
      },
      summary_metrics: {
        total_projects: 24,
        active_projects: 18,
        completed_projects: 6,
        total_budget: 3500000,
        average_completion: 72,
        on_time_delivery: 85,
      },
      available_actions: [
        { action: "view_details", label: "Project Details", icon: "📋" },
        { action: "assign_team", label: "Assign Team", icon: "👥" },
        { action: "update_status", label: "Update Status", icon: "🔄" },
        { action: "view_timeline", label: "View Timeline", icon: "📅" },
        { action: "add_project", label: "New Project", icon: "➕" },
      ],
    };
  }

  generateHRAnalyticsData() {
    return {
      data_type: "hr_analytics",
      query_context: "HR metrics and workforce analytics",
      primary_data: {
        workforce_metrics: {
          headcount: 156,
          turnover_rate: 8.2,
          average_tenure: 3.8,
          diversity_index: 72,
          employee_satisfaction: 4.3,
        },
        performance_metrics: {
          average_performance_rating: 4.2,
          high_performers: 28,
          training_completion_rate: 89,
          promotion_rate: 12,
        },
        recruitment_metrics: {
          time_to_hire: 32,
          cost_per_hire: 8500,
          offer_acceptance_rate: 78,
          quality_of_hire: 4.1,
        },
      },
      trends: {
        headcount_growth: [142, 145, 148, 152, 156],
        turnover_trend: [10.2, 9.5, 8.8, 8.2, 7.9],
        satisfaction_trend: [4.1, 4.2, 4.2, 4.3, 4.3],
      },
      available_actions: [
        { action: "view_dashboard", label: "Analytics Dashboard", icon: "📊" },
        { action: "generate_report", label: "Generate Report", icon: "📄" },
        { action: "export_data", label: "Export Analytics", icon: "📤" },
        { action: "set_goals", label: "Set KPIs", icon: "🎯" },
        { action: "compare_periods", label: "Compare Periods", icon: "⚖️" },
      ],
    };
  }

  generateDashboardOverviewData() {
    return {
      data_type: "dashboard_overview",
      query_context: "HR system dashboard and key metrics",
      primary_data: {
        quick_stats: {
          total_employees: 156,
          active_projects: 18,
          pending_requests: 23,
          upcoming_birthdays: 5,
        },
        recent_activity: [
          {
            type: "new_hire",
            employee: "John Wilson",
            department: "Engineering",
            timestamp: "2024-01-20",
          },
          {
            type: "project_completion",
            project: "Mobile App v2.0",
            manager: "Mike Brown",
            timestamp: "2024-01-19",
          },
        ],
      },
      summary_metrics: {
        attendance_rate: 94.2,
        project_completion: 72,
        employee_satisfaction: 4.3,
        budget_utilization: 78,
      },
      available_actions: [
        { action: "view_employees", label: "Employee Directory", icon: "👥" },
        { action: "view_projects", label: "Project Portfolio", icon: "📂" },
        { action: "view_analytics", label: "HR Analytics", icon: "📊" },
        { action: "view_reports", label: "Reports", icon: "📄" },
        { action: "system_settings", label: "Settings", icon: "⚙️" },
      ],
    };
  }

  async generateMockDataWithLLM(query) {
    try {
      const prompt = `Generate realistic HR system mock data for query: "${query}"

Return JSON data in this format:
{
  "action": "query",
  "response": "Brief response message",
  "data": {
    "database_results": {
      "select_employees_0": {
        "data": [
          {
            "employee_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@company.com",
            "phone": "+1234567890",
            "date_of_joining": "2023-01-15"
          }
        ]
      }
    }
  }
}

JSON Response:`;

      const response = await fetch(this.modelEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "qwen2-500m-instruct",
          messages: [
            { role: "system", content: this.systemPrompt },
            { role: "user", content: prompt },
          ],
          max_tokens: 1000,
          temperature: 0.3,
        }),
      });

      if (!response.ok) {
        throw new Error(`LLM API error! status: ${response.status}`);
      }

      const result = await response.json();
      const mockData = this.parseMockDataResponse(
        result.choices[0].message.content
      );
      return mockData || this.generateStructuredMockData(query);
    } catch (error) {
      console.error("LLM mock data generation error:", error);
      return this.generateStructuredMockData(query);
    }
  }

  parseMockDataResponse(response) {
    try {
      const cleanedResponse = response.replace(/```json\n?|\n?```/g, "").trim();
      const jsonMatch = cleanedResponse.match(/\{[\s\S]*\}/);

      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      throw new Error("No JSON found in LLM response");
    } catch (error) {
      console.error("Failed to parse LLM mock data response:", error);
      return null;
    }
  }

  async generateDynamicLayoutWithLLM(mockData, context) {
    try {
      const prompt = this.buildOptimizedLayoutPrompt(mockData, context);

      console.log("Sending structured data to LLM for layout generation");
      const response = await fetch(this.modelEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "qwen2-500m-instruct",
          messages: [
            { role: "system", content: this.systemPrompt },
            { role: "user", content: prompt },
          ],
          max_tokens: 2000,
          temperature: 0.2,
        }),
      });

      if (!response.ok) {
        throw new Error(`LLM API error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("LLM Layout Response:", result);

      return this.parseLayoutResponse(result.choices[0].message.content);
    } catch (error) {
      console.error("LLM layout generation error:", error);
      return this.fallbackLayout(mockData);
    }
  }

  buildOptimizedLayoutPrompt(mockData, context) {
    return `
You are an expert UI layout designer for HR management systems. Create an optimal React component layout based on the data provided.

DATA:
${JSON.stringify(mockData, null, 2)}

USER QUERY: "${context}"

Analyze the data structure and create appropriate UI components.

DESIGN REQUIREMENTS:
1. Create a layout that highlights the most important information first
2. Use appropriate component types for different data structures
3. Include action buttons for user interactions
4. Show summary metrics prominently
5. Ensure good information hierarchy

AVAILABLE COMPONENT TYPES:
- "header": For titles and main descriptions
- "profile_card": For individual employee/department profiles
- "data_table": For tabular data arrays
- "metrics_grid": For displaying multiple metrics
- "action_panel": For action buttons
- "info_card": For general information display
- "chart": For data visualization (trends, distributions)
- "timeline": For chronological data

RETURN JSON in this format:
{
  "layout": {
    "type": "responsive_grid",
    "columns": 2,
    "gap": "24px",
    "components": [
      {
        "type": "header",
        "title": "Main Title",
        "subtitle": "Context description",
        "dataField": "query_context",
        "style": {
          "gridColumn": "span 2",
          "background": "gradient",
          "padding": "24px"
        }
      },
      {
        "type": "profile_card",
        "title": "Primary Information",
        "dataField": "primary_data.employee",
        "style": {
          "gridColumn": "span 2"
        }
      },
      {
        "type": "metrics_grid",
        "title": "Key Metrics",
        "dataField": "summary_metrics",
        "style": {
          "gridColumn": "span 2"
        }
      },
      {
        "type": "action_panel",
        "title": "Available Actions",
        "dataField": "available_actions",
        "style": {
          "gridColumn": "span 2"
        }
      }
    ]
  },
  "dataMapping": {
    "employee_id": "Employee ID",
    "first_name": "First Name",
    "last_name": "Last Name"
  }
}

Focus on creating a clean, professional layout that makes the data easily understandable and actionable.

JSON Response:`;
  }

  parseLayoutResponse(response) {
    try {
      const cleanedResponse = response.replace(/```json\n?|\n?```/g, "").trim();
      const jsonMatch = cleanedResponse.match(/\{[\s\S]*\}/);

      if (jsonMatch) {
        const layout = JSON.parse(jsonMatch[0]);
        console.log("Successfully parsed LLM layout:", layout);
        return layout;
      }
      throw new Error("No valid JSON found in LLM response");
    } catch (error) {
      console.error("Failed to parse LLM layout response:", error);
      return this.fallbackLayout();
    }
  }

  fallbackLayout(data = {}) {
    return {
      layout: {
        type: "responsive_grid",
        columns: 2,
        gap: "24px",
        components: [
          {
            type: "header",
            title: "HR System Data",
            subtitle: data.query_context || "Overview Information",
            dataField: "query_context",
            style: {
              gridColumn: "span 2",
              background: "gradient",
              padding: "24px",
            },
          },
          {
            type: "info_card",
            title: "Primary Data",
            dataField: "primary_data",
            style: {
              gridColumn: "span 2",
            },
          },
          {
            type: "action_panel",
            title: "Available Actions",
            dataField: "available_actions",
            style: {
              gridColumn: "span 2",
            },
          },
        ],
      },
      dataMapping: {},
    };
  }
}

export default new QwenFormatter();
