import React from 'react';

const InventoryPage: React.FC = () => {
  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="card text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Inventory</h1>
          <p className="text-gray-400 mb-6">Manage your items and equipment coming soon!</p>
          <div className="text-6xl mb-4">🎒</div>
          <p className="text-sm text-gray-500">This page is under development</p>
        </div>
      </div>
    </div>
  );
};

export default InventoryPage;