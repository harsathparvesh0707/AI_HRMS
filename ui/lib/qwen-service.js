import { employees, projects } from '@/components/common/emp_details';

class QwenService {
  constructor() {
    this.apiUrl = process.env.NEXT_PUBLIC_QWEN_API_URL || 'http://172.25.243.122:1234/v1/chat/completions';
    this.employees = employees;
    this.projects = projects;
  }

  async generateResponse(query) {
    const context = this.buildContext();
    const prompt = this.buildPrompt(query, context);

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'qwen2-500m-instruct',
          messages: [
            {
              role: 'system',
              content: 'You are an HR Assistant. Provide concise, helpful responses about employees, projects, and HR matters based on the provided data.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          max_tokens: 200,
          temperature: 0.7,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.choices?.[0]?.message?.content || this.getFallbackResponse(query);
    } catch (error) {
      console.error('Qwen API error:', error);
      return this.getFallbackResponse(query);
    }
  }

  buildContext() {
    const employeeStats = {
      total: this.employees.length,
      active: this.employees.filter(emp => emp.status === 'active').length,
      freePool: this.employees.filter(emp => emp.status === 'freepool').length,
      avgExperience: Math.round(this.employees.reduce((sum, emp) => sum + emp.years_of_experience, 0) / this.employees.length * 10) / 10
    };

    const departments = {};
    const skills = {};
    this.employees.forEach(emp => {
      departments[emp.department] = (departments[emp.department] || 0) + 1;
      emp.skills.forEach(skill => {
        skills[skill] = (skills[skill] || 0) + 1;
      });
    });

    return {
      employees: this.employees,
      projects: this.projects,
      stats: employeeStats,
      departments,
      skills
    };
  }

  buildPrompt(query, context) {
    const lowerQuery = query.toLowerCase();
    
    if (this.isFreepoolQuery(lowerQuery)) {
      const freepoolEmployees = context.employees.filter(emp => emp.status === 'freepool');
      const employeeList = freepoolEmployees.map(emp => 
        `${emp.name} (${emp.designation}, ${emp.years_of_experience} years exp, Skills: ${emp.skills.slice(0, 3).join(', ')})`
      ).join('\n');
      
      return `User asked: "${query}"

Freepool Employees (${freepoolEmployees.length} total):
${employeeList}

Provide a helpful response listing these freepool employees with their key details.`;
    }
    
    if (this.isAllEmployeesQuery(lowerQuery)) {
      const employeeList = context.employees.map(emp => 
        `${emp.name} (${emp.designation}, ${emp.status}, ${emp.years_of_experience} years exp)`
      ).join('\n');
      
      return `User asked: "${query}"

All Employees (${context.employees.length} total):
${employeeList}

Provide a helpful response listing all employees with their key details.`;
    }
    
    return `Based on the following HR data, answer the user's question: "${query}"

Employee Statistics:
- Total: ${context.stats.total} employees
- Active: ${context.stats.active}
- Free Pool: ${context.stats.freePool}
- Average Experience: ${context.stats.avgExperience} years

Departments: ${Object.entries(context.departments).map(([dept, count]) => `${dept}: ${count}`).join(', ')}

Top Skills: ${Object.entries(context.skills).sort(([,a], [,b]) => b - a).slice(0, 5).map(([skill, count]) => `${skill} (${count})`).join(', ')}

Active Projects: ${context.projects?.filter(p => p.status === 'active').map(p => p.name).join(', ') || 'None'}

Please provide a helpful, concise response.`;
  }

  getFallbackResponse(query) {
    const lowerQuery = query.toLowerCase();
    
    if (this.isFreepoolQuery(lowerQuery)) {
      const freepoolEmployees = this.employees.filter(emp => emp.status === 'freepool');
      const employeeList = freepoolEmployees.map(emp => 
        `• ${emp.name} - ${emp.designation} (${emp.years_of_experience} years experience)`
      ).join('\n');
      return `Here are the ${freepoolEmployees.length} employees currently in the freepool:\n\n${employeeList}`;
    }
    
    if (this.isAllEmployeesQuery(lowerQuery)) {
      const employeeList = this.employees.map(emp => 
        `• ${emp.name} - ${emp.designation} (${emp.status}, ${emp.years_of_experience} years experience)`
      ).join('\n');
      return `Here are all ${this.employees.length} employees:\n\n${employeeList}`;
    }
    
    if (lowerQuery.includes('employee') || lowerQuery.includes('staff')) {
      const total = this.employees.length;
      const active = this.employees.filter(emp => emp.status === 'active').length;
      const freePool = this.employees.filter(emp => emp.status === 'freepool').length;
      return `We have ${total} total employees: ${active} active and ${freePool} in free pool.`;
    }
    
    if (lowerQuery.includes('project')) {
      const activeProjects = this.projects?.filter(p => p.status === 'active') || [];
      return `Currently running ${activeProjects.length} active projects: ${activeProjects.map(p => p.name).join(', ')}.`;
    }
    
    return "I'm your HR Assistant. I can help with employee info, projects, leave balances, skills, and departments.";
  }

  async getAllEmployees() {
    const query = 'Retrieve all employee records from the database';
    await this.generateResponse(query); // Log the LLM interaction
    return this.employees;
  }

  async getDashboardEmployees() {
    const query = 'Get employees for dashboard display';
    await this.generateResponse(query); // Log the LLM interaction
    return this.employees;
  }

  async getEmployeesByFilter(filter) {
    const query = `Get employees with status: ${filter}`;
    await this.generateResponse(query); // Log the LLM interaction
    return this.employees.filter(emp => emp.status === filter);
  }

  async getEmployeeStats() {
    const query = 'Calculate employee statistics';
    await this.generateResponse(query); // Log the LLM interaction
    return {
      total: this.employees.length,
      inProject: this.employees.filter(emp => emp.current_project).length,
      freePool: this.employees.filter(emp => emp.status === 'freepool').length,
      active: this.employees.filter(emp => emp.status === 'active').length
    };
  }

  isFreepoolQuery(lowerQuery) {
    return lowerQuery.includes('freepool') || lowerQuery.includes('free pool') ||
           (lowerQuery.includes('list') && lowerQuery.includes('employees') && lowerQuery.includes('freepool')) ||
           (lowerQuery.includes('fetch') && lowerQuery.includes('employees') && lowerQuery.includes('freepool')) ||
           (lowerQuery.includes('all') && lowerQuery.includes('employees') && lowerQuery.includes('freepool')) ||
           (lowerQuery.includes('show') && lowerQuery.includes('employees') && lowerQuery.includes('freepool')) ||
           (lowerQuery.includes('get') && lowerQuery.includes('employees') && lowerQuery.includes('freepool'));
  }

  isAllEmployeesQuery(lowerQuery) {
    return (lowerQuery.includes('list') && lowerQuery.includes('all') && lowerQuery.includes('employees')) ||
           (lowerQuery.includes('fetch') && lowerQuery.includes('all') && lowerQuery.includes('employees')) ||
           (lowerQuery.includes('show') && lowerQuery.includes('all') && lowerQuery.includes('employees')) ||
           (lowerQuery.includes('get') && lowerQuery.includes('all') && lowerQuery.includes('employees')) ||
           lowerQuery.includes('all employees') ||
           (lowerQuery.includes('list') && lowerQuery.includes('employees') && !lowerQuery.includes('freepool'));
  }
}

export const qwenService = new QwenService();