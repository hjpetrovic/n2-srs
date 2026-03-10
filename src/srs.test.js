import { describe, it, expect } from 'vitest';
import { sm2, parseSentence, shuffleOptions } from './srs.js';

// ─── SM-2 Algorithm ────────────────────────────────────────────────────────

describe('sm2 - new card defaults', () => {
  it('uses default ef/interval/repetitions when card is empty', () => {
    const result = sm2({}, 2);
    expect(result.ef).not.toBeNaN();
    expect(result.ef).toBeGreaterThanOrEqual(1.3);
    expect(result.interval).toBe(1);
    expect(result.repetitions).toBe(1);
  });
});

describe('sm2 - quality bounds check', () => {
  it('treats quality=-1 as 0 (Again), not NaN', () => {
    const result = sm2({ ef: 2.5, interval: 5, repetitions: 2 }, -1);
    expect(result.ef).not.toBeNaN();
    expect(result.interval).toBe(1);
    expect(result.repetitions).toBe(0);
    expect(result.lastQuality).toBe(0);
  });

  it('treats quality=4 as 0 (Again), not NaN', () => {
    const result = sm2({ ef: 2.5, interval: 5, repetitions: 2 }, 4);
    expect(result.ef).not.toBeNaN();
    expect(result.lastQuality).toBe(0);
  });

  it('treats quality=99 as 0 (Again), not NaN', () => {
    const result = sm2({ ef: 2.5, interval: 5, repetitions: 2 }, 99);
    expect(result.ef).not.toBeNaN();
  });
});

describe('sm2 - Again (quality=0)', () => {
  it('resets repetitions to 0 and interval to 1', () => {
    const result = sm2({ ef: 2.5, interval: 10, repetitions: 3 }, 0);
    expect(result.repetitions).toBe(0);
    expect(result.interval).toBe(1);
  });

  it('lowers ef but not below 1.3', () => {
    const result = sm2({ ef: 1.3, interval: 1, repetitions: 0 }, 0);
    expect(result.ef).toBeGreaterThanOrEqual(1.3);
  });
});

describe('sm2 - Hard (quality=1)', () => {
  it('resets repetitions to 0 and interval to 1', () => {
    const result = sm2({ ef: 2.5, interval: 6, repetitions: 2 }, 1);
    expect(result.repetitions).toBe(0);
    expect(result.interval).toBe(1);
  });
});

describe('sm2 - Good (quality=2)', () => {
  it('first review sets interval to 1 and increments repetitions', () => {
    const result = sm2({ ef: 2.5, interval: 0, repetitions: 0 }, 2);
    expect(result.interval).toBe(1);
    expect(result.repetitions).toBe(1);
  });

  it('second review sets interval to 3', () => {
    const result = sm2({ ef: 2.5, interval: 1, repetitions: 1 }, 2);
    expect(result.interval).toBe(3);
    expect(result.repetitions).toBe(2);
  });

  it('third review multiplies interval by ef', () => {
    const card = { ef: 2.5, interval: 3, repetitions: 2 };
    const result = sm2(card, 2);
    expect(result.interval).toBe(Math.round(3 * 2.5));
    expect(result.repetitions).toBe(3);
  });
});

describe('sm2 - Easy (quality=3)', () => {
  it('increases ef', () => {
    const result = sm2({ ef: 2.5, interval: 0, repetitions: 0 }, 3);
    expect(result.ef).toBeGreaterThan(2.5);
  });

  it('first review sets interval to 1', () => {
    const result = sm2({ ef: 2.5, interval: 0, repetitions: 0 }, 3);
    expect(result.interval).toBe(1);
    expect(result.repetitions).toBe(1);
  });
});

describe('sm2 - ef bounds', () => {
  it('ef never falls below 1.3 no matter how many Again ratings', () => {
    let card = { ef: 2.5, interval: 0, repetitions: 0 };
    for (let i = 0; i < 20; i++) card = sm2(card, 0);
    expect(card.ef).toBeGreaterThanOrEqual(1.3);
  });

  it('ef increases with repeated Easy ratings', () => {
    let card = { ef: 2.5, interval: 0, repetitions: 0 };
    const initial = card.ef;
    for (let i = 0; i < 5; i++) card = sm2(card, 3);
    expect(card.ef).toBeGreaterThan(initial);
  });
});

describe('sm2 - nextReview', () => {
  it('nextReview is in the future', () => {
    const before = Date.now();
    const result = sm2({ ef: 2.5, interval: 1, repetitions: 1 }, 2);
    expect(result.nextReview).toBeGreaterThan(before);
  });

  it('nextReview is interval days from now', () => {
    const result = sm2({ ef: 2.5, interval: 1, repetitions: 1 }, 2);
    const expectedDelta = result.interval * 86400000;
    expect(result.nextReview - result.lastReviewed).toBe(expectedDelta);
  });
});

// ─── parseSentence ─────────────────────────────────────────────────────────

// ─── shuffleOptions ─────────────────────────────────────────────────────────

describe('shuffleOptions - output structure', () => {
  const opts = ['ア', 'イ', 'ウ', 'エ'];

  it('returns the same number of options', () => {
    const result = shuffleOptions(opts, 0);
    expect(result.options).toHaveLength(opts.length);
  });

  it('contains all the original options', () => {
    const result = shuffleOptions(opts, 0);
    expect(result.options.sort()).toEqual([...opts].sort());
  });

  it('correctIdx points to the original correct text', () => {
    for (let correctIdx = 0; correctIdx < opts.length; correctIdx++) {
      const result = shuffleOptions(opts, correctIdx);
      expect(result.options[result.correctIdx]).toBe(opts[correctIdx]);
    }
  });

  it('correctIdx is within valid range', () => {
    const result = shuffleOptions(opts, 2);
    expect(result.correctIdx).toBeGreaterThanOrEqual(0);
    expect(result.correctIdx).toBeLessThan(opts.length);
  });
});

describe('shuffleOptions - randomisation', () => {
  it('produces different orderings across many runs', () => {
    const opts = ['ア', 'イ', 'ウ', 'エ'];
    const orders = new Set();
    for (let i = 0; i < 100; i++) {
      orders.add(shuffleOptions(opts, 0).options.join(','));
    }
    // With 4 options there are 24 permutations; 100 runs should hit more than 1
    expect(orders.size).toBeGreaterThan(1);
  });
});

describe('parseSentence - target word highlight', () => {
  it('identifies a target word in the sentence', () => {
    const result = parseSentence('彼は急いで走った。', '急いで');
    expect(result.type).toBe('target');
    expect(result.before).toBe('彼は');
    expect(result.target).toBe('急いで');
    expect(result.after).toBe('走った。');
  });

  it('returns plain when target not found in sentence', () => {
    const result = parseSentence('彼は走った。', '急いで');
    expect(result.type).toBe('plain');
  });
});

describe('parseSentence - blank slot', () => {
  it('identifies a （　） blank in the sentence', () => {
    const result = parseSentence('彼は（　）走った。', null);
    expect(result.type).toBe('blank');
    expect(result.before).toBe('彼は');
    expect(result.after).toBe('走った。');
  });

  it('captures blank with content inside parentheses', () => {
    const result = parseSentence('今日は（天気）が良い。', null);
    expect(result.type).toBe('blank');
    expect(result.blank).toBe('（天気）');
  });
});

describe('parseSentence - plain sentence', () => {
  it('returns plain when no target and no blank', () => {
    const result = parseSentence('今日はいい天気です。', null);
    expect(result.type).toBe('plain');
    expect(result.sentence).toBe('今日はいい天気です。');
  });
});
