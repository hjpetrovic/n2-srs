// SM-2 spaced repetition algorithm
// This file is the source of truth for the algorithm.
// The copy in n1_srs.html must be kept in sync with this.

export function sm2(card, quality) {
  if (quality < 0 || quality > 3) quality = 0;
  const q = [0, 2, 3, 5][quality];
  let { ef, interval, repetitions } = card;
  ef = ef || 2.5; interval = interval || 0; repetitions = repetitions || 0;

  if (q < 3) { repetitions = 0; interval = 1; }
  else {
    if (repetitions === 0) interval = 1;
    else if (repetitions === 1) interval = 3;
    else interval = Math.round(interval * ef);
    repetitions++;
  }
  ef = Math.max(1.3, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)));
  const now = Date.now();
  return { ef, interval, repetitions, nextReview: now + interval * 86400000, lastReviewed: now, lastQuality: quality };
}

// Shuffle the answer options for a card, returning the reordered options and
// the new index of the correct answer within the shuffled array.
export function shuffleOptions(options, correctIdx) {
  const indices = options.map((_, i) => i).sort(() => Math.random() - 0.5);
  return {
    options: indices.map(i => options[i]),
    correctIdx: indices.indexOf(correctIdx),
  };
}

// Parse a sentence into its display parts.
// Returns { type: 'target' | 'blank' | 'plain', ... }
export function parseSentence(sentence, target) {
  if (target && sentence.includes(target)) {
    const parts = sentence.split(target);
    return { type: 'target', before: parts[0], target, after: parts.slice(1).join(target) };
  }
  if (sentence.includes('（') && sentence.includes('）')) {
    const blankMatch = sentence.match(/（[^）]*）/);
    if (blankMatch) {
      const idx = sentence.indexOf(blankMatch[0]);
      return {
        type: 'blank',
        before: sentence.substring(0, idx),
        blank: blankMatch[0],
        after: sentence.substring(idx + blankMatch[0].length),
      };
    }
  }
  return { type: 'plain', sentence };
}
