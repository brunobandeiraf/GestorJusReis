import { useState, useEffect } from 'react';
import { useProcessos } from '../../context/ProcessoContext';
import { buscarPorCPF, getTribunaisBuscaCPF, cadastrarProcesso } from '../../services/api';

function BuscaCPF() {
  const { processos, fetchProcessos } = useProcessos();
  const [cpf, setCpf] = useState('');
  const [tribunal, setTribunal] = useState('');
  const [tribunais, setTribunais] = useState([]);
  const [resultados, setResultados] = useState(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);
  const [cpfErro, setCpfErro] = useState(null);
  const [monitorando, setMonitorando] = useState({});

  useEffect(() => {
    getTribunaisBuscaCPF()
      .then((res) => {
        const lista = res.data.tribunais || [];
        setTribunais(lista);
        if (lista.length === 1) {
          setTribunal(lista[0].id);
        }
      })
      .catch(() => {
        // silently fail, user can retry
      });
    fetchProcessos();
  }, [fetchProcessos]);

  const aplicarMascara = (valor) => {
    const digitos = valor.replace(/\D/g, '').slice(0, 11);
    if (digitos.length <= 3) return digitos;
    if (digitos.length <= 6) return `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
    if (digitos.length <= 9)
      return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
    return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9)}`;
  };

  const validarCPF = (valor) => {
    const digitos = valor.replace(/\D/g, '');
    if (digitos.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(digitos)) return false;

    let soma = 0;
    for (let i = 0; i < 9; i++) soma += parseInt(digitos[i]) * (10 - i);
    let resto = soma % 11;
    let primeiro = resto < 2 ? 0 : 11 - resto;
    if (parseInt(digitos[9]) !== primeiro) return false;

    soma = 0;
    for (let i = 0; i < 10; i++) soma += parseInt(digitos[i]) * (11 - i);
    resto = soma % 11;
    let segundo = resto < 2 ? 0 : 11 - resto;
    if (parseInt(digitos[10]) !== segundo) return false;

    return true;
  };

  const handleCpfChange = (e) => {
    const masked = aplicarMascara(e.target.value);
    setCpf(masked);
    if (cpfErro) setCpfErro(null);
    if (erro) setErro(null);
  };

  const handleCpfBlur = () => {
    const digitos = cpf.replace(/\D/g, '');
    if (digitos.length > 0 && digitos.length < 11) {
      setCpfErro('CPF deve conter 11 dígitos.');
    } else if (digitos.length === 11 && !validarCPF(cpf)) {
      setCpfErro('CPF inválido. Verifique os dígitos informados.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro(null);
    setCpfErro(null);
    setResultados(null);

    if (!validarCPF(cpf)) {
      setCpfErro('CPF inválido. Verifique os dígitos informados.');
      return;
    }

    if (!tribunal) {
      setErro('Selecione um tribunal para realizar a busca.');
      return;
    }

    setLoading(true);
    try {
      const res = await buscarPorCPF(cpf, tribunal);
      setResultados(res.data);
    } catch (err) {
      setErro(err.message || 'Erro ao realizar busca.');
    } finally {
      setLoading(false);
    }
  };

  const handleMonitorar = async (numeroCnj) => {
    setMonitorando((prev) => ({ ...prev, [numeroCnj]: 'loading' }));
    try {
      await cadastrarProcesso(numeroCnj);
      setMonitorando((prev) => ({ ...prev, [numeroCnj]: 'success' }));
      fetchProcessos();
    } catch (err) {
      setMonitorando((prev) => ({ ...prev, [numeroCnj]: 'error' }));
    }
  };

  const isMonitorado = (numeroCnj) => {
    return processos.some((p) => p.numero_cnj === numeroCnj && p.ativo !== false);
  };

  return (
    <section style={styles.container}>
      <h2 style={styles.title}>Busca por CPF</h2>

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.inputGroup}>
          <label htmlFor="cpf-input" style={styles.label}>CPF</label>
          <input
            id="cpf-input"
            type="text"
            value={cpf}
            onChange={handleCpfChange}
            onBlur={handleCpfBlur}
            placeholder="000.000.000-00"
            style={{
              ...styles.input,
              ...(cpfErro ? styles.inputError : {}),
            }}
            disabled={loading}
            aria-describedby="cpf-help"
          />
          {cpfErro && (
            <small id="cpf-help" style={styles.errorText} role="alert">
              {cpfErro}
            </small>
          )}
        </div>

        <div style={styles.inputGroup}>
          <label htmlFor="tribunal-select" style={styles.label}>Tribunal</label>
          <select
            id="tribunal-select"
            value={tribunal}
            onChange={(e) => setTribunal(e.target.value)}
            style={styles.select}
            disabled={loading}
          >
            <option value="">Selecione...</option>
            {tribunais.map((t) => (
              <option key={t.id} value={t.id}>{t.nome}</option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={loading || !!cpfErro} style={styles.button}>
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </form>

      {loading && (
        <div style={styles.loadingContainer}>
          <div style={styles.spinner} />
          <span>Consultando tribunal...</span>
        </div>
      )}

      {erro && (
        <div role="alert" style={styles.erroBox}>
          {erro}
        </div>
      )}

      {resultados && !loading && (
        <div style={styles.resultados}>
          {resultados.total === 0 ? (
            <p style={styles.vazio}>
              Nenhum processo encontrado para o CPF informado no tribunal selecionado.
            </p>
          ) : (
            <>
              <h3 style={styles.resultadosTitulo}>
                {resultados.total} processo{resultados.total > 1 ? 's' : ''} encontrado{resultados.total > 1 ? 's' : ''}
              </h3>
              <ul style={styles.lista}>
                {resultados.processos.map((proc, idx) => {
                  const jaMonitorado = isMonitorado(proc.numero_cnj) || monitorando[proc.numero_cnj] === 'success';
                  const monitorandoAtual = monitorando[proc.numero_cnj] === 'loading';
                  const erroMonitorar = monitorando[proc.numero_cnj] === 'error';

                  return (
                    <li key={proc.numero_cnj || idx} style={styles.item}>
                      <div style={styles.itemHeader}>
                        <strong style={styles.numeroCnj}>{proc.numero_cnj}</strong>
                        {jaMonitorado ? (
                          <span style={styles.jaMonitorado}>✓ Já monitorado</span>
                        ) : (
                          <button
                            onClick={() => handleMonitorar(proc.numero_cnj)}
                            disabled={monitorandoAtual}
                            style={styles.monitorarBtn}
                          >
                            {monitorandoAtual ? 'Cadastrando...' : 'Monitorar'}
                          </button>
                        )}
                      </div>
                      <div style={styles.itemDetails}>
                        {proc.classe && <span><strong>Classe:</strong> {proc.classe}</span>}
                        {proc.assunto && <span><strong>Assunto:</strong> {proc.assunto}</span>}
                        {proc.vara && <span><strong>Vara:</strong> {proc.vara}</span>}
                        {proc.partes && proc.partes.length > 0 && (
                          <span><strong>Partes:</strong> {proc.partes.join(', ')}</span>
                        )}
                      </div>
                      {erroMonitorar && (
                        <small style={styles.erroMonitorar}>
                          Erro ao cadastrar para monitoramento. Tente novamente.
                        </small>
                      )}
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>
      )}
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
  form: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'flex-end',
    flexWrap: 'wrap',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    flex: '1 1 200px',
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
  inputError: {
    borderColor: '#c62828',
  },
  select: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  button: {
    padding: '0.5rem 1.25rem',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    alignSelf: 'flex-end',
  },
  errorText: {
    marginTop: '0.25rem',
    color: '#c62828',
    fontSize: '0.75rem',
  },
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginTop: '1rem',
    color: '#555',
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid #ccc',
    borderTopColor: '#1976d2',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  erroBox: {
    marginTop: '1rem',
    padding: '0.75rem',
    backgroundColor: '#ffebee',
    color: '#c62828',
    border: '1px solid #ef9a9a',
    borderRadius: '4px',
    fontSize: '0.875rem',
  },
  resultados: {
    marginTop: '1.5rem',
  },
  resultadosTitulo: {
    margin: '0 0 0.75rem 0',
    fontSize: '1rem',
    color: '#333',
  },
  vazio: {
    color: '#666',
    fontStyle: 'italic',
  },
  lista: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  item: {
    padding: '0.75rem',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    marginBottom: '0.5rem',
  },
  itemHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  numeroCnj: {
    fontFamily: 'monospace',
    fontSize: '0.95rem',
  },
  itemDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
    fontSize: '0.85rem',
    color: '#555',
  },
  monitorarBtn: {
    padding: '0.25rem 0.75rem',
    backgroundColor: '#388e3c',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.8rem',
    cursor: 'pointer',
  },
  jaMonitorado: {
    color: '#388e3c',
    fontSize: '0.8rem',
    fontWeight: '600',
  },
  erroMonitorar: {
    color: '#c62828',
    fontSize: '0.75rem',
    marginTop: '0.25rem',
  },
};

export default BuscaCPF;
