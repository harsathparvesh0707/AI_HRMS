const searchApi = {
  async search(query) {
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
    
    return await response.json();
  }
};

export default searchApi;