import React, { useState, useEffect } from 'react';
import { Settings, Play, Pause, RotateCcw } from 'lucide-react';

interface RefreshControlProps {
  isAutoRefreshEnabled: boolean;
  refreshInterval: number;
  onToggleAutoRefresh: () => void;
  onIntervalChange: (interval: number) => void;
  onManualRefresh: () => void;
  isLoading: boolean;
  lastUpdated?: Date;
}

const REFRESH_OPTIONS = [
  { label: '10 segundos', value: 10000 },
  { label: '30 segundos', value: 30000 },
  { label: '1 minuto', value: 60000 },
  { label: '2 minutos', value: 120000 },
  { label: '5 minutos', value: 300000 },
];

export const RefreshControl: React.FC<RefreshControlProps> = ({
  isAutoRefreshEnabled,
  refreshInterval,
  onToggleAutoRefresh,
  onIntervalChange,
  onManualRefresh,
  isLoading,
  lastUpdated,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (!isAutoRefreshEnabled) {
      setCountdown(0);
      return;
    }

    const startTime = Date.now();
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, refreshInterval - elapsed);
      setCountdown(remaining);

      if (remaining === 0) {
        clearInterval(timer);
      }
    }, 100);

    return () => clearInterval(timer);
  }, [isAutoRefreshEnabled, refreshInterval, lastUpdated]);

  const formatTime = (ms: number) => {
    const seconds = Math.ceil(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${remainingSeconds}s`;
  };

  const formatLastUpdated = (date?: Date) => {
    if (!date) return 'Nunca';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (minutes > 0) {
      return `hace ${minutes}m`;
    }
    return `hace ${seconds}s`;
  };

  return (
    <div className="trading-card p-4 font-google">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-semibold">Control de Actualización</h3>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="trading-button trading-button-primary text-sm px-3 py-1"
        >
          {isExpanded ? 'Ocultar' : 'Mostrar'}
        </button>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={onToggleAutoRefresh}
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${
            isAutoRefreshEnabled
              ? 'bg-success-600 text-white hover:bg-success-700'
              : 'bg-gray-600 text-white hover:bg-gray-700'
          }`}
        >
          {isAutoRefreshEnabled ? (
            <>
              <Pause className="w-4 h-4" />
              Auto ON
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Auto OFF
            </>
          )}
        </button>

        <button
          onClick={onManualRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 trading-button trading-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RotateCcw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>

        <div className="flex flex-col">
          <span className="text-xs text-gray-400">Última actualización</span>
          <span className="text-sm font-medium">
            {formatLastUpdated(lastUpdated)}
          </span>
        </div>
      </div>

      {isAutoRefreshEnabled && (
        <div className="mb-4 p-3 bg-primary-900/20 border border-primary-700/50 rounded-md">
          <div className="flex items-center justify-between">
            <span className="text-sm text-primary-300">
              Próxima actualización en:
            </span>
            <span className="text-lg font-mono text-primary-400">
              {formatTime(countdown)}
            </span>
          </div>
          <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-100"
              style={{
                width: `${100 - (countdown / refreshInterval) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      {isExpanded && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Intervalo de actualización automática
            </label>
            <div className="grid grid-cols-2 gap-2">
              {REFRESH_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onIntervalChange(option.value)}
                  className={`px-3 py-2 text-sm rounded-md border transition-all ${
                    refreshInterval === option.value
                      ? 'bg-primary-600 text-white border-primary-500'
                      : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="text-xs text-gray-400 pt-2 border-t border-gray-700">
            <p>• El auto-refresh se pausa automáticamente durante las cargas</p>
            <p>• Los datos se actualizan solo si la API está conectada</p>
            <p>• Usa "Actualizar" para refrescar manualmente en cualquier momento</p>
          </div>
        </div>
      )}
    </div>
  );
};