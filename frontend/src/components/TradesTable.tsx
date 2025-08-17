import React, { useState, useMemo } from 'react';
import { TradeResult } from '../types';
import { Calendar, DollarSign, Target, TrendingUp, TrendingDown, ChevronUp, ChevronDown } from 'lucide-react';

interface TradesTableProps {
  trades: TradeResult[];
  isLoading: boolean;
}

type SortField = 'dias_trade' | 'profit_pct' | 'estado' | 'ticker' | 'fecha_compra' | 'precio_compra' | 'precio_actual' | 'precio_target' | 'profit_absoluto';
type SortDirection = 'asc' | 'desc';

const TradesTable: React.FC<TradesTableProps> = ({ trades, isLoading }) => {
  const [sortField, setSortField] = useState<SortField>('dias_trade');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedTrades = useMemo(() => {
    const sorted = [...trades].sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      if (sortField === 'fecha_compra') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      } else if (sortField === 'estado') {
        aValue = a.estado === 'TARGET_ALCANZADO' || a.profit_pct >= 4 ? 'CERRADO' : 'ABIERTO';
        bValue = b.estado === 'TARGET_ALCANZADO' || b.profit_pct >= 4 ? 'CERRADO' : 'ABIERTO';
      } else if (sortField === 'precio_actual') {
        aValue = aValue || a.precio_compra;
        bValue = bValue || b.precio_compra;
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    });
    
    return sorted;
  }, [trades, sortField, sortDirection]);

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ChevronUp className="h-4 w-4 text-gray-500 opacity-0 group-hover:opacity-50 transition-opacity" />;
    }
    return sortDirection === 'asc' 
      ? <ChevronUp className="h-4 w-4 text-primary-400" />
      : <ChevronDown className="h-4 w-4 text-primary-400" />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const getProfitColor = (profit: number) => {
    if (profit >= 4) return 'profit-positive';
    if (profit >= 0) return 'text-yellow-400';
    return 'profit-negative';
  };

  const getStatusBadge = (estado: string, profitPct: number) => {
    if (estado === 'TARGET_ALCANZADO' || profitPct >= 4) {
      return <span className="status-closed">CERRADO ✓</span>;
    }
    return <span className="status-open">ABIERTO</span>;
  };

  const getDaysColor = (days: number) => {
    if (days <= 7) return 'text-success-400';
    if (days <= 15) return 'text-yellow-400';
    return 'text-danger-400';
  };

  if (isLoading) {
    return (
      <div className="trading-card p-8">
        <div className="flex items-center justify-center space-x-2">
          <div className="loading-spinner" />
          <span className="text-gray-400">Cargando trades...</span>
        </div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="trading-card p-8 text-center">
        <TrendingUp className="h-12 w-12 text-gray-500 mx-auto mb-4" />
        <p className="text-gray-400 text-lg">No hay trades abiertos</p>
        <p className="text-gray-500 text-sm mt-2">
          Selecciona una fecha para analizar trades
        </p>
      </div>
    );
  }

  return (
    <div className="trading-card overflow-hidden">
      <div className="px-4 md:px-6 py-4 border-b border-dark-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 className="text-lg md:text-xl font-semibold text-white flex items-center space-x-2">
            <Target className="h-5 w-5 text-primary-500 flex-shrink-0" />
            <span>Trades Abiertos ({trades.length})</span>
          </h2>
          <p className="text-xs md:text-sm text-gray-400">
            Target general: 4% • Gestión profesional
          </p>
        </div>
      </div>

      {/* Tabla responsiva */}
      <div className="overflow-x-auto">
        <table className="trading-table min-w-full">
          <thead>
            <tr>
              <th className="text-center px-2 py-2">#</th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2 min-w-[80px]"
                onClick={() => handleSort('ticker')}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm">Ticker</span>
                  {getSortIcon('ticker')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2"
                onClick={() => handleSort('fecha_compra')}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm">Fecha</span>
                  {getSortIcon('fecha_compra')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2 hidden md:table-cell"
                onClick={() => handleSort('precio_compra')}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm">Compra</span>
                  {getSortIcon('precio_compra')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2"
                onClick={() => handleSort('precio_actual')}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm">Actual</span>
                  {getSortIcon('precio_actual')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2"
                onClick={() => handleSort('precio_target')}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm">Target</span>
                  {getSortIcon('precio_target')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2"
                onClick={() => handleSort('dias_trade')}
              >
                <div className="flex items-center justify-center">
                  <span className="text-xs sm:text-sm">Días</span>
                  {getSortIcon('dias_trade')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2"
                onClick={() => handleSort('profit_pct')}
              >
                <div className="flex items-center justify-center">
                  <span className="text-xs sm:text-sm">P&L%</span>
                  {getSortIcon('profit_pct')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2 hidden lg:table-cell"
                onClick={() => handleSort('profit_absoluto')}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm">P&L$</span>
                  {getSortIcon('profit_absoluto')}
                </div>
              </th>
              <th 
                className="cursor-pointer hover:bg-dark-600 transition-colors group px-2 py-2"
                onClick={() => handleSort('estado')}
              >
                <div className="flex items-center justify-center">
                  <span className="text-xs sm:text-sm">Estado</span>
                  {getSortIcon('estado')}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedTrades.map((trade, index) => (
              <tr
                key={`${trade.ticker}-${trade.trade_num}`}
                className="slide-in"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <td className="text-center font-mono text-gray-400 px-2 py-2 text-xs sm:text-sm">
                  {trade.trade_num}
                </td>
                
                <td className="px-2 py-2">
                  <span className="ticker-badge text-xs">{trade.ticker}</span>
                </td>
                
                <td className="font-mono text-gray-300 px-2 py-2 text-xs">
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-3 w-3 text-gray-500" />
                    <span>{formatDate(trade.fecha_compra)}</span>
                  </div>
                </td>
                
                <td className="font-mono text-gray-300 px-2 py-2 hidden md:table-cell text-xs">
                  <span className="block truncate max-w-[80px]">
                    {formatCurrency(trade.precio_compra)}
                  </span>
                </td>
                
                <td className="font-mono font-semibold px-2 py-2 text-xs sm:text-sm">
                  <div className="flex items-center space-x-1">
                    {trade.precio_actual && trade.precio_actual > trade.precio_compra ? (
                      <TrendingUp className="h-3 w-3 text-success-400 flex-shrink-0" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-danger-400 flex-shrink-0" />
                    )}
                    <span className={`block truncate max-w-[80px] ${trade.precio_actual && trade.precio_actual > trade.precio_compra ? 'text-success-400' : 'text-danger-400'}`}>
                      {formatCurrency(trade.precio_actual || trade.precio_compra)}
                    </span>
                  </div>
                </td>
                
                <td className="font-mono text-primary-400 font-semibold px-2 py-2 text-xs">
                  <span className="block truncate max-w-[80px]">
                    {formatCurrency(trade.precio_target)}
                  </span>
                </td>
                
                <td className="text-center px-2 py-2">
                  <span className={`font-mono font-semibold text-xs sm:text-sm ${getDaysColor(trade.dias_trade)}`}>
                    {trade.dias_trade}d
                  </span>
                </td>
                
                <td className="text-center px-2 py-2">
                  <span className={`font-mono font-bold text-xs sm:text-sm ${getProfitColor(trade.profit_pct)}`}>
                    {trade.profit_pct >= 0 ? '+' : ''}{trade.profit_pct.toFixed(2)}%
                  </span>
                </td>
                
                <td className="font-mono font-semibold px-2 py-2 hidden lg:table-cell text-xs">
                  <div className="flex items-center space-x-1">
                    <DollarSign className="h-3 w-3 flex-shrink-0" />
                    <span className={`block truncate max-w-[70px] ${trade.profit_absoluto >= 0 ? 'text-success-400' : 'text-danger-400'}`}>
                      {trade.profit_absoluto >= 0 ? '+' : ''}{trade.profit_absoluto.toFixed(2)}
                    </span>
                  </div>
                </td>
                
                <td className="text-center px-2 py-2">
                  <div className="text-xs">
                    {getStatusBadge(trade.estado, trade.profit_pct)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>


      {/* Resumen en el footer */}
      <div className="px-4 md:px-6 py-4 bg-dark-700/50 border-t border-dark-600">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm">
          <span className="text-gray-400 text-center sm:text-left">
            Total de posiciones: <span className="font-semibold text-white">{trades.length}</span>
          </span>
          <span className="text-gray-400 text-center sm:text-right">
            P&L Total: <span className={`font-semibold ${trades.reduce((sum, trade) => sum + trade.profit_absoluto, 0) >= 0 ? 'text-success-400' : 'text-danger-400'}`}>
              {formatCurrency(trades.reduce((sum, trade) => sum + trade.profit_absoluto, 0))}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default TradesTable;