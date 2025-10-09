class QwenFormatter {
  constructor() {
    this.modelEndpoint = 'http://172.25.243.122:1234/v1/chat/completions';
  }

  async formatResponse(jsonData, context = 'dashboard') {
    try {
      const prompt = this.buildPrompt(jsonData, context);
      
      const response = await fetch(this.modelEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'qwen2-500m-instruct',
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 500,
          temperature: 0.3,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return this.parseFormattedResponse(result.choices[0].message.content);
    } catch (error) {
      console.error('Qwen formatting error:', error);
      return this.fallbackFormat(jsonData);
    }
  }

  buildPrompt(jsonData, context) {
    return `Format this JSON data for ${context} display. Make it user-friendly and readable:

JSON Data: ${JSON.stringify(jsonData, null, 2)}

Instructions:
- Convert technical field names to readable labels
- Format numbers with appropriate units
- Structure data for easy consumption
- Return only the formatted JSON, no explanations

Formatted JSON:`;
  }

  parseFormattedResponse(response) {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      return JSON.parse(response);
    } catch (error) {
      console.error('Failed to parse Qwen response:', error);
      return null;
    }
  }

  fallbackFormat(jsonData) {
    if (Array.isArray(jsonData)) {
      return jsonData.map(item => this.formatObject(item));
    }
    return this.formatObject(jsonData);
  }

  formatObject(obj) {
    const formatted = {};
    for (const [key, value] of Object.entries(obj)) {
      const readableKey = key.replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .replace(/_/g, ' ');
      formatted[readableKey] = value;
    }
    return formatted;
  }
}

export default new QwenFormatter();