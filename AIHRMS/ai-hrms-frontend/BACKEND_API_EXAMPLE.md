# Backend API Integration Example

This document provides example implementations for connecting the AI HRMS frontend to a backend API with LLM integration.

## API Endpoints Structure

```
POST /api/chat/message
POST /api/cards/create
POST /api/cards/update/:id
DELETE /api/cards/delete/:id
GET /api/user/profile
GET /api/dashboard/data
```

## Example Node.js/Express Backend

### Setup

```bash
npm init -y
npm install express cors body-parser openai socket.io
```

### Basic Server (server.js)

```javascript
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { OpenAI } = require('openai');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: 'http://localhost:5173',
    methods: ['GET', 'POST'],
  },
});

app.use(cors());
app.use(bodyParser.json());

// Initialize OpenAI (or any other LLM)
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Chat endpoint
app.post('/api/chat/message', async (req, res) => {
  try {
    const { message, conversationHistory } = req.body;

    // System prompt for HR assistant
    const systemPrompt = `You are an AI HR assistant. You help users manage their HR tasks.

When users ask for dashboard updates, respond with JSON in this format:
{
  "message": "Your response to the user",
  "action": "create_card" | "update_card" | "delete_card" | null,
  "cardData": {
    "id": "unique-id",
    "title": "Card Title",
    "type": "attendance" | "leave" | "chart" | "announcements" | "custom",
    "pinned": false,
    "data": { /* type-specific data */ }
  }
}

Examples:
- User: "Show my attendance"
  Response: Create an attendance card
- User: "What's my leave balance?"
  Response: Create a leave balance card
- User: "Show team performance"
  Response: Create a chart card with performance data
`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: systemPrompt },
        ...conversationHistory,
        { role: 'user', content: message },
      ],
    });

    const aiResponse = completion.choices[0].message.content;

    // Try to parse if JSON response
    try {
      const parsed = JSON.parse(aiResponse);
      res.json(parsed);
    } catch {
      // Plain text response
      res.json({
        message: aiResponse,
        action: null,
      });
    }
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({ error: 'Failed to process message' });
  }
});

// WebSocket for real-time chat
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('chat_message', async (data) => {
    try {
      const { message, conversationHistory } = data;

      // Stream response
      const stream = await openai.chat.completions.create({
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are an AI HR assistant...' },
          ...conversationHistory,
          { role: 'user', content: message },
        ],
        stream: true,
      });

      let fullResponse = '';

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || '';
        fullResponse += content;

        // Emit each chunk
        socket.emit('chat_chunk', { content });
      }

      // Emit completion
      socket.emit('chat_complete', { fullResponse });
    } catch (error) {
      socket.emit('chat_error', { error: error.message });
    }
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Frontend Integration

### Update ChatPanel.jsx

```javascript
// Add at the top
import io from 'socket.io-client';

// Inside component
const [socket, setSocket] = useState(null);
const [streamingMessage, setStreamingMessage] = useState('');

useEffect(() => {
  // Connect to WebSocket
  const newSocket = io('http://localhost:3000');
  setSocket(newSocket);

  // Listen for message chunks
  newSocket.on('chat_chunk', (data) => {
    setStreamingMessage((prev) => prev + data.content);
  });

  // Listen for completion
  newSocket.on('chat_complete', (data) => {
    addMessage({
      role: 'assistant',
      content: data.fullResponse,
    });
    setStreamingMessage('');
    setTyping(false);
  });

  return () => newSocket.close();
}, []);

const handleSend = async () => {
  if (!inputValue.trim()) return;

  const userMessage = {
    role: 'user',
    content: inputValue,
  };

  addMessage(userMessage);
  setInputValue('');
  setTyping(true);

  // Option 1: REST API
  try {
    const response = await fetch('http://localhost:3000/api/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: inputValue,
        conversationHistory: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      }),
    });

    const data = await response.json();

    addMessage({
      role: 'assistant',
      content: data.message,
    });

    // Handle card actions
    if (data.action === 'create_card') {
      addCard(data.cardData);
    } else if (data.action === 'update_card') {
      updateCard(data.cardData.id, data.cardData);
    } else if (data.action === 'delete_card') {
      removeCard(data.cardData.id);
    }

    setTyping(false);
  } catch (error) {
    console.error('Chat error:', error);
    setTyping(false);
  }

  // Option 2: WebSocket (for streaming)
  // socket.emit('chat_message', {
  //   message: inputValue,
  //   conversationHistory: messages,
  // });
};
```

## Example LLM Prompts for Card Creation

### Attendance Card

```
User: "Show my attendance for this month"

LLM Response:
{
  "message": "Here's your attendance record for this month.",
  "action": "create_card",
  "cardData": {
    "id": "attendance-oct-2025",
    "title": "October Attendance",
    "type": "attendance",
    "pinned": false,
    "data": {
      "hoursWorked": 142,
      "totalHours": 160,
      "percentage": 88.75
    }
  }
}
```

### Team Performance Card

```
User: "How is my team performing?"

LLM Response:
{
  "message": "Your team's performance has been excellent! Here's the trend.",
  "action": "create_card",
  "cardData": {
    "id": "team-perf-2025",
    "title": "Team Performance Q4",
    "type": "chart",
    "pinned": true,
    "data": {
      "series": [
        { "month": "Jul", "value": 87 },
        { "month": "Aug", "value": 91 },
        { "month": "Sep", "value": 89 },
        { "month": "Oct", "value": 94 }
      ]
    }
  }
}
```

### Custom Analytics Card

```
User: "Show me the recruitment pipeline"

LLM Response:
{
  "message": "Here's your current recruitment pipeline status.",
  "action": "create_card",
  "cardData": {
    "id": "recruitment-pipeline",
    "title": "Recruitment Pipeline",
    "type": "custom",
    "pinned": false,
    "data": {
      "stages": [
        { "name": "Applied", "count": 45 },
        { "name": "Screening", "count": 23 },
        { "name": "Interview", "count": 12 },
        { "name": "Offer", "count": 5 }
      ]
    }
  }
}
```

## Environment Variables (.env)

```env
OPENAI_API_KEY=your_openai_api_key
PORT=3000
DATABASE_URL=your_database_url
JWT_SECRET=your_jwt_secret
```

## Alternative LLM Providers

### Anthropic Claude

```javascript
const Anthropic = require('@anthropic-ai/sdk');

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const message = await anthropic.messages.create({
  model: 'claude-3-5-sonnet-20241022',
  max_tokens: 1024,
  messages: conversationHistory,
});
```

### Local LLM (Ollama)

```javascript
const response = await fetch('http://localhost:11434/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'llama2',
    messages: conversationHistory,
    stream: false,
  }),
});
```

## Database Schema Example (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(100),
  avatar_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard Cards
CREATE TABLE dashboard_cards (
  id VARCHAR(255) PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  pinned BOOLEAN DEFAULT false,
  data JSONB,
  position INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Messages
CREATE TABLE chat_messages (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Considerations

1. **Authentication**: Implement JWT or session-based auth
2. **Rate Limiting**: Limit API calls to prevent abuse
3. **Input Validation**: Sanitize all user inputs
4. **CORS**: Configure appropriate CORS policies
5. **API Keys**: Never expose API keys in frontend
6. **Data Encryption**: Use HTTPS in production

## Production Deployment

### Frontend (Vercel/Netlify)

```bash
npm run build
# Deploy dist folder
```

### Backend (Railway/Render/AWS)

```bash
# Use PM2 for process management
npm install -g pm2
pm2 start server.js
pm2 save
```

---

This example provides a foundation for integrating the AI HRMS frontend with a backend API and LLM services.
