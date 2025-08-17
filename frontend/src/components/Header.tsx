import React from 'react';
import { TrendingUp, Activity, BarChart3 } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
}

const Header: React.FC<HeaderProps> = ({ onRefresh, isLoading }) => {
  return (
    <header className="bg-dark-800 border-b border-dark-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-8 w-8 text-primary-500" />
            <div>
              <h1 className="text-2xl font-bold text-white">Trading Dashboard</h1>
              <p className="text-sm text-gray-400">Sistema profesional de análisis VIX_Fix</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Status indicators */}
          <div className="flex items-center space-x-2 text-success-400">
            <Activity className="h-4 w-4" />
            <span className="text-sm font-medium">API Conectada</span>
          </div>
          
          <div className="flex items-center space-x-2 text-primary-400">
            <BarChart3 className="h-4 w-4" />
            <span className="text-sm font-medium">Mercados Abiertos</span>
          </div>
          
          {/* Refresh button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="trading-button-primary flex items-center space-x-2"
          >
            {isLoading ? (
              <div className="loading-spinner" />
            ) : (
              <Activity className="h-4 w-4" />
            )}
            <span>{isLoading ? 'Actualizando...' : 'Actualizar'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;