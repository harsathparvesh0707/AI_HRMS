import searchApi from "./searchApi.js";

class QwenFormatter {
  constructor() {
    this.modelEndpoint = "http://172.25.243.122:1234/v1/chat/completions";
    this.cache = new Map();
    this.maxCacheSize = 100;
  }

  async searchAndGenerateLayout(query) {
    try {
      console.log("Starting LLM-powered search:", query);

      // Step 1: Execute search
      const rawSearchData = await searchApi.search(query);
      console.log("Search API Response:", rawSearchData);

      // Step 2: Normalize data
      const normalizedData = this.normalizeSearchData(rawSearchData);
      
      // Step 3: LLM decides component layout
      const layout = await this.generateLayoutWithLLM(normalizedData, query);
      
      console.log("LLM layout complete");
      return { data: normalizedData, layout };
    } catch (error) {
      console.error("Error in search pipeline:", error);
      throw error;
    }
  }

  normalizeSearchData(rawData) {
    console.log("Normalizing search data - RAW:", rawData);

    if (rawData?.database_results?.select_employees_0) {
      return rawData;
    }

    let employeeData = [];

    if (rawData?.data?.database_results?.select_employees_0) {
      employeeData = rawData.data.database_results.select_employees_0.data || [];
    } else if (rawData && Array.isArray(rawData.data)) {
      employeeData = rawData.data;
    } else if (rawData && Array.isArray(rawData)) {
      employeeData = rawData;
    } else {
      console.warn("Unknown data structure, returning empty array");
      employeeData = [];
    }

    console.log("Normalized employee data:", employeeData);

    return {
      database_results: {
        select_employees_0: {
          data: employeeData,
        },
      },
    };
  }

  async generateLayoutWithLLM(actualData, query) {
    const employees = actualData.database_results?.select_employees_0?.data || [];
    
    const prompt = `You are an expert UI/UX designer for HR systems. Design the complete user interface for this query.

QUERY: "${query}"
DATA: ${employees.length} employees
SAMPLE: ${JSON.stringify(employees.slice(0, 1), null, 2)}

AVAILABLE COMPONENTS:
Data Display: Card, Table, Avatar, Badge, Progress, Chart, Tabs, Accordion
Interaction: Button, Input, Select, Form, Dialog, Sheet, Drawer
Navigation: Breadcrumb, Pagination, Menubar, Sidebar
Feedback: Alert, Toast, Tooltip, Skeleton
Layout: Separator, ScrollArea, AspectRatio, Resizable

DESIGN COMPLETE UI LAYOUT:
1. Analyze user intent and data context
2. Choose optimal component hierarchy
3. Design responsive layout structure
4. Define component properties and styling
5. Create intuitive user flow

RESPOND WITH COMPLETE JSON:
{
  "analysis": {
    "intent": "user goal",
    "dataType": "single/multiple/analytics",
    "priority": "what user needs most"
  },
  "layout": {
    "type": "grid/dashboard/list/form",
    "columns": 1-4,
    "spacing": "tight/normal/loose",
    "responsive": true/false
  },
  "components": [
    {
      "type": "ui_component_name",
      "title": "display title",
      "dataField": "data path",
      "props": {"variant": "style", "size": "md"},
      "position": {"row": 1, "col": 1, "span": 2},
      "priority": "primary/secondary/tertiary"
    }
  ],
  "interactions": [
    {
      "trigger": "click/hover/input",
      "action": "navigate/filter/sort/edit",
      "target": "component_id"
    }
  ],
  "styling": {
    "theme": "professional/modern/minimal",
    "colors": ["primary", "secondary"],
    "emphasis": "data/actions/status"
  },
  "reasoning": "detailed explanation of design decisions"
}`;

    try {
      const response = await fetch(this.modelEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "qwen2-500m-instruct",
          messages: [{ role: "user", content: prompt }],
          max_tokens: 500,
          temperature: 0.4
        })
      });
      
      const result = await response.json();
      const llmResponse = result.choices[0].message.content;
      
      console.log('Complete LLM UI Design:', llmResponse);
      
      return this.buildCompleteUIFromLLM(llmResponse, employees, query);
    } catch (error) {
      console.log('LLM failed, using minimal fallback');
      return this.buildMinimalFallback(employees, query);
    }
  }

  buildCompleteUIFromLLM(llmResponse, employees, query) {
    let uiDesign;
    
    try {
      uiDesign = JSON.parse(llmResponse);
    } catch (error) {
      console.log('Parsing LLM text response');
      uiDesign = this.extractUIFromText(llmResponse);
    }
    
    console.log('Complete UI Design:', uiDesign);
    
    return this.implementLLMDesign(uiDesign, employees, query);
  }
  
  extractUIFromText(text) {
    const lowerText = text.toLowerCase();
    
    // Extract components mentioned in text
    const components = [];
    const componentTypes = ['card', 'table', 'chart', 'badge', 'progress', 'avatar', 'alert', 'tabs', 'form', 'button'];
    
    componentTypes.forEach((type, index) => {
      if (lowerText.includes(type)) {
        components.push({
          type: `ui_${type}`,
          title: this.getTitleFromQuery(text),
          dataField: type === 'card' ? "database_results.select_employees_0.data[0]" : "database_results.select_employees_0.data",
          props: { variant: 'default' },
          position: { row: Math.floor(index / 2) + 1, col: (index % 2) + 1, span: type === 'table' ? 2 : 1 },
          priority: index === 0 ? 'primary' : 'secondary'
        });
      }
    });
    
    return {
      analysis: { intent: 'display', dataType: 'multiple', priority: 'data' },
      layout: { type: 'grid', columns: 2, spacing: 'normal', responsive: true },
      components: components.length > 0 ? components : [{
        type: 'ui_table',
        title: this.getTitleFromQuery(text),
        dataField: "database_results.select_employees_0.data",
        props: { variant: 'default' },
        position: { row: 1, col: 1, span: 2 },
        priority: 'primary'
      }],
      interactions: [],
      styling: { theme: 'professional', colors: ['primary'], emphasis: 'data' },
      reasoning: 'Extracted from text response'
    };
  }
  
  implementLLMDesign(design, employees, query) {
    const components = design.components?.map(comp => ({
      type: comp.type,
      title: comp.title,
      dataField: comp.dataField,
      uiComponent: this.mapToUIComponent(comp.type),
      props: comp.props || {},
      style: this.convertPositionToStyle(comp.position, design.layout),
      priority: comp.priority,
      llmGenerated: true
    })) || [];
    
    // Add interactions as metadata
    const interactions = design.interactions || [];
    
    return {
      layout: {
        type: design.layout?.type || 'responsive_grid',
        columns: design.layout?.columns || 2,
        spacing: design.layout?.spacing || 'normal',
        responsive: design.layout?.responsive !== false,
        components,
        interactions,
        styling: design.styling,
        llmAnalysis: design.analysis,
        llmReasoning: design.reasoning
      },
      dataMapping: this.getStandardMapping()
    };
  }
  
  mapToUIComponent(type) {
    const mapping = {
      'ui_card': 'Card',
      'ui_table': 'Table', 
      'ui_chart': 'Chart',
      'ui_badge': 'Badge',
      'ui_progress': 'Progress',
      'ui_avatar': 'Avatar',
      'ui_alert': 'Alert',
      'ui_tabs': 'Tabs',
      'ui_form': 'Form',
      'ui_button': 'Button',
      'ui_input': 'Input',
      'ui_skeleton': 'Skeleton'
    };
    return mapping[type] || 'Table';
  }
  
  convertPositionToStyle(position, layout) {
    if (!position) return { gridColumn: 'span 2' };
    
    const { row, col, span } = position;
    return {
      gridRow: row || 1,
      gridColumn: span ? `span ${span}` : col || 1,
      order: (row - 1) * (layout?.columns || 2) + (col - 1)
    };
  }
  
  buildMinimalFallback(employees, query) {
    return {
      layout: {
        type: 'responsive_grid',
        columns: 2,
        components: [{
          type: 'ui_table',
          title: this.getTitleFromQuery(query),
          dataField: 'database_results.select_employees_0.data',
          uiComponent: 'Table',
          style: { gridColumn: 'span 2' },
          priority: 'primary',
          llmGenerated: false
        }],
        llmReasoning: 'Fallback: LLM unavailable'
      },
      dataMapping: this.getStandardMapping()
    };
  }
  
  getTitleFromQuery(query) {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('active')) return 'Active Employees';
    if (lowerQuery.includes('freepool')) return 'Freepool Employees';
    if (lowerQuery.includes('all')) return 'All Employees';
    if (lowerQuery.includes('profile')) return 'Employee Profile';
    if (lowerQuery.includes('analytics')) return 'Employee Analytics';
    if (lowerQuery.includes('report')) return 'Employee Report';
    return 'Employee Search Results';
  }



  getStandardMapping() {
    return {
      employee_id: "Employee ID",
      first_name: "First Name",
      last_name: "Last Name",
      email: "Email",
      phone: "Phone",
      date_of_joining: "Join Date",
      employee_status: "Status"
    };
  }
}

export default new QwenFormatter();