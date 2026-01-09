const searchApi = {
  async search(query) {
    const response = await fetch('http://localhost:8000/search-rank', {
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
    return data;
  }
};

export default searchApi;