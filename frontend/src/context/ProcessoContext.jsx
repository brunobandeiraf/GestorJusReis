import { createContext, useContext, useState, useCallback } from 'react';
import {
  getProcessos as fetchProcessosApi,
  cadastrarProcesso as cadastrarProcessoApi,
  removerProcesso as removerProcessoApi,
  getMonitoramentoStatus as fetchMonitoramentoStatusApi,
} from '../services/api';

const ProcessoContext = createContext(null);

export function ProcessoProvider({ children }) {
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [monitoramentoStatus, setMonitoramentoStatus] = useState(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const fetchProcessos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchProcessosApi();
      setProcessos(response.data.processos || response.data || []);
    } catch (err) {
      setError(err.message || 'Erro ao carregar processos.');
    } finally {
      setLoading(false);
    }
  }, []);

  const addProcesso = useCallback(async (numeroCnj) => {
    setLoading(true);
    setError(null);
    try {
      const response = await cadastrarProcessoApi(numeroCnj);
      setProcessos((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError(err.message || 'Erro ao cadastrar processo.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const removeProcesso = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      await removerProcessoApi(id);
      setProcessos((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setError(err.message || 'Erro ao remover processo.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMonitoramentoStatus = useCallback(async () => {
    try {
      const response = await fetchMonitoramentoStatusApi();
      setMonitoramentoStatus(response.data);
    } catch (err) {
      // Non-critical, don't set global error
      console.error('Erro ao buscar status do monitoramento:', err);
    }
  }, []);

  const value = {
    processos,
    loading,
    error,
    monitoramentoStatus,
    fetchProcessos,
    addProcesso,
    removeProcesso,
    clearError,
    fetchMonitoramentoStatus,
  };

  return (
    <ProcessoContext.Provider value={value}>
      {children}
    </ProcessoContext.Provider>
  );
}

export function useProcessos() {
  const context = useContext(ProcessoContext);
  if (!context) {
    throw new Error('useProcessos must be used within a ProcessoProvider');
  }
  return context;
}
