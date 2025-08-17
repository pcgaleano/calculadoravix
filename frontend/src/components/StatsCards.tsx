import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Clock, Target } from 'lucide-react';

interface StatsCardsProps {
  totalTrades: number;
  tradesExitosos: number;
  profitTotal: number;
  diasPromedio: number;
}

const StatsCards: React.FC<StatsCardsProps> = ({
  totalTrades,
  tradesExitosos,
  profitTotal,
  diasPromedio,
}) => {
  const tasaExito = totalTrades > 0 ? (tradesExitosos / totalTrades) * 100 : 0;
  const tradesAbiertos = totalTrades - tradesExitosos;

  const stats = [
    {
      title: 'Trades Abiertos',
      value: tradesAbiertos.toString(),
      icon: TrendingUp,
      color: 'text-primary-400',
      bgColor: 'bg-primary-900/20',
      borderColor: 'border-primary-700/50',
    },
    {
      title: 'Tasa de Éxito',
      value: `${tasaExito.toFixed(1)}%`,
      icon: Target,
      color: tasaExito >= 70 ? 'text-success-400' : tasaExito >= 50 ? 'text-yellow-400' : 'text-danger-400',
      bgColor: tasaExito >= 70 ? 'bg-success-900/20' : tasaExito >= 50 ? 'bg-yellow-900/20' : 'bg-danger-900/20',
      borderColor: tasaExito >= 70 ? 'border-success-700/50' : tasaExito >= 50 ? 'border-yellow-700/50' : 'border-danger-700/50',
    },
    {
      title: 'P&L Total',
      value: `$${profitTotal.toFixed(2)}`,
      icon: profitTotal >= 0 ? TrendingUp : TrendingDown,
      color: profitTotal >= 0 ? 'text-success-400' : 'text-danger-400',
      bgColor: profitTotal >= 0 ? 'bg-success-900/20' : 'bg-danger-900/20',
      borderColor: profitTotal >= 0 ? 'border-success-700/50' : 'border-danger-700/50',
    },
    {
      title: 'Días Promedio',
      value: `${diasPromedio.toFixed(1)}d`,
      icon: Clock,
      color: 'text-gray-400',
      bgColor: 'bg-gray-900/20',
      borderColor: 'border-gray-700/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div
            key={index}
            className={`trading-card p-6 border ${stat.borderColor} ${stat.bgColor} slide-in`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400 mb-1">
                  {stat.title}
                </p>
                <p className={`text-2xl font-bold ${stat.color}`}>
                  {stat.value}
                </p>
              </div>
              <Icon className={`h-8 w-8 ${stat.color}`} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatsCards;