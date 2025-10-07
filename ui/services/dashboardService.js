const generateDashboardPrompt = (userId) => `Generate a personalized dashboard for user ${userId}. Return ONLY valid JSON in this exact format:
{
  "attendance": {
    "status": "Present",
    "leave_type": "None",
    "start_date": "2025-10-06",
    "end_date": "2025-10-06"
  },
  "leave_balance": {
    "available": 15,
    "used": 5
  },
  "recent_projects": [
    {
      "project_name": "AI Dashboard",
      "department": "Engineering",
      "status": "In Progress",
      "deadline": "2025-10-25"
    },
    {
      "project_name": "Customer Portal Redesign",
      "department": "UX/UI",
      "status": "Completed",
      "deadline": "2025-09-15"
    },
    {
      "project_name": "Mobile App Launch",
      "department": "Marketing",
      "status": "In Progress",
      "deadline": "2025-10-30"
    },
    {
      "project_name": "Data Analytics Overhaul",
      "department": "Data Science",
      "status": "Not Started",
      "deadline": "2025-11-15"
    },
    {
      "project_name": "Internal Knowledge Base",
      "department": "HR",
      "status": "Completed",
      "deadline": "2025-08-20"
    }
  ],
  "notifications": [
    {
      "title": "Team Meeting",
      "timestamp": "2025-10-06T10:00:00",
      "summary": "Weekly standup meeting."
    }
  ]
}`;

export const fetchDashboardData = async (userId = "current_user") => {
  try {
    // Call local LM Studio API
    const response = await fetch('http://172.25.247.19:1234/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: "local-model",
        messages: [{
          role: "user",
          content: generateDashboardPrompt(userId)
        }],
        temperature: 0.7
      })
    });

    if (!response.ok) {
      throw new Error('Failed to fetch LLM response');
    }

    const llmResponse = await response.json();
    const content = llmResponse.choices[0].message.content;
    
    // Parse JSON from LLM response
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    
    throw new Error('No valid JSON found in LLM response');
  } catch (error) {
    console.error('LLM API error:', error);
    // Fallback data
    return {
      attendance: { status: "Present", leave_type: "None", start_date: "2025-10-06", end_date: "2025-10-06" },
      leave_balance: { available: 10, used: 5 },
      recent_projects: [
        { project_name: "Project Alpha", department: "Engineering", status: "Completed", deadline: "2025-09-30" },
        { project_name: "Project Beta", department: "Engineering", status: "In Progress", deadline: "2025-10-15" },
        { project_name: "Project Gamma", department: "Marketing", status: "Not Started", deadline: "2025-11-10" },
        { project_name: "Project Delta", department: "Sales", status: "In Progress", deadline: "2025-10-20" },
        { project_name: "Project Epsilon", department: "Product", status: "Completed", deadline: "2025-08-25" }
      ],
      notifications: [
        { title: "Team Meeting", timestamp: "2025-10-06T10:00:00", summary: "Scheduled meeting at 10 AM." }
      ]
    };
  }
};
