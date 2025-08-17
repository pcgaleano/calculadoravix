// Types para la aplicación de trading

export interface TradeResult {
  trade_num: number;
  ticker: string;
  fecha_compra: string;
  precio_compra: number;
  precio_target: number;
  fecha_venta?: string;
  precio_venta?: number;
  dias_trade: number;
  profit_pct: number;
  profit_absoluto: number;
  estado: string;
  precio_actual?: number;
}

export interface DashboardData {
  fecha_analisis: string;
  trades_abiertos: TradeResult[];
  total_trades: number;
  trades_exitosos: number;
  profit_total: number;
  dias_promedio: number;
}

export interface TickerPrice {
  ticker: string;
  precio_actual: number;
  precio_anterior: number;
  cambio_pct: number;
  timestamp: string;
}

export interface AnalysisRequest {
  ticker: string;
  fecha_inicio: string;
  fecha_fin: string;
  profit_target?: number;
  max_days?: number;
}

export interface AnalysisResponse {
  ticker: string;
  periodo: {
    inicio: string;
    fin: string;
  };
  configuracion: {
    profit_target: number;
    max_days: number;
  };
  resumen: {
    total_trades: number;
    trades_exitosos: number;
    tasa_exito: number;
    profit_promedio: number;
    dias_promedio: number;
  };
  trades: TradeResult[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}