function MovimentacaoList({ movimentacoes = [] }) {
  if (movimentacoes.length === 0) {
    return (
      <section style={styles.container}>
        <h3 style={styles.title}>Movimentações</h3>
        <p style={styles.empty}>Nenhuma movimentação registrada.</p>
      </section>
    );
  }

  // Normaliza o campo de data (API retorna 'data', banco retorna 'data_movimentacao')
  const normalized = movimentacoes.map((mov) => ({
    ...mov,
    _date: mov.data_movimentacao || mov.data || null,
  }));

  // Sort by date descending (most recent first)
  const sorted = [...normalized].sort((a, b) => {
    const dateA = new Date(a._date || 0);
    const dateB = new Date(b._date || 0);
    return dateB - dateA;
  });

  // Agrupa movimentações consecutivas com mesmo nome na mesma data
  const grouped = [];
  for (const mov of sorted) {
    const dateStr = formatDateShort(mov._date);
    const last = grouped[grouped.length - 1];
    if (last && last.nome === mov.nome && formatDateShort(last._date) === dateStr) {
      last._count = (last._count || 1) + 1;
    } else {
      grouped.push({ ...mov, _count: 1 });
    }
  }

  return (
    <section style={styles.container}>
      <h3 style={styles.title}>
        Movimentações
        <span style={styles.count}>({movimentacoes.length} total)</span>
      </h3>
      <ol style={styles.list} role="list">
        {grouped.map((mov, idx) => (
          <li
            key={mov.id || idx}
            style={{
              ...styles.item,
              ...(mov.nova ? styles.itemNew : {}),
            }}
          >
            <div style={styles.header}>
              <time style={styles.date} dateTime={mov._date}>
                {formatDate(mov._date)}
              </time>
              {mov.nova && (
                <span style={styles.badge} aria-label="Nova movimentação">
                  Nova
                </span>
              )}
              {mov._count > 1 && (
                <span style={styles.countBadge}>
                  ×{mov._count}
                </span>
              )}
            </div>
            <p style={styles.nome}>{mov.nome}</p>
            {mov.complemento && !isNumericOnly(mov.complemento) && (
              <p style={styles.complemento}>{mov.complemento}</p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}

function isNumericOnly(str) {
  if (!str) return false;
  // Filtra complementos que são apenas números (códigos sem significado para o usuário)
  return /^\d+([;\s]*\d+)*$/.test(str.trim());
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleDateString('pt-BR', {
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

function formatDateShort(dateStr) {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleDateString('pt-BR');
  } catch {
    return '';
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
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  count: {
    fontSize: '0.8rem',
    color: '#888',
    fontWeight: '400',
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
  countBadge: {
    display: 'inline-block',
    padding: '0.1rem 0.4rem',
    backgroundColor: '#e0e0e0',
    color: '#555',
    borderRadius: '10px',
    fontSize: '0.7rem',
    fontWeight: '600',
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
