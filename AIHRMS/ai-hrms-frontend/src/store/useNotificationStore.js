import { create } from "zustand";
import {
  AlertTriangle,
  UserPlus,
  UserMinus,
  Briefcase,
} from "lucide-react";

const ICON_MAP = {
  project: AlertTriangle,
  employee_add: UserPlus,
  employee_remove: UserMinus,
  new_project: Briefcase,
};

export const useNotificationStore = create((set, get) => ({
  socket: null,
  notifications: [],
  connected: false,

  connect: () => {
    // ⛔ prevent multiple connections
    if (get().socket) return;

    const API_BASE = import.meta.env.VITE_API_BASE_URL;
    const WS_BASE = API_BASE.replace("http", "ws");
    const WS_URL = `${WS_BASE}/ws/notification`;


//  console.log("🔌 CONNECTING TO WS:", WS_URL);
    const socket = new WebSocket(WS_URL);

    

    socket.onopen = () => {
      console.log("🟢 Notification socket connected");
      set({ connected: true, socket });

      socket.send(
    JSON.stringify({
      type: "hello",
      source: "frontend",
    })
  );
  console.log("👋 hello sent");
    };

//     setTimeout(() => {
//   set((state) => ({
//     notifications: [
//       {
//         title: "Test Notification",
//         message: "WebSocket is working 🎉",
//         priority: "success",
//         time: "Just now",
//         icon: AlertTriangle,
//       },
//       ...state.notifications,
//     ],
//   }));
// }, 2000);


    socket.onmessage = (event) => {
      // const data = JSON.parse(event.data);
      // console.log("MESSAGE:", data)
      console.log("MESSAGE:", event.data)
 let data;
  try {
    data = JSON.parse(event.data);
  } catch {
    console.warn("⚠️ Non-JSON message received");
    return;
  }

  console.log("📦 PARSED MESSAGE:", data);

  set((state) => ({
    notifications: [
      {
        ...data,
        icon: ICON_MAP[data.type] || AlertTriangle,
      },
      ...state.notifications,
    ],
  }));
    };

    socket.onerror = (err) => {
      console.error("🔴 WebSocket error", err);
    };

    socket.onclose = (event) => {
      // console.log("⚠️ Notification socket closed");
       console.log("🔌 WS CLOSED", {
    code: event.code,
    reason: event.reason,
    wasClean: event.wasClean,
  });
      set({ socket: null, connected: false });
    };

    set({ socket });
  },

  disconnect: () => {
    const socket = get().socket;
    socket?.close();
    set({ socket: null, connected: false });
  },

  clearNotifications: () => set({ notifications: [] }),
}));
