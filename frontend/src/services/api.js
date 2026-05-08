import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = formatErrorMessage(error);
    console.error('[API Error]', message, error);
    return Promise.reject({ message, original: error });
  }
);

function formatErrorMessage(error) {
  if (error.response) {
    const { status, data } = error.response;
    if (data && data.erro) return data.erro;
    if (data && data.message) return data.message;
    switch (status) {
      case 400:
        return 'Requisição inválida. Verifique os dados informados.';
      case 404:
        return 'Recurso não encontrado.';
      case 409:
        return 'Processo já cadastrado no sistema.';
      case 500:
        return 'Erro interno do servidor. Tente novamente mais tarde.';
      default:
        return `Erro do servidor (${status}).`;
    }
  }
  if (error.request) {
    return 'Não foi possível conectar ao servidor. Verifique sua conexão.';
  }
  return error.message || 'Erro desconhecido.';
}

// --- Helper functions ---

export function getProcessos() {
  return api.get('/processos');
}

export function getProcesso(id) {
  return api.get(`/processos/${id}`);
}

export function cadastrarProcesso(numeroCnj) {
  return api.post('/processos', { numero_cnj: numeroCnj });
}

export function removerProcesso(id) {
  return api.delete(`/processos/${id}`);
}

export function getMovimentacoes(id) {
  return api.get(`/processos/${id}/movimentacoes`);
}

export function consultaAvulsa(numeroCnj) {
  return api.post('/consulta-avulsa', { numero_cnj: numeroCnj });
}

export function getHealth() {
  return api.get('/health');
}

export function getMonitoramentoStatus() {
  return api.get('/monitoramento/status');
}

export function getTribunais() {
  return api.get('/tribunais');
}

export function buscarPorCPF(cpf, tribunal) {
  return api.post('/busca-cpf', { cpf, tribunal });
}

export function getTribunaisBuscaCPF() {
  return api.get('/busca-cpf/tribunais');
}

export default api;
