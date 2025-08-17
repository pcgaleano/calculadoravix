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
};

export default api;