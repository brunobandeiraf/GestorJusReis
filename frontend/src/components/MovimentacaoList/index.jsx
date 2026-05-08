function MovimentacaoList({ movimentacoes = [] }) {
  if (movimentacoes.length === 0) {
    return (
      <section style={styles.container}>
        <h3 style={styles.title}>Movimentações</h3>
        <p style={styles.empty}>Nenhuma movimentação registrada.</p>
      </section>
    );
  }

  // Sort by date descending (most recent first)
  const sorted = [...movimentacoes].sort((a, b) => {
    const dateA = new Date(a.data_movimentacao);
    const dateB = new Date(b.data_movimentacao);
    return dateB - dateA;
  });

  return (
    <section style={styles.container}>
      <h3 style={styles.title}>Movimentações</h3>
      <ol style={styles.list} role="list">
        {sorted.map((mov, idx) => (
          <li
            key={mov.id || idx}
            style={{
              ...styles.item,
              ...(mov.nova ? styles.itemNew : {}),
            }}
          >
            <div style={styles.header}>
              <time style={styles.date} dateTime={mov.data_movimentacao}>
                {formatDate(mov.data_movimentacao)}
              </time>
              {mov.nova && (
                <span style={styles.badge} aria-label="Nova movimentação">
                  Nova
                </span>
              )}
            </div>
            <p style={styles.nome}>{mov.nome}</p>
            {mov.complemento && (
              <p style={styles.complemento}>{mov.complemento}</p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

const styles = {
  container: {
    padding: '1rem',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
  },
  title: {
    margin: '0 0 1rem 0',
    fontSize: '1.1rem',
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
    padding: '0.75rem',
    borderLeft: '3px solid #e0e0e0',
    marginBottom: '0.5rem',
    borderRadius: '0 4px 4px 0',
    backgroundColor: '#fafafa',
  },
  itemNew: {
    borderLeftColor: '#ff9800',
    backgroundColor: '#fff8e1',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.25rem',
  },
  date: {
    fontSize: '0.8rem',
    color: '#666',
    fontWeight: '500',
  },
  badge: {
    display: 'inline-block',
    padding: '0.1rem 0.4rem',
    backgroundColor: '#ff9800',
    color: '#fff',
    borderRadius: '10px',
    fontSize: '0.65rem',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  nome: {
    margin: '0 0 0.25rem 0',
    fontWeight: '500',
    fontSize: '0.9rem',
  },
  complemento: {
    margin: 0,
    fontSize: '0.8rem',
    color: '#555',
  },
};

export default MovimentacaoList;
