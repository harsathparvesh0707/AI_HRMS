const searchApi = {
  async search(query) {
    console.log('SearchAPI: Sending query:', query);
    
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
    console.log('SearchAPI: Received response:', data);
    return data;
  }
};

export default searchApi;