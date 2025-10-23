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
    const lowerQuery = query.toLowerCase();
    
    // Simple rule-based layout generation
    if (lowerQuery.includes('all') && employees.length > 10) {
      return {
        layout: {
          type: "responsive_grid",
          columns: 2,
          components: [
            { type: "metrics_grid", title: "Employee Overview", dataField: "database_results.select_employees_0.data", style: { gridColumn: "span 2" } },
            { type: "data_table", title: "All Employees", dataField: "database_results.select_employees_0.data", style: { gridColumn: "span 2" } }
          ]
        },
        dataMapping: this.getStandardMapping()
      };
    }
    
    const componentType = employees.length === 1 ? 'profile_card' : 'data_table';
    const title = employees.length === 1 ? "Employee Details" : this.getTitleFromQuery(query);
    
    return {
      layout: {
        type: "responsive_grid",
        columns: 2,
        components: [{
          type: componentType,
          title: title,
          dataField: employees.length === 1 ? "database_results.select_employees_0.data[0]" : "database_results.select_employees_0.data",
          style: { gridColumn: "span 2" }
        }]
      },
      dataMapping: this.getStandardMapping()
    };
  }
  
  getTitleFromQuery(query) {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('active')) return 'Active Employees';
    if (lowerQuery.includes('freepool')) return 'Freepool Employees';
    if (lowerQuery.includes('all')) return 'All Employees';
    return 'Employee List';
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