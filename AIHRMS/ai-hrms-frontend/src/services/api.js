import axios from 'axios'
const BASE_URL = import.meta.env.VITE_API_BASE_URL;


export async function searchAPI(query) {
    const response = await fetch(`${BASE_URL}/search-rank`, 
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query : query }),
    });
     
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
     return response.json();
  }


export async function uploadAPI(formData) {
  console.log(formData)
  const response = await fetch(`${BASE_URL}/upload/hrms-data`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      return response.json();
}

export async function getProjectDistributions() {
  const response = await  axios.get (`${BASE_URL}/dashboard/project_distribution`);
  return response.data;
}

export async function getAvailableEmployees(monthThreshold = 10) {
  const response = await axios.get(`${BASE_URL}/available_employees?month_threshold=${monthThreshold}`);
  return response.data;
}

