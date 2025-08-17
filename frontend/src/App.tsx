import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import StatsCards from './components/StatsCards';
import DateSelector from './components/DateSelector';
import TradesTable from './components/TradesTable';
import { RefreshControl } from './components/RefreshControl';
import { tradingAPI } from './services/api';
import { DashboardData } from './types';
import { AlertCircle } from 'lucide-react';

function App() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    // Default to 1 month ago
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    return oneMonthAgo.toISOString().split('T')[0];
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState<boolean>(true);
  const [refreshInterval, setRefreshInterval] = useState<number>(30000);
  const [lastUpdated, setLastUpdated] = useState<Date | undefined>();

  // Check API health
  const checkApiHealth = useCallback(async () => {
    try {
      await tradingAPI.healthCheck();
      setApiStatus('connected');
      setError(null);
    } catch (err) {
      setApiStatus('disconnected');
      setError('Error conectando con la API. Asegúrate de que el backend esté ejecutándose en http://127.0.0.1:8000');
    }
  }, []);

  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    if (apiStatus !== 'connected') return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Calcular diferencia en días
      const fechaSeleccionada = new Date(selectedDate);
      const fechaActual = new Date();
      const diffInDays = Math.floor((fechaActual.getTime() - fechaSeleccionada.getTime()) / (1000 * 60 * 60 * 24));
      
      // Si es más de 45 días, usar análisis histórico
      if (diffInDays > 45) {
        const fechaFin = fechaActual.toISOString().split('T')[0];
        const historicalData = await tradingAPI.getHistoricalAnalysis(selectedDate, fechaFin);
        
        // Convertir datos históricos al formato del dashboard
        const dashboardConverted: DashboardData = {
          fecha_analisis: selectedDate,
          trades_abiertos: historicalData.trades_historicos.map(trade => ({
            trade_num: trade.trade_num,
            ticker: trade.ticker,
            fecha_compra: trade.fecha_compra,
            precio_compra: trade.precio_compra,
            precio_target: trade.precio_target,
            fecha_venta: trade.fecha_venta || undefined,
            precio_venta: trade.precio_venta || undefined,
            dias_trade: trade.dias_duracion,
            profit_pct: trade.profit_pct,
            profit_absoluto: trade.profit_absoluto,
            estado: trade.estado_final,
            precio_actual: trade.precio_venta || trade.precio_compra
          })),
          total_trades: historicalData.resumen.total_trades,
          trades_exitosos: historicalData.resumen.trades_exitosos,
          profit_total: historicalData.resumen.profit_total,
          dias_promedio: historicalData.resumen.avg_dias_duracion
        };
        
        setDashboardData(dashboardConverted);
      } else {
        // Para períodos cortos, usar dashboard normal
        const data = await tradingAPI.getDashboardData(selectedDate);
        setDashboardData(data);
      }
      
      setLastUpdated(new Date());
    } catch (err: any) {
      console.error('Error loading dashboard data:', err);
      setError(err.response?.data?.detail || 'Error cargando datos del dashboard');
      setDashboardData(null);
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate, apiStatus]);

  // Handle date change
  const handleDateChange = (newDate: string) => {
    setSelectedDate(newDate);
  };

  // Handle refresh
  const handleRefresh = () => {
    if (apiStatus === 'connected') {
      loadDashboardData();
    } else {
      checkApiHealth();
    }
  };

  // Initial load
  useEffect(() => {
    checkApiHealth();
  }, [checkApiHealth]);

  // Load data when date changes or API connects
  useEffect(() => {
    if (apiStatus === 'connected') {
      loadDashboardData();
    }
  }, [loadDashboardData, apiStatus]);

  // Auto-refresh with configurable interval
  useEffect(() => {
    if (!isAutoRefreshEnabled) return;

    const interval = setInterval(() => {
      if (apiStatus === 'connected' && !isLoading) {
        loadDashboardData();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [loadDashboardData, apiStatus, isLoading, isAutoRefreshEnabled, refreshInterval]);

  // Refresh control handlers
  const handleToggleAutoRefresh = () => {
    setIsAutoRefreshEnabled(!isAutoRefreshEnabled);
  };

  const handleIntervalChange = (newInterval: number) => {
    setRefreshInterval(newInterval);
  };

  const handleManualRefresh = () => {
    if (apiStatus === 'connected') {
      loadDashboardData();
    } else {
      checkApiHealth();
    }
  };

  return (
    <div className="min-h-screen bg-dark-900">
      <Header 
        onRefresh={handleRefresh} 
        isLoading={isLoading || apiStatus === 'checking'} 
      />
      
      <main className="container mx-auto px-6 py-8">
        {/* API Status */}
        {apiStatus === 'disconnected' && (
          <div className="mb-6 p-4 bg-danger-900/20 border border-danger-700/50 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-danger-400" />
              <p className="text-danger-400 font-medium">API Desconectada</p>
            </div>
            <p className="text-sm text-danger-300 mt-1">
              No se puede conectar con el backend. Ejecuta: <code className="bg-dark-800 px-2 py-1 rounded">python backend/main.py</code>
            </p>
          </div>
        )}

        {/* Date Selector */}
        <DateSelector
          selectedDate={selectedDate}
          onDateChange={handleDateChange}
          isLoading={isLoading}
        />

        {/* Refresh Control */}
        <div className="mb-6">
          <RefreshControl
            isAutoRefreshEnabled={isAutoRefreshEnabled}
            refreshInterval={refreshInterval}
            onToggleAutoRefresh={handleToggleAutoRefresh}
            onIntervalChange={handleIntervalChange}
            onManualRefresh={handleManualRefresh}
            isLoading={isLoading}
            lastUpdated={lastUpdated}
          />
        </div>

        {/* Error Message */}
        {error && apiStatus === 'connected' && (
          <div className="mb-6 p-4 bg-danger-900/20 border border-danger-700/50 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-danger-400" />
              <p className="text-danger-400 font-medium">Error</p>
            </div>
            <p className="text-sm text-danger-300 mt-1">{error}</p>
          </div>
        )}

        {/* Dashboard Content */}
        {apiStatus === 'connected' && (
          <>
            {/* Stats Cards */}
            {dashboardData && (
              <StatsCards
                totalTrades={dashboardData.total_trades}
                tradesExitosos={dashboardData.trades_exitosos}
                profitTotal={dashboardData.profit_total}
                diasPromedio={dashboardData.dias_promedio}
              />
            )}

            {/* Trades Table */}
            <TradesTable
              trades={dashboardData?.trades_abiertos || []}
              isLoading={isLoading}
            />
          </>
        )}

        {/* Loading State */}
        {apiStatus === 'checking' && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="loading-spinner w-8 h-8 mx-auto mb-4" />
              <p className="text-gray-400">Conectando con la API...</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-dark-800 border-t border-dark-700 py-4 mt-12">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>Trading Dashboard v1.0.0 - Sistema Profesional VIX_Fix</span>
            <span>
              {dashboardData && (
                <>Última actualización: {new Date().toLocaleTimeString('es-AR')}</>
              )}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
