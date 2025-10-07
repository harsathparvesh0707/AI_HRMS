import React from "react";
import { PieChart, Pie, Cell, Tooltip } from "recharts";

const data = [
  { name: "Job Boards", value: 100 },
  { name: "Referrals", value: 50 },
  { name: "Socials", value: 40 },
  { name: "Others", value: 10 },
];

const COLORS = ["#22c55e", "#facc15", "#3b82f6", "#9333ea"];

const Charts = () => {
  return (
    <div className="flex flex-col items-center relative">
      {/* Donut Chart */}
      <PieChart width={250} height={250}>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={5}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>

      {/* Center Text */}
      <div className="absolute mt-[110px] text-center">
        <p className="text-sm font-medium">Total Companies</p>
        <p className="text-xl font-bold">
          {data.reduce((acc, cur) => acc + cur.value, 0)}
        </p>
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2 mt-4 text-sm">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS[index] }}
            />
            {item.value} {item.name}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Charts;