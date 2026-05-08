import { useState } from 'react';
import { useProcessos } from '../../context/ProcessoContext';
import { mascararInput, validarCNJ } from '../../utils/cnjFormatter';

function ProcessoForm() {
  const { addProcesso, loading } = useProcessos();
  const [numeroCnj, setNumeroCnj] = useState('');
  const [feedback, setFeedback] = useState(null);

  const handleChange = (e) => {
    const masked = mascararInput(e.target.value);
    setNumeroCnj(masked);
    if (feedback) setFeedback(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validarCNJ(numeroCnj)) {
      setFeedback({
        type: 'error',
        message: 'Número CNJ inválido. Use o formato: NNNNNNN-DD.AAAA.J.TR.OOOO',
      });
      return;
    }

    try {
      await addProcesso(numeroCnj);
      setFeedback({
        type: 'success',
        message: 'Processo cadastrado com sucesso para monitoramento.',
      });
      setNumeroCnj('');
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err.message || 'Erro ao cadastrar processo.',
      });
    }
  };

  return (
    <section style={styles.container}>
      <h2 style={styles.title}>Cadastrar Processo</h2>
      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.inputGroup}>
          <label htmlFor="cnj-input" style={styles.label}>
            Número CNJ
          </label>
          <input
            id="cnj-input"
            type="text"
            value={numeroCnj}
            onChange={handleChange}
            placeholder="0000000-00.0000.0.00.0000"
            style={styles.input}
            disabled={loading}
            aria-describedby="cnj-help"
          />
          <small id="cnj-help" style={styles.help}>
            Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
          </small>
        </div>

        <button type="submit" disabled={loading} style={styles.button}>
          {loading ? 'Cadastrando...' : 'Cadastrar'}
        </button>
      </form>

      {feedback && (
        <div
          role="alert"
          style={{
            ...styles.feedback,
            ...(feedback.type === 'success' ? styles.success : styles.error),
          }}
        >
          {feedback.message}
        </div>
      )}

      <p style={styles.notice}>
        <strong>Nota:</strong> O download de documentos processuais não está
        disponível nesta versão. Apenas dados públicos de movimentação são
        monitorados.
      </p>
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
  form: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'flex-end',
    flexWrap: 'wrap',
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
  help: {
    marginTop: '0.25rem',
    color: '#666',
    fontSize: '0.75rem',
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
  feedback: {
    marginTop: '0.75rem',
    padding: '0.75rem',
    borderRadius: '4px',
    fontSize: '0.875rem',
  },
  success: {
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
    border: '1px solid #a5d6a7',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    border: '1px solid #ef9a9a',
  },
  notice: {
    marginTop: '1rem',
    padding: '0.5rem 0.75rem',
    backgroundColor: '#fff3e0',
    borderRadius: '4px',
    fontSize: '0.8rem',
    color: '#e65100',
  },
};

export default ProcessoForm;
