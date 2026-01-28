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