import { formatarCNJ } from '../../utils/cnjFormatter';

function ProcessoDetail({ processo }) {
  if (!processo) {
    return <p style={styles.empty}>Nenhum processo selecionado.</p>;
  }

  const consultaUrl = processo.url_consulta_publica || null;

  return (
    <section style={styles.container}>
      <h2 style={styles.title}>Detalhes do Processo</h2>

      <dl style={styles.dl}>
        <div style={styles.field}>
          <dt style={styles.dt}>Número CNJ</dt>
          <dd style={styles.dd}>
            <span style={styles.cnj}>{formatarCNJ(processo.numero_cnj)}</span>
          </dd>
        </div>

        <div style={styles.field}>
          <dt style={styles.dt}>Tribunal</dt>
          <dd style={styles.dd}>{processo.tribunal || '—'}</dd>
        </div>

        <div style={styles.field}>
          <dt style={styles.dt}>Classe</dt>
          <dd style={styles.dd}>{processo.classe || '—'}</dd>
        </div>

        <div style={styles.field}>
          <dt style={styles.dt}>Assunto</dt>
          <dd style={styles.dd}>{processo.assunto || '—'}</dd>
        </div>

        <div style={styles.field}>
          <dt style={styles.dt}>Valor da Causa</dt>
          <dd style={styles.dd}>{processo.valor_causa || '—'}</dd>
        </div>

        {processo.partes && processo.partes.length > 0 && (
          <div style={styles.field}>
            <dt style={styles.dt}>Partes</dt>
            <dd style={styles.dd}>
              <ul style={styles.partesList}>
                {processo.partes.map((parte, idx) => (
                  <li key={idx} style={styles.parteItem}>
                    <strong>{parte.nome}</strong>
                    {parte.tipo && <span style={styles.parteTipo}> ({parte.tipo})</span>}
                    {parte.polo && <span style={styles.partePolo}> — Polo {parte.polo}</span>}
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        )}

        {processo.ultima_atualizacao && (
          <div style={styles.field}>
            <dt style={styles.dt}>Última Atualização</dt>
            <dd style={styles.dd}>
              {new Date(processo.ultima_atualizacao).toLocaleString('pt-BR')}
            </dd>
          </div>
        )}
      </dl>

      {consultaUrl && (
        <a
          href={consultaUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={styles.externalLink}
        >
          Consultar no site do tribunal ↗
        </a>
      )}
    </section>
  );
}

const styles = {
  container: {
    padding: '1rem',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    marginBottom: '1rem',
  },
  title: {
    margin: '0 0 1rem 0',
    fontSize: '1.25rem',
  },
  empty: {
    color: '#666',
    fontStyle: 'italic',
  },
  dl: {
    margin: 0,
  },
  field: {
    marginBottom: '0.75rem',
  },
  dt: {
    fontWeight: '600',
    fontSize: '0.8rem',
    color: '#555',
    textTransform: 'uppercase',
    marginBottom: '0.125rem',
  },
  dd: {
    margin: 0,
    fontSize: '0.95rem',
  },
  cnj: {
    fontFamily: 'monospace',
    fontWeight: '500',
  },
  partesList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  parteItem: {
    padding: '0.25rem 0',
    borderBottom: '1px solid #f5f5f5',
  },
  parteTipo: {
    color: '#666',
    fontSize: '0.85rem',
  },
  partePolo: {
    color: '#888',
    fontSize: '0.8rem',
  },
  externalLink: {
    display: 'inline-block',
    marginTop: '1rem',
    padding: '0.5rem 1rem',
    backgroundColor: '#e3f2fd',
    color: '#1565c0',
    textDecoration: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    fontWeight: '500',
  },
};

export default ProcessoDetail;
