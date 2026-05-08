/**
 * Utilitário de formatação e validação de número CNJ no frontend.
 *
 * Formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
 * - NNNNNNN: número sequencial (7 dígitos)
 * - DD: dígito verificador (2 dígitos)
 * - AAAA: ano de ajuizamento (4 dígitos)
 * - J: ramo da justiça (1 dígito)
 * - TR: tribunal (2 dígitos)
 * - OOOO: origem/vara (4 dígitos)
 */

const CNJ_REGEX = /^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$/;

/**
 * Formata um número CNJ para exibição: NNNNNNN-DD.AAAA.J.TR.OOOO
 *
 * Aceita tanto o número já formatado quanto apenas os dígitos (20 dígitos).
 *
 * @param {string} numero - Número CNJ formatado ou apenas dígitos.
 * @returns {string} Número formatado no padrão CNJ, ou a string original se não puder formatar.
 */
export function formatarCNJ(numero) {
  if (!numero || typeof numero !== 'string') {
    return '';
  }

  // Se já está no formato correto, retorna como está
  if (CNJ_REGEX.test(numero)) {
    return numero;
  }

  // Remove caracteres não numéricos
  const digits = numero.replace(/\D/g, '');

  if (digits.length !== 20) {
    return numero;
  }

  // NNNNNNN-DD.AAAA.J.TR.OOOO
  return `${digits.slice(0, 7)}-${digits.slice(7, 9)}.${digits.slice(9, 13)}.${digits.slice(13, 14)}.${digits.slice(14, 16)}.${digits.slice(16, 20)}`;
}

/**
 * Valida se o número está no formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
 *
 * @param {string} numero - String com o número do processo a ser validado.
 * @returns {boolean} true se o formato é válido, false caso contrário.
 */
export function validarCNJ(numero) {
  if (!numero || typeof numero !== 'string') {
    return false;
  }

  return CNJ_REGEX.test(numero);
}

/**
 * Aplica máscara progressiva ao valor de input durante digitação.
 *
 * Adiciona hífens e pontos nas posições corretas conforme o usuário digita,
 * seguindo o padrão NNNNNNN-DD.AAAA.J.TR.OOOO.
 *
 * @param {string} valor - Valor atual do input.
 * @returns {string} Valor com máscara aplicada.
 */
export function mascararInput(valor) {
  if (!valor || typeof valor !== 'string') {
    return '';
  }

  // Remove tudo que não é dígito
  const digits = valor.replace(/\D/g, '');

  // Limita a 20 dígitos
  const limited = digits.slice(0, 20);

  let result = '';

  for (let i = 0; i < limited.length; i++) {
    // Posição 7: adiciona hífen antes
    if (i === 7) {
      result += '-';
    }
    // Posição 9: adiciona ponto antes
    if (i === 9) {
      result += '.';
    }
    // Posição 13: adiciona ponto antes
    if (i === 13) {
      result += '.';
    }
    // Posição 14: adiciona ponto antes
    if (i === 14) {
      result += '.';
    }
    // Posição 16: adiciona ponto antes
    if (i === 16) {
      result += '.';
    }

    result += limited[i];
  }

  return result;
}
