import axios from 'axios';
import { DashboardData, TickerPrice, AnalysisRequest, AnalysisResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptors para manejo de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const tradingAPI = {
  // Health check
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get('/health');
    return response.data;
  },

  // Obtener tickers disponibles
  getTickers: async (): Promise<{
    tickers: string[];
    count: number;
    categories: {
      argentinas: string[];
      etfs: string[];
      crypto: string[];
    };
  }> => {
    const response = await api.get('/tickers');
    return response.data;
  },

  // Obtener precio actual de un ticker
  getCurrentPrice: async (ticker: string): Promise<TickerPrice> => {
    const response = await api.get(`/price/${ticker}`);
    return response.data;
  },

  // Obtener datos del dashboard
  getDashboardData: async (fecha: string): Promise<DashboardData> => {
    const response = await api.get(`/dashboard?fecha=${fecha}`);
    return response.data;
  },

  // Analizar un ticker específico
  analyzeTicker: async (request: AnalysisRequest): Promise<AnalysisResponse> => {
    const response = await api.post('/analyze', request);
    return response.data;
  },

  // Analizar todos los tickers
  analyzeAllTickers: async (
    fecha_inicio: string,
    fecha_fin: string
  ): Promise<{
    periodo: { inicio: string; fin: string };
    tickers_analizados: number;
    resultados: Record<string, AnalysisResponse | { error: string }>;
  }> => {
    const response = await api.get(
      `/analyze-all?fecha_inicio=${fecha_inicio}&fecha_fin=${fecha_fin}`
    );
    return response.data;
  },

  // Análisis histórico completo
  getHistoricalAnalysis: async (
    fecha_inicio: string,
    fecha_fin: string,
    profit_target?: number,
    max_days?: number
  ): Promise<{
    resumen: {
      periodo: { inicio: string; fin: string };
      total_trades: number;
      trades_exitosos: number;
      trades_perdida: number;
      trades_timeout: number;
      profit_total: number;
      win_rate: number;
      avg_profit_ganadores: number;
      avg_perdida_perdedores: number;
      avg_dias_duracion: number;
      mejores_tickers: Array<{ ticker: string; profit: number; win_rate: number }>;
      peores_tickers: Array<{ ticker: string; profit: number; win_rate: number }>;
    };
    trades_historicos: Array<{
      trade_num: number;
      ticker: string;
      fecha_compra: string;
      precio_compra: number;
      precio_target: number;
      fecha_venta?: string;
      precio_venta?: number;
      dias_duracion: number;
      profit_pct: number;
      profit_absoluto: number;
      estado_final: 'EXITOSO' | 'PERDIDA' | 'TIMEOUT';
      resultado_detalle: string;
    }>;
    performance_por_ticker: Record<string, any>;
  }> => {
    const params = new URLSearchParams({
      fecha_inicio,
      fecha_fin,
    });
    
    if (profit_target !== undefined) {
      params.append('profit_target', profit_target.toString());
    }
    
    if (max_days !== undefined) {
      params.append('max_days', max_days.toString());
    }
    
    const response = await api.get(`/historical-analysis?${params.toString()}`);
    return response.data;
  },
};

export default api;