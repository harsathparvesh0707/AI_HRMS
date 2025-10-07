import React, { useState, useEffect } from "react";
import GridLayout from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { motion, AnimatePresence } from "framer-motion";
import Masonry from "react-masonry-css";

// import Layout from "@/components/common/Layout";
import Cards from "@/components/common/Cards";
import { TableContent, Projects } from "@/components/common/TableContent";
import Charts from "@/components/common/Charts";
// import Stats from "@/components/common/Stats";
import Candidate from "@/components/common/Candidate";
import DynamicCard from "@/components/common/DynamicCard";
import EmployeeTable from "@/components/features/employee-table";

import { Users, Briefcase, UserMinus, Pin, X, MoreHorizontal } from "lucide-react";
import { fetchDashboardData } from "@/services/dashboardService";
import "@/styles/masonry.css";

const ContentContainer = ({ onShowEmployeeList }) => {
  // === State from first code ===
  const [showEmployeeList, setShowEmployeeList] = useState(null);
  const [showEmployeeTable, setShowEmployeeTable] = useState(false);

  // === State from second code ===
  const [pinned, setPinned] = useState([]);
  const [unpinned, setUnpinned] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [allCards, setAllCards] = useState([]);
  const [showPinLimitModal, setShowPinLimitModal] = useState(false);

  // === Employee Stats (from first code) ===
  const employeeStats = [
    { title: "Total Employees", count: 545, change: +12, trend: "up", icon: <Users className="w-5 h-5 text-gray-500" /> },
    { title: "In Project", count: 480, change: -5, trend: "down", icon: <Briefcase className="w-5 h-5 text-gray-500" /> },
    { title: "Free Pool", count: 65, change: +7, trend: "up", icon: <UserMinus className="w-5 h-5 text-gray-500" /> },
  ];

  // === First Code: listen to global employee events ===
  useEffect(() => {
    const handleShowEmployeeCards = (event) => {
      setShowEmployeeList(event.detail?.filter || "freepool");
      setShowEmployeeTable(false);
    };

    const handleShowEmployeeTable = () => {
      setShowEmployeeTable(true);
      setShowEmployeeList(null);
    };

    window.addEventListener("showEmployeeCards", handleShowEmployeeCards);
    window.addEventListener("showEmployeeTable", handleShowEmployeeTable);

    return () => {
      window.removeEventListener("showEmployeeCards", handleShowEmployeeCards);
      window.removeEventListener("showEmployeeTable", handleShowEmployeeTable);
    };
  }, []);

  useEffect(() => {
    if (onShowEmployeeList) onShowEmployeeList(setShowEmployeeList);
  }, [onShowEmployeeList]);

  // === Second Code: Load dashboard data ===
  useEffect(() => {
    const loadDashboardData = async () => {
      const data = await fetchDashboardData();
      const dynamicCards = [
        { id: "attendance", component: <DynamicCard type="attendance" data={data.attendance} />, header: "Attendance Status" },
        { id: "leaveBalance", component: <DynamicCard type="leave_balance" data={data.leave_balance} />, header: "Leave Balance" },
        { id: "recentProjects", component: <DynamicCard type="recent_projects" data={data.recent_projects} />, header: "Recent Projects" },
        { id: "notifications", component: <DynamicCard type="notifications" data={data.notifications} />, header: "Notifications" },
      ];

      const staticCards = [
        { id: "employeeTable", component: <TableContent />, header: "Employee Table" },
        { id: "upcomingProjects", component: <Projects />, header: "Upcoming Projects" },
        { id: "latestCandidates", component: <Candidate />, header: "Latest Candidates" },
        ...employeeStats.map((stat, index) => ({
          id: `stats-${index}`,
          component: (
            <>
              <div className="mt-3 text-3xl font-bold">{stat.count}</div>
              <div className="flex items-center gap-1 text-sm mt-2">
                <span className={`${stat.trend === "up" ? "text-green-600" : "text-red-600"} font-semibold`}>
                  {stat.trend === "up" ? `↑ ${stat.change}` : `↓ ${Math.abs(stat.change)}`}
                </span>
                <span className="text-gray-500">vs last week</span>
              </div>
              <div className="mt-3 flex items-end gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="w-full rounded bg-green-700" style={{ height: `${Math.random() * 20 + 30}px` }} />
                ))}
              </div>
            </>
          ),
          header: stat.title
        }))
      ];

      setAllCards([...dynamicCards, ...staticCards]);
    };

    loadDashboardData();
  }, []);

  // === Pinned/unpinned logic ===
  useEffect(() => {
    if (allCards.length > 0) {
      const storedPinned = JSON.parse(localStorage.getItem("pinnedCards")) || [];
      const validPinned = storedPinned.filter((id) => allCards.find((c) => c.id === id));
      const storedUnpinned = allCards.map((c) => c.id).filter((id) => !validPinned.includes(id));

      setPinned(validPinned);
      setUnpinned(storedUnpinned);
    }
  }, [allCards]);

  const togglePin = (id) => {
    // Check if the card exists in allCards
    const cardExists = allCards.find(card => card.id === id);
    if (!cardExists) {
      console.warn(`Card with id ${id} not found in allCards`);
      return;
    }

    let newPinned = [...pinned];
    let newUnpinned = [...unpinned];

    if (pinned.includes(id)) {
      newPinned = newPinned.filter((pid) => pid !== id);
      if (!newUnpinned.includes(id)) {
        newUnpinned.unshift(id);
      }
    } else {
      if (pinned.length >= 8) {
        setShowPinLimitModal(true);
        return;
      }
      newPinned.unshift(id);
      newUnpinned = newUnpinned.filter((uid) => uid !== id);
    }

    setPinned(newPinned);
    setUnpinned(newUnpinned);
    localStorage.setItem("pinnedCards", JSON.stringify(newPinned));
  };

  const getCardActions = (id) => (
    <>
      <button onClick={() => togglePin(id)} className="p-1 rounded">
        <Pin className={`w-4 h-4 ${pinned.includes(id) ? "text-blue-600 fill-blue-600" : "text-gray-500"}`} />
      </button>
      <button className="p-1 rounded">
        <MoreHorizontal className="w-5 h-5 text-gray-600" />
      </button>
      <button className="p-1 rounded">
        <X className="w-4 h-4 text-gray-500" />
      </button>
    </>
  );

  const buildLayout = (ids, startY = 0) =>
    ids.map((id, index) => ({
      i: id,
      x: (index % 3) * 4,
      y: startY + Math.floor(index / 3),
      w: 4,
      h: 2,
    }));

  // const breakpointColumnsObj = { default: 3, 1100: 3, 700: 2, 500: 1 };

  return (
    <div className="flex flex-1 p-3">
      <main className="flex-1 bg-neutral-100 drop-shadow-lg p-6 flex rounded-xl overflow-auto flex-col gap-6">
        {showEmployeeTable ? (
          <EmployeeTable />
        ) : showEmployeeList ? (
          <EmployeeTable filter={showEmployeeList} />
        ) : (
          <>
            {/* === PINNED CARDS === */}
            {pinned.length > 0 && (
              <GridLayout
                className="layout bg-blue-50 rounded-lg p-2 min-h-[150px]"
                layout={buildLayout(pinned, 0)}
                cols={12}
                rowHeight={150}
                width={1360}
                isResizable
                isDraggable
              >
                {pinned.map((id) => {
                  const card = allCards.find((c) => c.id === id);
                  if (!card) return null;
                  return (
                    <div key={id}>
                      <Cards header={card.header} actions={getCardActions(id)}>
                        {card.component}
                      </Cards>
                    </div>
                  );
                })}
              </GridLayout>
            )}

            {/* === UNPINNED CARDS === */}
            {unpinned.length > 0 && (
              <GridLayout
                className="layout p-2"
                layout={buildLayout(unpinned, 0)}
                cols={12}
                rowHeight={150}
                width={1360}
                isResizable
                isDraggable
              >
                {unpinned.map((id) => {
                  const card = allCards.find((c) => c.id === id);
                  if (!card) return null;
                  return (
                    <div key={id}>
                      <Cards header={card.header} actions={getCardActions(id)}>
                        {card.component}
                      </Cards>
                    </div>
                  );
                })}
              </GridLayout>
            )}



            {/* === MODAL === */}
            <AnimatePresence>
              {showPinLimitModal && (
                <motion.div
                  className="fixed inset-0 flex items-center justify-center bg-black/30 z-50"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <motion.div
                    className="bg-white rounded-xl p-6 w-80 shadow-lg text-center"
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0.8 }}
                    transition={{ duration: 0.2 }}
                  >
                    <h3 className="text-lg font-semibold mb-4">Pin Limit Reached</h3>
                    <p className="text-gray-600 mb-6">You can pin a maximum of 8 cards.</p>
                    <button
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                      onClick={() => setShowPinLimitModal(false)}
                    >
                      OK
                    </button>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </main>
    </div>
  );
};

export default ContentContainer;
