import { useProcessos } from '../../context/ProcessoContext';
import { formatarCNJ } from '../../utils/cnjFormatter';
import { Link } from 'react-router-dom';

function ProcessoList() {
  const { processos, removeProcesso, loading } = useProcessos();

  const handleRemove = async (id) => {
    if (window.confirm('Deseja remover este processo do monitoramento?')) {
      try {
        await removeProcesso(id);
      } catch {
        // Error is handled by context
      }
    }
  };

  if (processos.length === 0) {
    return (
      <section style={styles.container}>
        <h2 style={styles.title}>Processos Monitorados</h2>
        <p style={styles.empty}>Nenhum processo cadastrado para monitoramento.</p>
      </section>
    );
  }

  return (
    <section style={styles.container}>
      <h2 style={styles.title}>Processos Monitorados</h2>
      <ul style={styles.list} role="list">
        {processos.map((processo) => {
          const hasNew = processo.novas_movimentacoes > 0;
          return (
            <li key={processo.id} style={styles.item}>
              <div style={styles.itemContent}>
                <div style={styles.mainInfo}>
                  <Link to={`/processo/${processo.id}`} style={styles.link}>
                    <span style={styles.cnj}>{formatarCNJ(processo.numero_cnj)}</span>
                  </Link>
                  {hasNew && (
                    <span style={styles.badge} aria-label="Novas movimentações">
                      Novo
                    </span>
                  )}
                </div>
                <div style={styles.details}>
                  {processo.tribunal && (
                    <span style={styles.tag}>{processo.tribunal}</span>
                  )}
                  {processo.classe && (
                    <span style={styles.classe}>{processo.classe}</span>
                  )}
                  {processo.status && (
                    <span style={styles.status}>{processo.status}</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleRemove(processo.id)}
                disabled={loading}
                style={styles.removeBtn}
                aria-label={`Remover processo ${processo.numero_cnj}`}
                title="Remover do monitoramento"
              >
                ✕
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

const styles = {
  container: {
    padding: '1rem',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
  },
  title: {
    margin: '0 0 1rem 0',
    fontSize: '1.25rem',
  },
  empty: {
    color: '#666',
    fontStyle: 'italic',
  },
  list: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  item: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem',
    borderBottom: '1px solid #f0f0f0',
  },
  itemContent: {
    flex: 1,
  },
  mainInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.25rem',
  },
  link: {
    textDecoration: 'none',
    color: '#1976d2',
  },
  cnj: {
    fontFamily: 'monospace',
    fontSize: '0.95rem',
    fontWeight: '500',
  },
  badge: {
    display: 'inline-block',
    padding: '0.125rem 0.5rem',
    backgroundColor: '#ff9800',
    color: '#fff',
    borderRadius: '12px',
    fontSize: '0.7rem',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  details: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
    fontSize: '0.8rem',
    color: '#555',
  },
  tag: {
    padding: '0.125rem 0.375rem',
    backgroundColor: '#e3f2fd',
    borderRadius: '4px',
    color: '#1565c0',
  },
  classe: {
    color: '#555',
  },
  status: {
    color: '#388e3c',
    fontWeight: '500',
  },
  removeBtn: {
    background: 'none',
    border: '1px solid #ef5350',
    color: '#ef5350',
    borderRadius: '4px',
    padding: '0.25rem 0.5rem',
    cursor: 'pointer',
    fontSize: '0.875rem',
    marginLeft: '0.5rem',
  },
};

export default ProcessoList;
