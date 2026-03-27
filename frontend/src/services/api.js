/**
 * API service – all calls to the Django backend
 */
import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({ baseURL: BASE_URL });

export const getSymbols        = ()                   => api.get('/symbols/');
export const getTimeframes     = ()                   => api.get('/timeframes/');
export const getHealth         = ()                   => api.get('/health/');
export const getForexData      = (params)             => api.get('/forex-data/', { params });
export const getEconomicData   = ()                   => api.get('/economic-indicators/');
export const generateSignals   = (data)               => api.post('/signals/', data);
export const getSignalHistory  = (params)             => api.get('/signals/history/', { params });
export const trainRL           = (data)               => api.post('/signals/train-rl/', data);
export const sendChat          = (data)               => api.post('/chat/', data);
export const explainSignal     = (data)               => api.post('/chat/explain/', data);

export default api;
