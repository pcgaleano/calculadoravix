# Frontend Structure - CalculadoraVIX

```
frontend/
├── public/
│   ├── index.html (SEO optimizado)
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── VixCalculator.js (Calculadora principal)
│   │   ├── ResultsDisplay.js (Mostrar resultados)
│   │   ├── TickerSelector.js (Selector de símbolos)
│   │   ├── Header.js (Navegación)
│   │   └── Footer.js
│   ├── pages/
│   │   ├── Home.js (Landing page)
│   │   ├── Calculator.js (Página calculadora)
│   │   ├── About.js (Sobre VIX Fix)
│   │   └── Api.js (Documentación API)
│   ├── services/
│   │   └── api.js (Llamadas al backend)
│   ├── styles/
│   │   └── index.css (Estilos globales)
│   ├── App.js
│   └── index.js
└── package.json
```

## Características principales:
1. **Calculadora VIX Fix interactiva**
2. **Landing page SEO optimizada**
3. **Integración con API backend**
4. **Diseño responsive**
5. **Resultados en tiempo real**
6. **Soporte para múltiples tickers**