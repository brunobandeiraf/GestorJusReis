import { useEffect } from 'react';
import { useProcessos } from '../context/ProcessoContext';
import ProcessoForm from '../components/ProcessoForm/index';
import ProcessoList from '../components/ProcessoList/index';

function Dashboard() {
  const { fetchProcessos, fetchMonitoramentoStatus, monitoramentoStatus, error, clearError } =
    useProcessos();

  useEffect(() => {
    fetchProcessos();
    fetchMonitoramentoStatus();
  }, [fetchProcessos, fetchMonitoramentoStatus]);

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Dashboard</h1>

      {error && (
        <div role="alert" style={styles.error}>
          <span>{error}</span>
          <button onClick={clearError} style={styles.dismissBtn} aria-label="Fechar">
            ✕
          </button>
        </div>
      )}

      {monitoramentoStatus && (
        <div style={styles.statusCard}>
          <h3 style={styles.statusTitle}>Status do Monitoramento</h3>
          <div style={styles.statusGrid}>
            <div>
              <span style={styles.statusLabel}>Último:</span>{' '}
              {monitoramentoStatus.data_execucao
                ? new Date(monitoramentoStatus.data_execucao).toLocaleString('pt-BR')
                : '—'}
            </div>
            <div>
              <span style={styles.statusLabel}>Status:</span>{' '}
              {monitoramentoStatus.status || '—'}
            </div>
            <div>
              <span style={styles.statusLabel}>Processos:</span>{' '}
              {monitoramentoStatus.total_processos ?? '—'}
            </div>
            <div>
              <span style={styles.statusLabel}>Atualizados:</span>{' '}
              {monitoramentoStatus.processos_atualizados ?? '—'}
            </div>
          </div>
        </div>
      )}

      <ProcessoForm />
      <ProcessoList />
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
  },
  heading: {
    marginBottom: '1.5rem',
    fontSize: '1.75rem',
  },
  error: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem',
    backgroundColor: '#ffebee',
    color: '#c62828',
    border: '1px solid #ef9a9a',
    borderRadius: '4px',
    marginBottom: '1rem',
    fontSize: '0.875rem',
  },
  dismissBtn: {
    background: 'none',
    border: 'none',
    color: '#c62828',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  statusCard: {
    padding: '1rem',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    marginBottom: '1rem',
    backgroundColor: '#f5f5f5',
  },
  statusTitle: {
    margin: '0 0 0.5rem 0',
    fontSize: '1rem',
  },
  statusGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '0.5rem',
    fontSize: '0.875rem',
  },
  statusLabel: {
    fontWeight: '600',
    color: '#555',
  },
};

export default Dashboard;
