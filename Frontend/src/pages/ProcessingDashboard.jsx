import React from "react";

export const ProcessingDashboard = () => {
  return (
    <div className="h-screen w-full bg-[#F5F7F8] flex items-center justify-center">

      <div className="flex flex-col items-center text-center animate-fadeIn">

        {/* Animated Circle */}
        <div className="relative mb-12">

          {/* Outer rotating ring */}
          <div className="absolute inset-0 h-40 w-40 rounded-full border border-gray-300 animate-spin-slow"></div>

          {/* Pulse ring */}
          <div className="absolute inset-0 h-40 w-40 rounded-full border border-gray-300 animate-ping opacity-20"></div>

          {/* Main circle */}
          <div className="h-40 w-40 rounded-full border border-gray-300 flex items-center justify-center">
            
            <div className="h-24 w-24 rounded-full border border-gray-300 flex items-center justify-center">
              
              <div className="h-10 w-10 bg-gray-400 rounded-md flex items-center justify-center animate-pulse">
                ✓
              </div>

            </div>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl font-semibold mb-4">Processing</h1>

        <p className="text-gray-500 max-w-md mb-12">
          Clearing the mental space. We're organizing your thoughts into clarity.
        </p>

        {/* Cards */}
        <div className="flex gap-6">

          {/* Phase 1 */}
          <div className="bg-white p-6 rounded-2xl w-72 shadow-sm transition-all duration-500 hover:shadow-md">
            <p className="text-xs text-gray-400 mb-2">PHASE 1</p>
            <h3 className="font-semibold mb-2">Deciphering Dump</h3>
            <p className="text-sm text-gray-500">
              Extracting core themes from your stream of consciousness.
            </p>
          </div>

          {/* Phase 2 animated */}
          <div className="bg-white p-6 rounded-2xl w-72 shadow-sm border-b-4 border-[#546E7A] animate-progressGlow">
            <p className="text-xs text-gray-400 mb-2">PHASE 2</p>
            <h3 className="font-semibold mb-2">Tonal Analysis</h3>
            <p className="text-sm text-gray-500">
              Identifying underlying emotional patterns and stressors.
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 mt-10 animate-pulse">
          • Almost there. Breathe deeply. •
        </p>
      </div>
    </div>
  );
};