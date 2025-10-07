import { employees, projects } from '@/components/common/emp_details';
import { qwenService } from './qwen-service';

export async function processHRQuery(query) {
  const lowerQuery = query.toLowerCase().trim();
  
  // Handle greetings directly
  if (isGreeting(lowerQuery)) {
    return {
      response: "Hello! How can I assist you today?",
      employee: null,
      focusSection: "overview"
    };
  }
  
  // Handle specific queries that need UI updates directly
  if (lowerQuery.includes('list all employees') || lowerQuery.includes('show all employees') || lowerQuery.includes('all employee details') || lowerQuery.includes('fetch all employees')) {
    return processHRQueryFallback(query);
  }
  
  if (lowerQuery.includes('freepool') || lowerQuery.includes('free pool')) {
    return processHRQueryFallback(query);
  }
  
  try {
    const response = await qwenService.generateResponse(query);
    return {
      response,
      employee: null,
      focusSection: "overview"
    };
  } catch (error) {
    console.error('Qwen processing error:', error);
    return processHRQueryFallback(query);
  }
}

function isGreeting(query) {
  const greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'];
  return greetings.some(greeting => query === greeting || query.startsWith(greeting + ' '));
}

function processHRQueryFallback(query) {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes('list all employees') || lowerQuery.includes('show all employees') || lowerQuery.includes('all employee details') || lowerQuery.includes('fetch all employees')) {
    return handleAllEmployeesQuery();
  }
  if (lowerQuery.includes('freepool') || lowerQuery.includes('free pool')) {
    return handleFreepoolQuery();
  }
  if (lowerQuery.includes('employee') || lowerQuery.includes('staff')) {
    return handleEmployeeQuery();
  }
  if (lowerQuery.includes('project')) {
    return handleProjectQuery();
  }
  if (lowerQuery.includes('leave') || lowerQuery.includes('vacation')) {
    return handleLeaveQuery();
  }
  if (lowerQuery.includes('skill') || lowerQuery.includes('expertise')) {
    return handleSkillQuery();
  }
  if (lowerQuery.includes('department') || lowerQuery.includes('team')) {
    return handleDepartmentQuery();
  }
  
  return {
    response: "I'm your HR Assistant. I can help with employee info, projects, leave balances, skills, and departments. What would you like to know?",
    employee: null,
    focusSection: "overview"
  };
}

function handleEmployeeQuery() {
  const total = employees.length;
  const active = employees.filter(emp => emp.status === 'active').length;
  const freePool = employees.filter(emp => emp.status === 'freepool').length;
  const avgExp = Math.round(employees.reduce((sum, emp) => sum + emp.years_of_experience, 0) / total * 10) / 10;
  
  return {
    response: `We have ${total} total employees: ${active} active and ${freePool} in free pool. Average experience is ${avgExp} years.`,
    employee: null,
    focusSection: "overview"
  };
}

function handleProjectQuery() {
  const activeProjects = projects?.filter(p => p.status === 'active') || [];
  const employeesInProjects = employees.filter(emp => emp.current_project).length;
  
  return {
    response: `Currently running ${activeProjects.length} active projects with ${employeesInProjects} employees assigned. Key projects: ${activeProjects.map(p => p.name).join(', ')}.`,
    employee: null,
    focusSection: "projects"
  };
}

function handleLeaveQuery() {
  const avgLeave = Math.round(employees.reduce((sum, emp) => sum + emp.leave_balance.annual, 0) / employees.length);
  const topLeave = employees
    .sort((a, b) => b.leave_balance.annual - a.leave_balance.annual)
    .slice(0, 3)
    .map(emp => `${emp.name} (${emp.leave_balance.annual} days)`)
    .join(', ');
  
  return {
    response: `Average annual leave balance is ${avgLeave} days. Top balances: ${topLeave}.`,
    employee: null,
    focusSection: "leave"
  };
}

function handleSkillQuery() {
  const skillMap = {};
  employees.forEach(emp => {
    emp.skills.forEach(skill => {
      skillMap[skill] = (skillMap[skill] || 0) + 1;
    });
  });
  
  const topSkills = Object.entries(skillMap)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([skill, count]) => `${skill} (${count})`)
    .join(', ');
  
  return {
    response: `Top skills in our team: ${topSkills}. Strong in frontend, backend, and DevOps.`,
    employee: null,
    focusSection: "overview"
  };
}

function handleDepartmentQuery() {
  const deptMap = {};
  employees.forEach(emp => {
    deptMap[emp.department] = (deptMap[emp.department] || 0) + 1;
  });
  
  const deptInfo = Object.entries(deptMap)
    .map(([dept, count]) => `${dept}: ${count}`)
    .join(', ');
  
  return {
    response: `Department distribution: ${deptInfo}. Engineering is our largest department.`,
    employee: null,
    focusSection: "overview"
  };
}

function handleAllEmployeesQuery() {
  // Trigger employee table display
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('showEmployeeTable'));
  }
  
  return {
    response: "Here are the details of all employees.",
    employee: null,
    focusSection: "overview"
  };
}

function handleFreepoolQuery() {
  const freepoolEmployees = employees.filter(emp => emp.status === 'freepool');
  const names = freepoolEmployees.map(emp => emp.name).join(', ');
  
  // Trigger employee cards display
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('showEmployeeCards', { detail: { filter: 'freepool' } }));
  }
  
  return {
    response: `We have ${freepoolEmployees.length} employees in the free pool: ${names}. I'll show you their details.`,
    employee: null,
    focusSection: "freepool",
    showEmployeeList: "freepool"
  };
}