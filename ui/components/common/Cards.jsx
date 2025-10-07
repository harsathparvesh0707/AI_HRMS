import React from "react";


const Cards = ({ children, header, footer, actions }) => {
  return (
    <div className="bg-white shadow-md rounded-2xl flex flex-col w-auto h-auto">
      {/* Header */}
      {header && (
        <div className="p-3 font-semibold text-lg flex items-center justify-between">
          <span>{header}</span>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}

      {/* Body */}
      <div className="flex-1 p-4 pt-0 overflow-auto">{children}</div>

      {/* Footer  */}
      {footer && (
        <div className="p-3 text-sm text-gray-600 bg-gray-50">{footer}</div>
      )}
    </div>
  );
};

export default Cards;
