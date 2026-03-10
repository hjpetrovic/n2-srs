import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

const data = JSON.parse(readFileSync(resolve(__dirname, '../n2_data.json'), 'utf-8'));

const QUESTION_TYPES = ['kanji_reading', 'orthography', 'word_formation', 'vocabulary', 'synonym', 'usage'];

// ─── Vocabulary ─────────────────────────────────────────────────────────────

describe('vocabulary - structure', () => {
  it('has at least 3000 words', () => {
    expect(data.vocabulary.length).toBeGreaterThanOrEqual(3000);
  });

  it('every entry has word and reading', () => {
    const bad = data.vocabulary.filter(v => !v.word || !v.reading);
    expect(bad).toHaveLength(0);
  });

  it('readings are mostly kana', () => {
    const kanaRe = /^[\u3040-\u30ff\uff66-\uff9fー（）]+$/;
    const bad = data.vocabulary.filter(v => v.reading && !kanaRe.test(v.reading));
    // Allow a small tolerance for edge cases
    expect(bad.length).toBeLessThan(data.vocabulary.length * 0.02);
  });

  it('no duplicate words', () => {
    const words = data.vocabulary.map(v => v.word);
    const unique = new Set(words);
    expect(unique.size).toBe(words.length);
  });

  it('en field is present on every entry', () => {
    const missing = data.vocabulary.filter(v => !('en' in v));
    expect(missing).toHaveLength(0);
  });
});

// ─── Grammar ─────────────────────────────────────────────────────────────────

describe('grammar - structure', () => {
  it('has exactly 135 patterns', () => {
    expect(data.grammar.length).toBe(135);
  });

  it('every entry has id, pattern, meaning, connection, examples', () => {
    const bad = data.grammar.filter(
      g => !g.id || !g.pattern || !('meaning' in g) || !('connection' in g) || !Array.isArray(g.examples)
    );
    expect(bad).toHaveLength(0);
  });

  it('ids are sequential from 1', () => {
    data.grammar.forEach((g, i) => expect(g.id).toBe(i + 1));
  });

  it('most patterns start with 〜 or ～', () => {
    const withTilde = data.grammar.filter(g => /^[〜～]/.test(g.pattern));
    expect(withTilde.length).toBeGreaterThan(130);
  });

  it('most entries have at least one example', () => {
    const withExamples = data.grammar.filter(g => g.examples.length > 0);
    expect(withExamples.length).toBeGreaterThan(110);
  });
});

// ─── Questions ───────────────────────────────────────────────────────────────

describe('questions - structure', () => {
  it('has at least 390 questions', () => {
    expect(data.questions.length).toBeGreaterThanOrEqual(390);
  });

  it('every question has required fields', () => {
    const bad = data.questions.filter(
      q => !q.id || !q.sentence || !q.type || !Array.isArray(q.options) || !('correct' in q)
    );
    expect(bad).toHaveLength(0);
  });

  it('every question has exactly 4 options', () => {
    const bad = data.questions.filter(q => q.options.length !== 4);
    expect(bad).toHaveLength(0);
  });

  it('correct index is 0–3 for all questions', () => {
    const bad = data.questions.filter(q => q.correct < 0 || q.correct > 3);
    expect(bad).toHaveLength(0);
  });

  it('all question types are valid N2 types', () => {
    const bad = data.questions.filter(q => !QUESTION_TYPES.includes(q.type));
    expect(bad).toHaveLength(0);
  });

  it('has all 6 question types', () => {
    const found = new Set(data.questions.map(q => q.type));
    QUESTION_TYPES.forEach(t => expect(found.has(t)).toBe(true));
  });

  it('kanji_reading questions have a non-empty target', () => {
    const bad = data.questions.filter(q => q.type === 'kanji_reading' && !q.target);
    expect(bad).toHaveLength(0);
  });

  it('ids are sequential from 1', () => {
    data.questions.forEach((q, i) => expect(q.id).toBe(i + 1));
  });
});
