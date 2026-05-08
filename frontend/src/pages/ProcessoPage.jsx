import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProcesso, getMovimentacoes } from '../services/api';
import ProcessoDetail from '../components/ProcessoDetail/index';
import MovimentacaoList from '../components/MovimentacaoList/index';

function ProcessoPage() {
  const { id } = useParams();
  const [processo, setProcesso] = useState(null);
  const [movimentacoes, setMovimentacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [procRes, movRes] = await Promise.all([
          getProcesso(id),
          getMovimentacoes(id),
        ]);
        setProcesso(procRes.data);
        setMovimentacoes(movRes.data.movimentacoes || movRes.data || []);
      } catch (err) {
        setError(err.message || 'Erro ao carregar dados do processo.');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div style={styles.container}>
        <p>Carregando...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div role="alert" style={styles.error}>
          {error}
        </div>
        <Link to="/" style={styles.backLink}>
          ← Voltar ao Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Link to="/" style={styles.backLink}>
        ← Voltar ao Dashboard
      </Link>
      <ProcessoDetail processo={processo} />
      <MovimentacaoList movimentacoes={movimentacoes} />
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
  },
  error: {
    padding: '0.75rem',
    backgroundColor: '#ffebee',
    color: '#c62828',
    border: '1px solid #ef9a9a',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  backLink: {
    display: 'inline-block',
    marginBottom: '1rem',
    color: '#1976d2',
    textDecoration: 'none',
    fontSize: '0.9rem',
  },
};

export default ProcessoPage;
