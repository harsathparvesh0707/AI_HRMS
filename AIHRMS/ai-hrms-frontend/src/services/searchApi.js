import mockData from './mockData.json';

const searchApi = {
  async search(query) {
    // console.log('SearchAPI: Sending query:', query);
    
    // Check if this is a project requirement query
    const projectKeywords = ['project requirement', 'project need', 'need for project', 'requirement for', 'angular developer', 'frontend developer'];
    const isProjectQuery = projectKeywords.some(keyword => 
      query.toLowerCase().includes(keyword.toLowerCase())
    );
    
    if (isProjectQuery) {
      // Return mock data for project requirement searches
      return {
        data: {
          database_results: {
            select_employees_0: {
              data: mockData.all_employees
            }
          }
        }
      };
    }
    
    const response = await fetch('http://172.25.247.12:8000/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query : query }),
    });
     
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    // console.log('SearchAPI: Received response:', data);
    return data;
  }
};

export default searchApi;