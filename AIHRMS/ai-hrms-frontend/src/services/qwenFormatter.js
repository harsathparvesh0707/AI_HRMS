import searchApi from './searchApi.js';

class QwenFormatter {
  constructor() {
    this.modelEndpoint = "http://172.25.243.122:1234/v1/chat/completions";
    this.cache = new Map();
    this.systemPrompt = `You are a specialized UI layout generator for HR management systems. Your ONLY task is to create JSON layouts that map directly to the provided employee data.

CRITICAL RULES:
1. For DATA TABLE components (employee lists), ALWAYS set "gridColumn": "span 2" to make them full width
2. For single employee PROFILE CARDS, use "gridColumn": "span 1" or "span 2" based on content
3. HEADER components should always be "span 2"

DATA TABLE LAYOUT REQUIREMENTS:
- data_table components MUST have: "style": {"gridColumn": "span 2"}
- This ensures tables use the full container width
- Header above table should also be "span 2"

OUTPUT FORMAT:
{
  "layout": {
    "type": "responsive_grid", 
    "columns": 2,
    "gap": "20px",
    "components": [
      {
        "type": "header",
        "title": "Employee List",
        "subtitle": "Showing all employees", 
        "style": {"gridColumn": "span 2"}
      },
      {
        "type": "data_table",
        "title": "Employee List",
        "dataField": "database_results.select_employees_0.data",
        "style": {"gridColumn": "span 2"}  // <-- CRITICAL: This makes table full width
      }
    ]
  },
  "dataMapping": {
    "employee_id": "Employee ID",
    "first_name": "First Name", 
    "last_name": "Last Name",
    "email": "Email",
    "phone": "Phone",
    "date_of_joining": "Join Date", 
    "employee_status": "Status"
  }
}

IMPORTANT: All data_table components MUST have "gridColumn": "span 2" for full width display.`;
  }

   // PROMPT BUILDING METHODS
  buildStrictLayoutPrompt(actualData, dataAnalysis, context) {
    const itemCount = dataAnalysis.itemCount;
    
    return `
ANALYZE THIS EMPLOYEE DATA AND CREATE APPROPRIATE UI COMPONENTS:

EMPLOYEE DATA:
${JSON.stringify(actualData, null, 2)}

DATA ANALYSIS:
- Number of employees found: ${itemCount}
- User query: "${context}"
- Data fields available: ${dataAnalysis.fields.join(', ')}

CREATE A DYNAMIC UI LAYOUT THAT:
${itemCount === 1 ? 
  '• Shows a detailed employee profile with all information\n' +
  '• Includes action buttons for user interactions\n' +
  '• Provides a clean, organized profile view' :
  '• Displays employees in a comprehensive table\n' + 
  '• Shows summary metrics about the team\n' +
  '• Includes bulk action options'
}

GENERATE THE UI COMPONENTS NOW:`;
  }

  buildMockDataPrompt(query) {
    return `Generate realistic HR system mock data for query: "${query}"`;
  }

  // Then use it in your methods:
  // async generateDynamicLayoutWithLLM(actualData, context) {
  //   try {
  //     const dataAnalysis = this.analyzeDataStructure(actualData);
  //     const prompt = this.buildStrictLayoutPrompt(actualData, dataAnalysis, context);
      
  //     // ... rest of the method
  //   } catch (error) {
  //     // ... error handling
  //   }
  // }

  async generateDynamicLayoutWithLLM(actualData, context) {
    try {
      // First analyze the data to determine layout type
      const dataAnalysis = this.analyzeDataStructure(actualData);
      console.log("Data analysis for layout:", dataAnalysis);

      const prompt = this.buildStrictLayoutPrompt(actualData, dataAnalysis, context);

      console.log("Sending structured prompt to LLM");
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
          max_tokens: 1500,
          temperature: 0.1, // Very low temperature for consistent output
        }),
      });

      if (!response.ok) {
        throw new Error(`LLM API error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("LLM Raw Response:", result.choices[0].message.content);

      const layout = this.parseLayoutResponse(result.choices[0].message.content);
      
      // Validate and fix the layout if needed
      return this.validateAndFixLayout(layout, dataAnalysis);
    } catch (error) {
      console.error("LLM layout generation error:", error);
      return this.generateAutoLayout(this.analyzeDataStructure(actualData), context);
    }
  }

  buildStrictLayoutPrompt(actualData, dataAnalysis, context) {
    const itemCount = dataAnalysis.itemCount;
    const layoutType = itemCount === 1 ? 'employee_profile' : 'employee_list';
    
    return `
ACTUAL EMPLOYEE DATA RECEIVED:
${JSON.stringify(actualData, null, 2)}

DATA ANALYSIS:
- Number of employees: ${itemCount}
- Required layout type: ${layoutType}
- User query: "${context}"

CREATE A ${layoutType.toUpperCase()} LAYOUT:

${itemCount === 1 ? 
`SINGLE EMPLOYEE PROFILE CARD REQUIRED:
- Use "profile_card" component with dataField: "database_results.select_employees_0.data[0]"
- Include all employee fields in the card` : 
`MULTIPLE EMPLOYEES TABLE REQUIRED:
- Use "data_table" component with dataField: "database_results.select_employees_0.data" 
- Show all employees in a table format`}

RETURN THE JSON LAYOUT NOW:`;
  }

  validateAndFixLayout(layout, dataAnalysis) {
    // Ensure dataMapping is correct
    const requiredMapping = {
      "employee_id": "Employee ID",
      "first_name": "First Name", 
      "last_name": "Last Name",
      "email": "Email",
      "phone": "Phone", 
      "date_of_joining": "Join Date",
      "employee_status": "Status"
    };

    if (!layout.dataMapping) {
      layout.dataMapping = {};
    }

    // Merge with required mapping
    layout.dataMapping = { ...requiredMapping, ...layout.dataMapping };

    // Ensure correct dataField paths based on item count
    const correctDataField = dataAnalysis.itemCount === 1 ? 
      "database_results.select_employees_0.data[0]" : 
      "database_results.select_employees_0.data";

    // Fix dataField in components
    if (layout.layout && layout.layout.components) {
      layout.layout.components.forEach(component => {
        // Add dataField if missing
        if (!component.dataField) {
          component.dataField = correctDataField;
        }
        // Fix existing dataField if it contains database_results
        if (component.dataField && component.dataField.includes('database_results')) {
          component.dataField = correctDataField;
        }
      });
    }

    console.log('Fixed layout:', layout);
    return layout;
  }

  analyzeDataStructure(data) {
    const analysis = {
      dataType: 'employee',
      hasList: false,
      hasSingleItem: false,
      itemCount: 0,
      fields: ['employee_id', 'first_name', 'last_name', 'email', 'phone', 'date_of_joining', 'employee_status'],
      layoutType: 'unknown'
    };

    try {
      if (data.database_results && data.database_results.select_employees_0) {
        const resultData = data.database_results.select_employees_0.data;
        
        if (Array.isArray(resultData)) {
          analysis.itemCount = resultData.length;
          analysis.hasList = true;
          analysis.hasSingleItem = resultData.length === 1;
          analysis.layoutType = resultData.length === 1 ? 'employee_profile' : 'employee_list';
        }
      }
      
      return analysis;
    } catch (error) {
      console.error("Data analysis error:", error);
      return analysis;
    }
  }

  async searchAndGenerateLayout(query) {
    try {
      console.log("Searching API for query:", query);

      const rawSearchData = await searchApi.search(query);
      console.log("Raw Search API Response:", rawSearchData);
      
      // Normalize the data structure
      const normalizedData = this.normalizeSearchData(rawSearchData);
      console.log("Normalized data:", normalizedData);

      const layout = await this.generateDynamicLayoutWithLLM(normalizedData, query);
      return { data: normalizedData, layout };
    } catch (error) {
      console.error("Search and layout generation failed:", error);
      const mockData = await this.generateMockDataWithLLM(query);
      const layout = await this.generateDynamicLayoutWithLLM(mockData, query);
      return { data: mockData, layout };
    }
  }

  // In QwenFormatter - update the normalizeSearchData method
normalizeSearchData(rawData) {
  console.log("Normalizing search data - RAW:", rawData);
  
  // If data is already in the expected format
  if (rawData && rawData.database_results && rawData.database_results.select_employees_0) {
    return rawData;
  }
  
  let employeeData = [];
  
  // Check for the actual API response structure from your screenshot
  if (rawData && rawData.data && rawData.data.database_results && rawData.data.database_results.select_employees_0) {
    employeeData = rawData.data.database_results.select_employees_0.data || [];
  } 
  // If data is directly in the response
  else if (rawData && Array.isArray(rawData.data)) {
    employeeData = rawData.data;
  }
  // If it's a different structure
  else if (rawData && Array.isArray(rawData)) {
    employeeData = rawData;
  }
  // If no data found
  else {
    console.warn("Unknown data structure, returning empty array");
    employeeData = [];
  }
  
  console.log("Normalized employee data:", employeeData);
  
  // Return the structure that DynamicUIComponent expects
  return {
    database_results: {
      select_employees_0: {
        data: employeeData
      }
    }
  };
}

  async generateMockDataWithLLM(query) {
    try {
      const prompt = `Generate realistic HR system mock data for query: "${query}"`;

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
      return this.parseMockDataResponse(result.choices[0].message.content) || this.generateStructuredMockData(query);
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

  parseLayoutResponse(response) {
    try {
      let cleanedResponse = response.replace(/```json\n?|\n?```/g, "").trim();
      
      // Fix common JSON issues from LLM
      cleanedResponse = cleanedResponse
        .replace(/dataField:/g, '"dataField":')
        .replace(/([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*):/g, '$1"$2":')
        .replace(/:\s*([a-zA-Z_][a-zA-Z0-9_]*)(\s*[,}])/g, ': "$1"$2');
      
      const jsonMatch = cleanedResponse.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const layout = JSON.parse(jsonMatch[0]);
        console.log("Successfully parsed LLM layout:", layout);
        return layout;
      }
      throw new Error("No valid JSON found in LLM response");
    } catch (error) {
      console.error("Failed to parse LLM layout response:", error);
      console.log("Raw response:", response);
      return this.fallbackLayout();
    }
  }

  generateStructuredMockData(query) {
    return {
      database_results: {
        select_employees_0: {
          data: [
            {
              employee_id: 1,
              first_name: "John",
              last_name: "Doe",
              email: "john@company.com",
              phone: "+1234567890",
              date_of_joining: "2023-01-15",
              employee_status: "Active"
            }
          ]
        }
      }
    };
  }

  generateAutoLayout(dataAnalysis, context) {
    const isProfile = dataAnalysis.itemCount === 1;
    
    return {
      layout: {
        type: "responsive_grid",
        columns: 2,
        gap: "20px",
        components: [
          {
            type: "header",
            title: isProfile ? "Employee Profile" : `Employee List (${dataAnalysis.itemCount})`,
            subtitle: context,
            style: { gridColumn: "span 2" }
          },
          {
            type: isProfile ? "profile_card" : "data_table",
            title: "Employee Details",
            dataField: isProfile ? "database_results.select_employees_0.data[0]" : "database_results.select_employees_0.data",
            style: { gridColumn: "span 2" }
          }
        ]
      },
      dataMapping: {
        "employee_id": "Employee ID",
        "first_name": "First Name",
        "last_name": "Last Name",
        "email": "Email",
        "phone": "Phone",
        "date_of_joining": "Join Date",
        "employee_status": "Status"
      }
    };
  }

  fallbackLayout() {
    return {
      layout: {
        type: "responsive_grid",
        columns: 2,
        gap: "20px",
        components: [
          {
            type: "header",
            title: "HR System Data",
            subtitle: "No data available",
            style: { gridColumn: "span 2" }
          }
        ]
      },
      dataMapping: {}
    };
  }
}

export default new QwenFormatter();