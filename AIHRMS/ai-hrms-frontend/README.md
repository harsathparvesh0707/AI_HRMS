# 🚀 AI-Driven HRMS Dashboard

<div align="center">

![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-7-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A next-generation Human Resources Management System (HRMS) with AI-powered chat assistant, dynamic dashboards, and beautiful animations.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Screenshots](#-preview)

</div>

---

## ✨ Features

### 🤖 AI-Powered Assistant
- **Conversational Interface**: Chat with an AI assistant to manage HR tasks
- **Dynamic Dashboard Updates**: Cards created and updated based on chat interactions
- **Smart Suggestions**: Quick action buttons for common tasks
- **Message Streaming**: Real-time typing indicators and response streaming

### 📊 Dynamic Dashboard
- **Modular Card System**: Attendance, leave balance, performance charts, announcements
- **Drag & Drop**: Reorder cards with smooth animations
- **Pin Important Cards**: Keep frequently accessed information at the top
- **Real-time Updates**: Dashboard reflects changes instantly
- **Responsive Grid**: Adaptive layout for all screen sizes

### 🎨 Premium UI/UX
- **Glassmorphism**: Modern translucent UI elements
- **Dark/Light Theme**: Seamless theme switching with persistence
- **Smooth Animations**: Framer Motion powered transitions
- **Micro-interactions**: Hover effects, scale animations, pulse effects
- **Custom Components**: Beautifully designed cards and controls

### 📈 Data Visualizations
- **Line Charts**: Track performance trends
- **Circular Progress**: Attendance visualization
- **Bar Charts**: Leave balance tracking
- **Responsive Charts**: Built with Recharts

### 🔧 Developer Experience
- **TypeScript Ready**: Easy migration to TypeScript
- **Component Based**: Modular, reusable components
- **State Management**: Zustand with localStorage persistence
- **Hot Module Replacement**: Instant updates during development

---

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm/yarn
- Modern web browser

### Installation

```bash
# Clone or navigate to the project
cd ai-hrms-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at **http://localhost:5173**

### Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

---

## 📁 Project Structure

```
ai-hrms-frontend/
├── src/
│   ├── components/           # React components
│   │   ├── Header.jsx       # Top navigation with theme toggle
│   │   ├── DashboardGrid.jsx # Main dashboard container
│   │   ├── DashboardCard.jsx # Individual card component
│   │   └── ChatPanel.jsx    # AI chat interface
│   ├── store/
│   │   └── useStore.js      # Zustand state management
│   ├── App.jsx              # Main app component
│   ├── main.jsx             # React entry point
│   └── index.css            # Global styles + Tailwind
├── public/                  # Static assets
├── tailwind.config.js       # Tailwind configuration
├── vite.config.js           # Vite configuration
├── PROJECT_GUIDE.md         # Detailed implementation guide
└── BACKEND_API_EXAMPLE.md   # Backend integration examples
```

---

## 🎯 Key Components

### Dashboard Cards

Cards are the building blocks of the dashboard. Each card displays specific HR data:

- **Attendance Card**: Circular progress showing hours worked
- **Leave Balance**: Bar chart of available vs. used days
- **Team Performance**: Line chart with monthly metrics
- **Announcements**: Scrollable news feed
- **Custom Cards**: Extensible for new data types

### Chat Assistant

The AI chat panel enables natural language interactions:
- Quick action buttons for common tasks
- Real-time message streaming
- Conversation history
- Context-aware responses

### State Management

Powered by Zustand with localStorage persistence:
- Theme preferences
- Dashboard cards (position, pinned status)
- User profile
- Chat message history

---

## 🎨 Customization

### Adding New Card Types

1. **Update the store** (`src/store/useStore.js`):

```javascript
{
  id: 'new-card',
  title: 'New Card',
  type: 'custom-type',
  pinned: false,
  data: { /* your data structure */ }
}
```

2. **Add rendering logic** (`src/components/DashboardCard.jsx`):

```javascript
case 'custom-type':
  return (
    <div className="p-4">
      {/* Your custom UI */}
    </div>
  );
```

### Theme Customization

Edit `tailwind.config.js`:

```javascript
colors: {
  primary: {
    500: '#your-color',
    // ... other shades
  },
}
```

### Connecting to Backend

See `BACKEND_API_EXAMPLE.md` for complete integration examples with:
- REST APIs
- WebSocket (Socket.io)
- OpenAI integration
- Database schemas
- Authentication

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool & dev server |
| **Tailwind CSS** | Utility-first styling |
| **Framer Motion** | Animation library |
| **Recharts** | Data visualization |
| **Zustand** | State management |
| **@dnd-kit** | Drag and drop |
| **Lucide React** | Icon library |
| **Socket.io** | Real-time communication (ready) |

---

## 📱 Responsive Design

The app is fully responsive with breakpoints:

- **Mobile**: < 768px (stacked layout)
- **Tablet**: 768px - 1024px (2-column grid)
- **Desktop**: > 1024px (4-column grid)
- **Chat Panel**: Collapses to bottom sheet on mobile

---

## 🔒 Security Best Practices

When deploying to production:

1. **Environment Variables**: Use `.env` for API keys
2. **HTTPS**: Always use secure connections
3. **Authentication**: Implement JWT or session-based auth
4. **Input Validation**: Sanitize all user inputs
5. **Rate Limiting**: Prevent API abuse
6. **CORS**: Configure appropriate policies

---

## 📚 Documentation

- **[PROJECT_GUIDE.md](PROJECT_GUIDE.md)**: Comprehensive implementation guide
- **[BACKEND_API_EXAMPLE.md](BACKEND_API_EXAMPLE.md)**: Backend integration examples
- **Component Docs**: Inline comments in each component

---

## 🎥 Preview

### Light Mode
- Clean, professional interface
- Soft gradients and shadows
- High contrast for readability

### Dark Mode
- Easy on the eyes
- Modern glassmorphism effects
- Consistent color scheme

### Features in Action
- ✅ Drag and drop card reordering
- ✅ Smooth theme transitions
- ✅ Real-time chat interactions
- ✅ Animated card creation/removal
- ✅ Pinned cards stay at top
- ✅ Responsive on all devices

---

## 🚧 Roadmap

- [ ] Backend API integration (LLM + Database)
- [ ] Voice input for chat
- [ ] Advanced analytics dashboards
- [ ] Calendar integration
- [ ] Team collaboration features
- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Desktop app (Electron)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style
4. Write clear commit messages
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - feel free to use it in your own projects!

---

## 🙏 Acknowledgments

Built with modern web technologies:
- React Team for the amazing framework
- Tailwind CSS for utility-first styling
- Framer Motion for beautiful animations
- All open-source contributors

---

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Check existing documentation
- Review the example implementations

---

<div align="center">

**Built with ❤️ using React, Tailwind CSS, and modern web technologies**

⭐ Star this repo if you find it useful!

</div>
