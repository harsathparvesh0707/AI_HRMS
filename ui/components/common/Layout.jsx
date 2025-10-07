import React from "react";

const Layout = ({ children, className, isVertical = true }) => {
  return (
    <div className={`w-auto h-auto ${className}`}>
      <div
        className={`flex ${
          isVertical ? "flex-col gap-6" : "flex-row gap-6"
        }`}
      >
        {children}
      </div>
    </div>
  );
};

export default Layout;
