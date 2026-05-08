import { useState } from 'react';
import { mascararInput, validarCNJ } from '../../utils/cnjFormatter';
import { consultaAvulsa } from '../../services/api';
import { useProcessos } from '../../context/ProcessoContext';
import ProcessoDetail from '../ProcessoDetail/index';
import MovimentacaoList from '../MovimentacaoList/index';

function ConsultaAvulsa() {
  const { addProcesso } = useProcessos();
  const [numeroCnj, setNumeroCnj] = useState('');
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cadastrado, setCadastrado] = useState(false);

  const handleChange = (e) => {
    const masked = mascararInput(e.target.value);
    setNumeroCnj(masked);
    if (error) setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validarCNJ(numeroCnj)) {
      setError('Número CNJ inválido. Use o formato: NNNNNNN-DD.AAAA.J.TR.OOOO');
      return;
    }

    setLoading(true);
    setError(null);
    setResultado(null);
    setCadastrado(false);

    try {
      const response = await consultaAvulsa(numeroCnj);
      setResultado(response.data);
    } catch (err) {
      setError(err.message || 'Erro ao consultar processo. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleCadastrar = async () => {
    try {
      setLoading(true);
      await addProcesso(numeroCnj);
      setCadastrado(true);
    } catch (err) {
      setError(err.message || 'Erro ao cadastrar processo para monitoramento.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={styles.container}>
      <h2 style={styles.title}>Consulta Avulsa</h2>
      <p style={styles.description}>
        Consulte dados de um processo sem cadastrá-lo para monitoramento.
      </p>

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.inputGroup}>
          <label htmlFor="consulta-cnj-input" style={styles.label}>
            Número CNJ
          </label>
          <input
            id="consulta-cnj-input"
            type="text"
            value={numeroCnj}
            onChange={handleChange}
            placeholder="0000000-00.0000.0.00.0000"
            style={styles.input}
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading} style={styles.button}>
          {loading ? 'Consultando...' : 'Consultar'}
        </button>
      </form>

      {error && (
        <div role="alert" style={styles.error}>
          {error}
        </div>
      )}

      {resultado && (
        <div style={styles.results}>
          <ProcessoDetail processo={resultado} />
          {resultado.movimentacoes && resultado.movimentacoes.length > 0 && (
            <MovimentacaoList movimentacoes={resultado.movimentacoes} />
          )}

          {!cadastrado ? (
            <button
              onClick={handleCadastrar}
              disabled={loading}
              style={styles.cadastrarBtn}
            >
              Cadastrar para monitoramento
            </button>
          ) : (
            <p style={styles.cadastradoMsg}>
              ✓ Processo cadastrado para monitoramento com sucesso.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

const styles = {
  container: {
    padding: '1rem',
  },
  title: {
    margin: '0 0 0.5rem 0',
    fontSize: '1.5rem',
  },
  description: {
    color: '#555',
    marginBottom: '1rem',
  },
  form: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'flex-end',
    flexWrap: 'wrap',
    marginBottom: '1rem',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    flex: '1 1 300px',
  },
  label: {
    marginBottom: '0.25rem',
    fontWeight: '600',
    fontSize: '0.875rem',
  },
  input: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: 'monospace',
  },
  button: {
    padding: '0.5rem 1.25rem',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
  },
  error: {
    padding: '0.75rem',
    backgroundColor: '#ffebee',
    color: '#c62828',
    border: '1px solid #ef9a9a',
    borderRadius: '4px',
    marginBottom: '1rem',
    fontSize: '0.875rem',
  },
  results: {
    marginTop: '1.5rem',
  },
  cadastrarBtn: {
    marginTop: '1rem',
    padding: '0.5rem 1.25rem',
    backgroundColor: '#388e3c',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
  },
  cadastradoMsg: {
    marginTop: '1rem',
    color: '#2e7d32',
    fontWeight: '500',
  },
};

export default ConsultaAvulsa;
