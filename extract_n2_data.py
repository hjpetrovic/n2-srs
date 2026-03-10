"""
N2 NNM Pass One Book — data extraction script.

Outputs n2_data.json matching the N1 app's data format:
  vocabulary:  [{word, reading, en}]           en blank — fill via Jisho later
  grammar:     [{id, pattern, meaning, connection, examples[]}]
  questions:   [{id, sentence, type, options, correct, target}]

Run with:  .venv/bin/python3 extract_n2_data.py
Output:    n2_data.json
"""

import re
import json
import pdfplumber

PDF_PATH = "../Japanese textbooks/N2 NNM Pass One Book.pdf"

OFFSET = 2  # PDF 0-index = book page + OFFSET - 1

def book_to_idx(book_page):
    return book_page + OFFSET - 1

VOCAB_RANGE    = range(book_to_idx(10),  book_to_idx(92))
QUESTION_RANGE = range(book_to_idx(94),  book_to_idx(154))
GRAMMAR_RANGE  = range(book_to_idx(160), book_to_idx(277))

QUESTION_TYPE_MAP = {
    "漢字読み":     "kanji_reading",
    "表記":         "orthography",
    "語形成":       "word_formation",
    "文脈規定":     "vocabulary",
    "言い換え類義": "synonym",
    "用法":         "usage",
}

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


# ──────────────────────────────────────────────────────────
# VOCABULARY
# ──────────────────────────────────────────────────────────

def is_mostly_kana(s):
    kana = sum(1 for c in s if '\u3040' <= c <= '\u30ff' or c in 'ー（）')
    return kana > len(s) * 0.6 and len(s) >= 2

def chars_to_spaced_text(row_chars):
    if not row_chars:
        return ""
    parts = [row_chars[0]['text']]
    for prev, curr in zip(row_chars, row_chars[1:]):
        if curr['x0'] - prev['x1'] > 8:
            parts.append(' ')
        parts.append(curr['text'])
    return "".join(parts)

def split_word_reading(entry):
    """Split 'wordreading' like '穴あな' into ('穴', 'あな')."""
    entry = entry.strip()
    if not entry:
        return None, None
    last_kanji = -1
    for i, ch in enumerate(entry):
        if '\u4e00' <= ch <= '\u9fff' or '\u30a0' <= ch <= '\u30ff' or ch in '々〆〇':
            last_kanji = i
    if last_kanji == -1:
        return entry, ""
    return entry[:last_kanji + 1], entry[last_kanji + 1:].strip()

def extract_vocab(pdf):
    vocab = []
    seen = set()
    for page_idx in VOCAB_RANGE:
        page  = pdf.pages[page_idx]
        chars = [c for c in page.chars if c['size'] >= 8]
        rows  = {}
        for c in chars:
            y = round(c['top'] / 3) * 3
            rows.setdefault(y, []).append(c)
        for y in sorted(rows.keys()):
            row_chars = sorted(rows[y], key=lambda c: c['x0'])
            row_text  = chars_to_spaced_text(row_chars)
            if '□' not in row_text:
                continue
            for part in row_text.split('□'):
                part = part.strip()
                if not part:
                    continue
                if ' ' in part:
                    idx     = part.index(' ')
                    word    = part[:idx].strip()
                    reading = part[idx:].strip().replace(' ', '')
                else:
                    word, reading = split_word_reading(part)
                if not word or not reading:
                    continue
                if not is_mostly_kana(reading):
                    continue
                if re.match(r'^(名詞|動詞|形容詞|副詞|カタカナ|接|まず|これ)', word):
                    continue
                if word in seen:
                    continue
                seen.add(word)
                vocab.append({"word": word, "reading": reading, "en": ""})
    return vocab


# ──────────────────────────────────────────────────────────
# GRAMMAR
# ──────────────────────────────────────────────────────────

def extract_main_text_lines(page):
    chars = [c for c in page.chars if c['size'] >= 8]
    rows  = {}
    for c in chars:
        y = round(c['top'] / 3) * 3
        rows.setdefault(y, []).append(c)
    lines = []
    for y in sorted(rows.keys()):
        row_chars = sorted(rows[y], key=lambda c: c['x0'])
        text = "".join(c['text'] for c in row_chars).strip()
        if text:
            lines.append(text)
    return lines

def extract_grammar(pdf):
    grammar    = []
    all_lines  = []
    for page_idx in GRAMMAR_RANGE:
        all_lines.extend(extract_main_text_lines(pdf.pages[page_idx]))

    entry_re   = re.compile(r'^(\d{2,3})\s*$')
    pattern_re = re.compile(r'^[〜～]')
    example_re = re.compile(r'^([123])\s*(.+)')

    current     = None
    examples    = []
    in_conn     = False
    in_practice = False  # True while inside 問題N exercises within grammar section

    def flush():
        if current and current.get("pattern") and (current.get("meaning") or examples):
            grammar.append({
                "id":         len(grammar) + 1,
                "pattern":    current["pattern"],
                "meaning":    current.get("meaning", ""),
                "connection": current.get("connection", "").strip(),
                "examples":   examples[:3],
            })

    for line in all_lines:
        if re.match(r'^問題\d', line):
            flush(); current = None; examples = []; in_conn = False
            in_practice = True; continue

        # 正答 marks the end of a practice exercise block
        if line.startswith("正答"):
            in_practice = False
            continue

        if entry_re.match(line):
            if in_practice:
                continue  # number inside practice block — not a grammar entry
            flush()
            current  = {"pattern": "", "meaning": "", "connection": ""}
            examples = []; in_conn = False
            continue

        if current is None:
            continue

        if not current["pattern"] and (
            pattern_re.match(line)
            or (len(line) <= 20
                and not line.startswith(("意味", "接続", "※"))
                and not example_re.match(line))
        ):
            current["pattern"] = line; continue

        # 〜 line immediately after pattern = inline meaning gloss (no 意味 label)
        if pattern_re.match(line) and current["pattern"] and not current["meaning"]:
            current["meaning"] = line; continue

        if line.startswith("意味"):
            in_conn = False
            current["meaning"] = (current["meaning"] + " " + line[2:].strip()).strip()
            continue

        if line.startswith("接続"):
            in_conn = True
            current["connection"] = (current["connection"] + " " + line[2:].strip()).strip()
            continue

        m = example_re.match(line)
        if m:
            in_conn = False
            n = int(m.group(1))
            text = m.group(2).strip()
            while len(examples) < n - 1:
                examples.append("")
            if len(examples) < n:
                examples.append(text)
            else:
                examples[n - 1] = (examples[n - 1] + text).strip()
            continue

        if line.startswith("※"):
            current["meaning"] = (current["meaning"] + " " + line).strip()
            in_conn = False; continue

        if in_conn and line and not pattern_re.match(line):
            current["connection"] = (current["connection"] + " " + line).strip()

    flush()
    return grammar


# ──────────────────────────────────────────────────────────
# PRACTICE QUESTIONS
# ──────────────────────────────────────────────────────────

def parse_answer_line(ans_text):
    """Returns {question_num_1indexed: correct_0indexed}."""
    answers = {}
    for m in re.finditer(r'([①-⑮])\s*(\d)', ans_text):
        ch = m.group(1)
        if ch in CIRCLED:
            answers[CIRCLED.index(ch) + 1] = int(m.group(2)) - 1
    return answers

def is_furigana_line(line):
    return bool(re.fullmatch(r'[\u3041-\u3096\u30a0-\u30ffー\s]{1,12}', line))

def find_target_from_underlines(page, sentence):
    underlines  = [l for l in page.lines if abs(l['y0'] - l['y1']) < 2 and l['x1'] - l['x0'] > 3]
    main_chars  = [c for c in page.chars if c['size'] >= 8]
    targets     = []
    for ul in underlines:
        line_top = page.height - ul['y0']
        ul_chars = [
            c for c in main_chars
            if c['x0'] >= ul['x0'] - 2 and c['x1'] <= ul['x1'] + 2
            and abs(c['bottom'] - line_top) < 6
        ]
        if ul_chars:
            word = "".join(c['text'] for c in sorted(ul_chars, key=lambda c: c['x0']))
            if word and word in sentence:
                targets.append(word)
    return targets[0] if len(targets) == 1 else ""

def parse_page_questions(content_lines, current_type):
    """
    Parse a list of content lines into question dicts.
    Returns list of (qnum, {sentence, options}).
    """
    q_num_re       = re.compile(r'^(\d{1,2})$')
    options_inline = re.compile(r'^[1１]\s+(\S+)\s+[2２]\s+(\S+)\s+[3３]\s+(\S+)\s+[4４]\s+(\S+)')
    options_usage  = re.compile(r'^([1-4])\s+(.{6,}[。いうえおんーぞだす])$')

    num_positions = [(i, int(l)) for i, l in enumerate(content_lines) if q_num_re.match(l)]
    if not num_positions:
        return []

    results = []
    for k, (num_pos, qnum) in enumerate(num_positions):
        prev_pos    = num_positions[k-1][0] if k > 0 else -1
        block_start = prev_pos + 1 if k > 0 else 0
        block_end   = num_positions[k+1][0] if k + 1 < len(num_positions) else len(content_lines)

        # Sentence = lines between previous block and this number
        sentence_lines = []
        for i in range(block_start, num_pos):
            l = content_lines[i]
            if is_furigana_line(l):
                continue
            if options_inline.match(l) or options_usage.match(l):
                continue
            sentence_lines.append(l)
        sentence = "".join(sentence_lines).strip()

        # Options = lines after number
        option_lines = [content_lines[i] for i in range(num_pos + 1, block_end)
                        if not is_furigana_line(content_lines[i])]
        opts = []
        for ol in option_lines:
            m = options_inline.match(ol)
            if m:
                opts = [m.group(1), m.group(2), m.group(3), m.group(4)]
                break
        if not opts and current_type == "usage":
            usage_opts = ["", "", "", ""]
            for ol in option_lines:
                m = options_usage.match(ol)
                if m:
                    usage_opts[int(m.group(1)) - 1] = m.group(2).strip()
            if any(usage_opts):
                opts = usage_opts

        if sentence and opts:
            results.append((qnum, {"sentence": sentence, "options": opts}))
    return results

def extract_questions(pdf):
    questions    = []
    current_type = "kanji_reading"
    q_id         = 1

    # Usage questions span 2 pages; buffer them until we see 正答
    usage_buffer = []

    type_intro_re = re.compile(r'^(漢字読み|表記|語形成|文脈規定|言い換え類義|用法)$')
    instruct_re   = re.compile(r'問題\d')
    answer_re     = re.compile(r'^正答(\s+.+|$)')
    noise_re      = re.compile(r'^(JLPT|文字|文法|語彙|\d{2,}$)')

    def emit(q, qnum, answers_dict, page):
        nonlocal q_id
        # answers_dict keyed by 1-based question number
        correct = answers_dict.get(qnum, 0)
        target  = find_target_from_underlines(page, q["sentence"]) \
                  if current_type in ("kanji_reading", "synonym") else ""
        questions.append({
            "id":       q_id,
            "sentence": q["sentence"],
            "type":     current_type,
            "options":  q["options"],
            "correct":  correct,
            "target":   target,
        })
        q_id += 1

    for page_idx in QUESTION_RANGE:
        page = pdf.pages[page_idx]
        text = page.extract_text()
        if not text:
            continue

        raw_lines = [l.strip() for l in text.splitlines()]

        # Detect type change on this page
        for line in raw_lines:
            m = type_intro_re.match(line)
            if m:
                # Flush usage buffer if switching away
                if current_type == "usage" and usage_buffer:
                    usage_buffer.clear()
                current_type = QUESTION_TYPE_MAP[m.group(1)]

        lines = [l for l in raw_lines
                 if l and not noise_re.match(l) and not instruct_re.match(l)]
        if not lines:
            continue

        # Find answer line
        ans_idx = next((i for i, l in enumerate(lines) if answer_re.match(l)), None)

        if ans_idx is not None:
            # Collect full answer text (may span multiple lines for usage)
            ans_text = answer_re.match(lines[ans_idx]).group(1).strip()
            for extra in lines[ans_idx + 1:]:
                if re.search(r'[①-⑮]', extra):
                    ans_text += " " + extra
                else:
                    break
            answers = parse_answer_line(ans_text)
            content_lines = lines[:ans_idx]
        else:
            answers       = {}
            content_lines = lines

        page_qs = parse_page_questions(content_lines, current_type)

        if current_type == "usage":
            usage_buffer.extend(page_qs)
            if ans_idx is not None and answers:
                # Assign answers to all buffered usage questions
                for qnum, q in usage_buffer:
                    emit(q, qnum, answers, page)
                usage_buffer.clear()
        else:
            # Non-usage: sequential mapping (question numbers may start at 1 each page)
            # Normalise: use answers keyed by 1-based sequential index
            if page_qs and answers:
                # Check if answers use sequential 1-based keys matching page order
                seq_answers = {i+1: answers.get(i+1, 0) for i in range(len(page_qs))}
                # If page questions start from >1 (continuation), remap
                first_qnum = page_qs[0][0]
                if first_qnum > 1 and first_qnum in answers:
                    seq_answers = {i+1: answers.get(qnum, 0) for i, (qnum, _) in enumerate(page_qs)}
                for j, (qnum, q) in enumerate(page_qs):
                    correct = seq_answers.get(j + 1, 0)
                    target  = find_target_from_underlines(page, q["sentence"]) \
                              if current_type in ("kanji_reading", "synonym") else ""
                    questions.append({
                        "id":       q_id,
                        "sentence": q["sentence"],
                        "type":     current_type,
                        "options":  q["options"],
                        "correct":  correct,
                        "target":   target,
                    })
                    q_id += 1

    return questions


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────

def main():
    print(f"Opening: {PDF_PATH}")
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"  Pages: {len(pdf.pages)}")

        print("Extracting vocabulary...")
        vocab = extract_vocab(pdf)
        print(f"  → {len(vocab)} words")

        print("Extracting grammar...")
        grammar = extract_grammar(pdf)
        print(f"  → {len(grammar)} patterns")

        print("Extracting questions...")
        questions = extract_questions(pdf)
        print(f"  → {len(questions)} questions")

    data = {"vocabulary": vocab, "grammar": grammar, "questions": questions}
    with open("n2_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\nWrote n2_data.json")

    print("\n── Vocab samples ──")
    for v in vocab[:5]:
        print(f"  {v}")

    print("\n── Grammar samples ──")
    for g in grammar[:3]:
        print(f"  [{g['id']}] {g['pattern']} | {g['meaning'][:50]} | examples:{len(g['examples'])}")

    print("\n── Question samples ──")
    for q in questions[:6]:
        print(f"  [{q['id']}] ({q['type']}) target={q['target']!r} opts={q['options'][:2]}")

    print("\n── Question breakdown ──")
    from collections import Counter
    print(Counter(q["type"] for q in questions))

    missing_target = sum(1 for q in questions if q["type"] in ("kanji_reading","synonym") and not q["target"])
    print(f"\nQuestions missing target (kanji_reading/synonym): {missing_target}")

    short_grammar = [g for g in grammar if len(g["examples"]) < 3]
    print(f"Grammar with < 3 examples: {len(short_grammar)}")

if __name__ == "__main__":
    main()
