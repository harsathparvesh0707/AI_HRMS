# AI-Driven HRMS Dashboard

A next-generation Human Resources Management System (HRMS) frontend featuring an AI-powered chat assistant, dynamic dashboard cards, and beautiful animations.

## 🌟 Features

### Core Functionality
- **AI Chat Assistant**: Interactive chat panel with LLM-powered responses
- **Dynamic Dashboard Cards**: Modular, draggable cards that display HR metrics
- **Real-time Updates**: Dashboard updates based on chat interactions
- **Pinned Cards**: Save frequently accessed information
- **Dark/Light Theme**: Seamless theme switching with persistent preferences

### Dashboard Cards
- **Attendance Tracker**: Circular progress visualization
- **Leave Balance**: Bar chart showing available vs. used days
- **Team Performance**: Line chart with monthly metrics
- **Announcements**: Scrolling news feed
- **Extensible**: Easy to add new card types

### UI/UX Features
- **Premium Animations**: Framer Motion powered smooth transitions
- **Glassmorphism Effects**: Modern, translucent UI elements
- **Responsive Design**: Mobile-first, adaptive layouts
- **Custom Scrollbars**: Themed and minimal
- **Micro-interactions**: Hover effects, scale animations

## 🛠️ Tech Stack

- **React 18**: Modern React with hooks
- **Vite**: Lightning-fast build tool
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Advanced animations
- **Recharts**: Beautiful data visualizations
- **Zustand**: Lightweight state management
- **Lucide React**: Clean, consistent icons
- **Socket.io**: WebSocket for real-time chat (ready to integrate)

## 📁 Project Structure

```
src/
├── components/
│   ├── Header.jsx           # Top navigation with theme toggle
│   ├── DashboardGrid.jsx    # Main card container
│   ├── DashboardCard.jsx    # Individual card component
│   └── ChatPanel.jsx        # AI assistant interface
├── store/
│   └── useStore.js          # Zustand state management
├── App.jsx                  # Main application component
├── main.jsx                 # React entry point
└── index.css                # Global styles + Tailwind
```

## 🚀 Getting Started

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development

The app will be available at `http://localhost:5173`

## 🎨 Customization

### Adding New Card Types

Edit `src/store/useStore.js` to add new card definitions:

```javascript
{
  id: 'custom-card',
  title: 'Custom Card',
  type: 'custom',
  pinned: false,
  data: { /* your data */ }
}
```

Then implement the rendering logic in `src/components/DashboardCard.jsx`:

```javascript
case 'custom':
  return (
    <div>Your custom content</div>
  );
```

### Theme Customization

Edit `tailwind.config.js` to customize colors:

```javascript
colors: {
  primary: { /* your color palette */ },
  azure: { /* your color palette */ }
}
```

### Adding AI Backend

To connect to a real LLM backend:

1. Update the `handleSend` function in `src/components/ChatPanel.jsx`
2. Replace the mock response with your API call
3. Implement card creation based on LLM JSON responses

Example integration:

```javascript
const handleSend = async () => {
  const userMessage = { role: 'user', content: inputValue };
  addMessage(userMessage);
  setTyping(true);

  try {
    const response = await fetch('YOUR_API_ENDPOINT', {
      method: 'POST',
      body: JSON.stringify({ message: inputValue }),
    });

    const data = await response.json();

    // Process LLM response
    addMessage({ role: 'assistant', content: data.message });

    // Create cards if instructed
    if (data.createCard) {
      addCard(data.cardData);
    }
  } catch (error) {
    console.error('Chat error:', error);
  } finally {
    setTyping(false);
  }
};
```

## 🎯 Key Components

### State Management

The app uses Zustand with localStorage persistence:
- Theme preferences
- Dashboard cards
- User profile
- Chat messages

### Animation System

Framer Motion provides:
- Page transitions
- Card entrance/exit animations
- Micro-interactions
- Background particle effects

### Responsive Breakpoints

- Mobile: `< 768px`
- Tablet: `768px - 1024px`
- Desktop: `> 1024px`

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:3000
VITE_SOCKET_URL=ws://localhost:3000
```

### Build Settings

Edit `vite.config.js` for custom build configuration.

## 📱 Mobile Experience

The chat panel transforms into a bottom sheet on mobile devices. Dashboard cards stack vertically with touch-friendly controls.

## 🎭 Theme System

Dark mode is controlled via:
1. Zustand store (`theme` state)
2. Tailwind's `dark:` classes
3. CSS custom properties for smooth transitions

## 🚧 Future Enhancements

- Drag-and-drop card reordering
- Voice input for chat
- Real-time notifications
- Multi-language support
- Advanced analytics dashboards
- Calendar integration
- Team collaboration features

## 📄 License

MIT License - feel free to use this in your projects!

## 🤝 Contributing

Contributions welcome! Please follow the existing code style and component patterns.

---

Built with ❤️ using modern web technologies
