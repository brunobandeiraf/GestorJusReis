import { describe, it, expect } from 'vitest';
import { formatarCNJ, validarCNJ, mascararInput } from './cnjFormatter';

describe('formatarCNJ', () => {
  it('formats 20 raw digits into CNJ pattern', () => {
    expect(formatarCNJ('00012345620238260100')).toBe('0001234-56.2023.8.26.0100');
  });

  it('returns already formatted number unchanged', () => {
    expect(formatarCNJ('0001234-56.2023.8.26.0100')).toBe('0001234-56.2023.8.26.0100');
  });

  it('returns original string if digit count is not 20', () => {
    expect(formatarCNJ('12345')).toBe('12345');
  });

  it('returns empty string for null/undefined/non-string', () => {
    expect(formatarCNJ(null)).toBe('');
    expect(formatarCNJ(undefined)).toBe('');
    expect(formatarCNJ('')).toBe('');
  });

  it('strips non-digit characters before formatting', () => {
    expect(formatarCNJ('0001234-56.2023.8.26.0100')).toBe('0001234-56.2023.8.26.0100');
  });
});

describe('validarCNJ', () => {
  it('returns true for valid CNJ format', () => {
    expect(validarCNJ('0001234-56.2023.8.26.0100')).toBe(true);
    expect(validarCNJ('1234567-89.2024.5.02.0001')).toBe(true);
  });

  it('returns false for raw digits without formatting', () => {
    expect(validarCNJ('00012345620238260100')).toBe(false);
  });

  it('returns false for incomplete numbers', () => {
    expect(validarCNJ('0001234-56.2023')).toBe(false);
  });

  it('returns false for wrong separators', () => {
    expect(validarCNJ('0001234.56.2023.8.26.0100')).toBe(false);
    expect(validarCNJ('0001234-56-2023.8.26.0100')).toBe(false);
  });

  it('returns false for null/undefined/non-string', () => {
    expect(validarCNJ(null)).toBe(false);
    expect(validarCNJ(undefined)).toBe(false);
    expect(validarCNJ('')).toBe(false);
  });

  it('returns false for letters in the number', () => {
    expect(validarCNJ('ABCDEFG-12.2023.8.26.0100')).toBe(false);
  });
});

describe('mascararInput', () => {
  it('returns empty string for null/undefined', () => {
    expect(mascararInput(null)).toBe('');
    expect(mascararInput(undefined)).toBe('');
    expect(mascararInput('')).toBe('');
  });

  it('allows typing first 7 digits without mask', () => {
    expect(mascararInput('0')).toBe('0');
    expect(mascararInput('00012')).toBe('00012');
    expect(mascararInput('0001234')).toBe('0001234');
  });

  it('adds hyphen after 7th digit', () => {
    expect(mascararInput('00012345')).toBe('0001234-5');
    expect(mascararInput('000123456')).toBe('0001234-56');
  });

  it('adds dot after 9th digit (DD)', () => {
    expect(mascararInput('0001234562')).toBe('0001234-56.2');
    expect(mascararInput('0001234562023')).toBe('0001234-56.2023');
  });

  it('adds dot after 13th digit (AAAA)', () => {
    expect(mascararInput('00012345620238')).toBe('0001234-56.2023.8');
  });

  it('adds dot after 14th digit (J)', () => {
    expect(mascararInput('000123456202382')).toBe('0001234-56.2023.8.2');
    expect(mascararInput('0001234562023826')).toBe('0001234-56.2023.8.26');
  });

  it('adds dot after 16th digit (TR)', () => {
    expect(mascararInput('00012345620238260')).toBe('0001234-56.2023.8.26.0');
  });

  it('produces full formatted number with 20 digits', () => {
    expect(mascararInput('00012345620238260100')).toBe('0001234-56.2023.8.26.0100');
  });

  it('limits input to 20 digits', () => {
    expect(mascararInput('000123456202382601001234')).toBe('0001234-56.2023.8.26.0100');
  });

  it('strips non-digit characters from input', () => {
    expect(mascararInput('0001234-56')).toBe('0001234-56');
  });
});
