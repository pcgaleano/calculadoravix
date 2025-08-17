import React from 'react';
import { Calendar } from 'lucide-react';

interface DateSelectorProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  isLoading: boolean;
}

const DateSelector: React.FC<DateSelectorProps> = ({
  selectedDate,
  onDateChange,
  isLoading,
}) => {
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onDateChange(e.target.value);
  };

  const getQuickDateOptions = () => {
    const today = new Date();
    const options = [
      {
        label: 'Hoy',
        value: today.toISOString().split('T')[0],
      },
      {
        label: '1 semana',
        value: new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      },
      {
        label: '1 mes',
        value: new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      },
      {
        label: '3 meses',
        value: new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      },
      {
        label: '6 meses',
        value: new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      },
      {
        label: '1 año',
        value: new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      },
    ];
    return options;
  };

  return (
    <div className="trading-card p-6 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Calendar className="h-5 w-5 text-primary-500" />
          <div>
            <h3 className="text-lg font-semibold text-white">Análisis por Fecha</h3>
            <p className="text-sm text-gray-400">
              Selecciona la fecha de inicio para analizar trades
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Quick date options */}
          <div className="flex items-center space-x-2">
            {getQuickDateOptions().map((option, index) => (
              <button
                key={index}
                onClick={() => onDateChange(option.value)}
                disabled={isLoading}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                  selectedDate === option.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
                } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {option.label}
              </button>
            ))}
          </div>

          {/* Custom date input */}
          <div className="flex items-center space-x-2">
            <label htmlFor="date-input" className="text-sm text-gray-400">
              Fecha personalizada:
            </label>
            <input
              id="date-input"
              type="date"
              value={selectedDate}
              onChange={handleDateChange}
              disabled={isLoading}
              className={`bg-dark-700 border border-dark-600 rounded-md px-3 py-2 text-sm text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              max={new Date().toISOString().split('T')[0]}
            />
          </div>
        </div>
      </div>

      {/* Selected date info */}
      <div className="mt-4 pt-4 border-t border-dark-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Analizando desde: <span className="font-semibold text-white">{selectedDate}</span>
          </span>
          <span className="text-gray-400">
            Hasta: <span className="font-semibold text-white">
              {new Date().toISOString().split('T')[0]}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default DateSelector;