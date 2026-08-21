import re
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np

# ─── Regex ───────────────────────────────────────────────────────────────────

RE_NEWLINE          = re.compile(r'[\r\n]+')  # dùng chung cho cả v1 và v2
RE_SENTENCE_FINDALL = re.compile(r'[^.!?]+[.!?]*|[.!?]+')

# Một "từ" để đóng gói chunk: coi NGUYÊN một thẻ <en>...</en> là một token không
# thể tách (thẻ chứa khoảng trắng như "<en>u s d</en>" sẽ vỡ nếu .split() theo
# space). Dùng khi chia text ĐÃ normalize (có chèn <en>) thành chunk.
RE_TOKEN_KEEP_EN = re.compile(r'<en>.*?</en>|\S+', re.IGNORECASE | re.DOTALL)


def _tokenize_keep_en(s: str) -> List[str]:
    """Tách ``s`` thành token, giữ NGUYÊN mỗi cụm ``<en>...</en>``."""
    return RE_TOKEN_KEEP_EN.findall(s)

# v1 only
RE_SENTENCE_END = re.compile(r'(?<=[\.\!\?\…])\s+')
RE_MINOR_PUNCT  = re.compile(r'(?<=[\,\;\:\-\–\—])\s+')

# ─── Tách câu nhận biết ngoặc/trích dẫn ──────────────────────────────────────
# Dấu kết câu nằm BÊN TRONG một cặp ngoặc/trích dẫn KHÔNG phải ranh giới câu:
#   Có phải ... kiểu như: "Rồi sao nữa? Mình phải làm đến bao giờ?", đúng không anh?
# là MỘT câu, không phải ba. Cắt theo regex thuần (RE_SENTENCE_END) sẽ vỡ câu này
# thành mảnh, mảnh cuối ", đúng không anh?" mở đầu bằng dấu phẩy — không phải câu.
#
# Cố tình BỎ nháy đơn ' và ’ khỏi danh sách: chúng trùng với dấu lược trong
# "don't" / "l’ordre", sẽ mở ngoặc mà không bao giờ đóng và nuốt phần còn lại.
_OPEN_TO_CLOSE = {
    '(': ')', '[': ']', '{': '}',
    '“': '”', '‘': '’', '«': '»', '‹': '›', '「': '」', '『': '』',
}
_OPENERS = frozenset(_OPEN_TO_CLOSE)
_CLOSERS = frozenset(_OPEN_TO_CLOSE.values())
_SYMMETRIC_QUOTE = '"'   # cùng một ký tự vừa mở vừa đóng -> dùng cờ bật/tắt
_SENT_END_CHARS  = frozenset('.!?…')
# Dấu đóng bám NGAY SAU dấu kết câu vẫn thuộc về câu đó: `bao giờ?"` , `(thế à!)`
_TRAILING_CLOSE = _CLOSERS | frozenset('"\'’”')

# v2 noise cleanup
_NOISE_RULES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'([.!?])[.,;:]+'), r'\1'),
    (re.compile(r'[.,;:]+([.!?])'), r'\1'),
    (re.compile(r'\s+[,;]\s+'),     ' '),
    (re.compile(r' {2,}'),          ' '),
]
_MULTI_PUNCT = re.compile(r'([.!?])\s*[.!?]+')

# ─── Data class ──────────────────────────────────────────────────────────────

@dataclass
class PhoneChunk:
    text: str
    is_sentence_end: bool  # True = kết thúc câu thật | False = cắt nhân tạo

# ─── Audio utils ─────────────────────────────────────────────────────────────

# Im lặng (giây) chèn giữa hai chunk tuỳ RANH GIỚI đã cắt: ngắt đoạn (\n) nghỉ
# dài nhất, hết câu (.!?) nghỉ vừa, ngắt trong câu (,;: hoặc cắt cưỡng bức) gần
# như liền mạch. Dùng cho đường v3 khi có metadata gap từ splitter.
V3_GAP_SILENCE = {"para": 0.35, "sentence": 0.18, "minor": 0.04}

# Trần số frame audio hợp lý cho MỘT chunk theo độ dài phoneme — chặn-trên đối
# xứng với guard chặn-dưới MIN_FRAMES_PER_PHONE=0.25 bên v3_turbo_serve.engine.
# Đo trên dataset pnnbao-ump/vi-tts-v3-finetune-mix (129,790 rows, 2026-08):
# frames/ký-tự-phoneme p50=0.53, p99=1.10, p99.9=1.50; trần 24 + 2.0*len phủ
# 99.9915% rows (11/129,790 vượt). Row rất ngắn có ratio cao vì chi phí cố định
# (bin len<15: max 25 frames) — phần đó nằm trong slack. Chunk ngắn (1-2 từ) hay
# bắn trượt stop token rồi "nói thêm" — trần này cắt cụt phần bịa thay vì để
# chạy hết max_new_frames (300); chunk dài bình thường có trần > 300 nên không
# bị ảnh hưởng. Markup (<en>…</en>, <|emotion_k|>) chiếm ký tự nhưng không tốn
# frame nên bị loại trước khi đo.
MAX_FRAMES_PER_PHONE = 2.0
_FRAME_CAP_SLACK = 24            # frame trừ hao cho lead-in / chi phí cố định
_FRAME_MARKUP_RE = re.compile(r"<\|emotion_\d+\|>|</?en>")

# Codec chạy 12.5 frame/giây. Chunk chỉ có MỘT từ thì công thức tuyến tính vẫn
# quá hào phóng ("chào" -> 40 frame = 3.2s toàn phần bịa), nên chặn cứng ~1 giây.
# Không áp khi có emotion cue (tiếng cười/thở dài tốn frame thật), và chỉ áp cho
# từ có phoneme <= _SINGLE_WORD_MAX_PHONES (một "từ" dài bất thường là do
# normalize dính, không phải từ thật — để công thức thường lo).
SINGLE_WORD_MAX_FRAMES = 13      # ~1s @ 12.5 frame/s
_SINGLE_WORD_MAX_PHONES = 24


def max_expected_frames(phonemes: str) -> int:
    """Số frame TỐI ĐA hợp lý cho chunk có chuỗi ``phonemes`` này."""
    stripped = _FRAME_MARKUP_RE.sub("", phonemes or "")
    eff_len = len(stripped)
    cap = _FRAME_CAP_SLACK + int(np.ceil(MAX_FRAMES_PER_PHONE * eff_len))
    if (
        len(stripped.split()) <= 1
        and eff_len <= _SINGLE_WORD_MAX_PHONES
        and "<|emotion_" not in (phonemes or "")
    ):
        cap = min(cap, SINGLE_WORD_MAX_FRAMES)
    return cap


def gaps_to_silence(gaps: List[str]) -> List[float]:
    """Map list loại-ranh-giới -> list độ dài im lặng (giây) cho ``join_audio_chunks``."""
    return [V3_GAP_SILENCE.get(g, V3_GAP_SILENCE["sentence"]) for g in gaps]


def join_audio_chunks(
    chunks: List[np.ndarray],
    sr: int,
    silence_p: float = 0.0,
    crossfade_p: float = 0.0,
    silence_ps: Optional[List[float]] = None,
) -> np.ndarray:
    """Ghép các chunk audio. ``silence_ps`` (tuỳ chọn) cho im lặng RIÊNG từng khe
    nối — ``silence_ps[i]`` là im lặng (giây) giữa chunk ``i`` và ``i+1`` — dùng để
    nghỉ dài/ngắn khác nhau theo loại ranh giới. Khi truyền ``silence_ps`` thì
    ``silence_p``/``crossfade_p`` bị bỏ qua.
    """
    if not chunks:
        return np.array([], dtype=np.float32)
    if len(chunks) == 1:
        return chunks[0]

    silence_samples   = int(sr * silence_p)
    crossfade_samples = int(sr * crossfade_p)
    final_wav = chunks[0]

    for i in range(1, len(chunks)):
        next_chunk = chunks[i]
        if silence_ps is not None:
            gap_samples = int(sr * silence_ps[i - 1]) if i - 1 < len(silence_ps) else 0
            if gap_samples > 0:
                silence   = np.zeros(gap_samples, dtype=np.float32)
                final_wav = np.concatenate([final_wav, silence, next_chunk])
            else:
                final_wav = np.concatenate([final_wav, next_chunk])
        elif silence_samples > 0:
            silence   = np.zeros(silence_samples, dtype=np.float32)
            final_wav = np.concatenate([final_wav, silence, next_chunk])
        elif crossfade_samples > 0:
            overlap = min(len(final_wav), len(next_chunk), crossfade_samples)
            if overlap > 0:
                fade_out  = np.linspace(1.0, 0.0, overlap, dtype=np.float32)
                fade_in   = np.linspace(0.0, 1.0, overlap, dtype=np.float32)
                blended   = final_wav[-overlap:] * fade_out + next_chunk[:overlap] * fade_in
                final_wav = np.concatenate([final_wav[:-overlap], blended, next_chunk[overlap:]])
            else:
                final_wav = np.concatenate([final_wav, next_chunk])
        else:
            final_wav = np.concatenate([final_wav, next_chunk])

    return final_wav

# ─── v1: split raw text ──────────────────────────────────────────────────────

def _scan_sentences(text: str, quote_aware: bool = True) -> Tuple[List[str], bool]:
    """Quét ``text`` một lượt, cắt ở dấu ``.!?…`` KHÔNG nằm trong ngoặc/trích dẫn.

    Trả ``(sentences, balanced)``; ``balanced=False`` nghĩa là văn bản có ngoặc/
    nháy lệch (thiếu dấu đóng) — caller nên quét lại với ``quote_aware=False``.
    """
    sentences: List[str] = []
    n = len(text)
    start = i = 0
    depth = 0          # độ sâu ngoặc ( [ { “ « …
    in_quote = False   # đang trong "…" (nháy kép thẳng, đối xứng)

    while i < n:
        ch = text[i]
        if quote_aware and ch == _SYMMETRIC_QUOTE:
            in_quote = not in_quote
        elif quote_aware and ch in _OPENERS:
            depth += 1
        elif quote_aware and ch in _CLOSERS:
            if depth:
                depth -= 1
        elif ch in _SENT_END_CHARS and depth == 0 and not in_quote:
            j = i + 1
            while j < n and text[j] in _SENT_END_CHARS:   # nuốt "?!", "..."
                j += 1
            while j < n and text[j] in _TRAILING_CLOSE:   # nuốt dấu đóng bám sau
                j += 1
            # Chỉ là ranh giới câu khi theo sau là khoảng trắng hoặc hết văn bản;
            # nhờ vậy "3.5 triệu" / "8.30 sáng" không bị cắt.
            if j >= n or text[j].isspace():
                sentences.append(text[start:j])
                start = i = j
                continue
            i = j
            continue
        i += 1

    if start < n:
        sentences.append(text[start:])

    return [s.strip() for s in sentences if s.strip()], (depth == 0 and not in_quote)


def split_into_sentences(text: str) -> List[str]:
    """Tách ``text`` thành câu, KHÔNG cắt bên trong ngoặc/trích dẫn.

    Dùng trên text THÔ (trước normalize): normalizer của sea-g2p xoá sạch mọi dấu
    ngoặc (``"…"`` -> ``,``), nên sau normalize thì không còn cách nào phân biệt
    dấu ``?`` kết câu với dấu ``?`` trong câu trích dẫn.

    Nếu văn bản có ngoặc lệch (thiếu dấu đóng) thì quét lại bỏ qua ngoặc, để một
    dấu nháy lạc không nuốt toàn bộ phần còn lại thành một câu khổng lồ.
    """
    if not text:
        return []
    sentences, balanced = _scan_sentences(text, quote_aware=True)
    if not balanced:
        sentences, _ = _scan_sentences(text, quote_aware=False)
    return sentences


# ─── Cắt mảnh dài không còn dấu ngắt: ưu tiên từ nối ─────────────────────────
_CONN_WORDS = frozenset(
    "và nhưng hoặc song rồi nên vì nếu khi để do bởi".split()
)
# Cặp hai từ là MỘT từ nối: cắt trước cả cặp. Cặp cũng là luật CHẶN — không cắt
# lọt vào giữa cặp ("sau | khi") hay ngay sau từ đầu cặp ("cho | đến khi").
_CONN_PAIRS = frozenset([
    ("sau", "khi"), ("trước", "khi"), ("trong", "khi"), ("mỗi", "khi"),
    ("đến", "khi"), ("tới", "khi"), ("cho", "nên"), ("cho", "đến"),
    ("bởi", "vì"), ("nếu", "như"), ("tuy", "nhiên"), ("thế", "nhưng"),
    ("vì", "vậy"), ("vì", "thế"), ("do", "đó"), ("sau", "đó"),
])
_CONN_STRIP = "\"'“”‘’()[]«»…"


def _conn_key(token: str) -> str:
    return token.strip(_CONN_STRIP).lower()


def _natural_cut(words: List[str], start: int, end: int, min_left: int) -> Optional[int]:
    """Tìm ``j`` trong ``(start, end)`` sao cho cắt TRƯỚC ``words[j]`` rơi đúng
    từ nối. Quét lùi từ sát trần về (ưu tiên chunk đầy nhất), dừng khi mảnh trái
    ngắn hơn ``min_left``. Trả ``None`` nếu không có điểm cắt tự nhiên."""
    left = sum(len(w) for w in words[start:end]) + (end - start - 1)
    for j in range(end - 1, start, -1):
        left -= len(words[j]) + 1        # độ dài mảnh trái nếu cắt trước words[j]
        if left < min_left:
            return None
        key, prev = _conn_key(words[j]), _conn_key(words[j - 1])
        if (prev, key) in _CONN_PAIRS or prev in _CONN_WORDS:
            # Giữa một cặp ("sau | khi") hoặc ngay sau từ nối khác ("và | sau
            # đó" bỏ rơi "và" cuối mảnh trái) — điểm đúng là j-1, quét tiếp.
            continue
        nxt = _conn_key(words[j + 1]) if j + 1 < len(words) else ""
        if key in _CONN_WORDS or (key, nxt) in _CONN_PAIRS:
            return j
    return None


def _split_long_part(part: str, max_chars: int) -> List[str]:
    """Cắt một mảnh dài quá ``max_chars`` (không còn dấu ngắt nào để bám) thành
    các mảnh <= ``max_chars`` theo TỪ, ưu tiên cắt trước từ nối (``_CONN_WORDS``/
    ``_CONN_PAIRS``) thay vì chặt sát trần giữa cụm.

    Điểm cắt tự nhiên chỉ được nhận khi mảnh trái >= ``max_chars // 2`` — lùi
    sâu hơn thì chunk vụn ra, mất cái lợi của chunk đầy; không tìm thấy thì cắt
    sát trần như trước. Token ``<en>...</en>`` luôn nguyên vẹn."""
    words = _tokenize_keep_en(part)
    min_left = max_chars // 2
    pieces: List[str] = []
    start = 0
    while start < len(words):
        end, length = start, 0
        while end < len(words):
            add = length + 1 + len(words[end]) if end > start else len(words[end])
            if end > start and add > max_chars:
                break
            length, end = add, end + 1
        if end < len(words):             # còn phần dư -> buộc phải cắt
            cut = _natural_cut(words, start, end, min_left)
            if cut is not None:
                end = cut
            else:
                # Cắt sát trần cũng KHÔNG được lọt giữa cặp từ nối ("cho | đến
                # khi") — lùi qua cả chuỗi cặp chồng lấn, chấp nhận mảnh non
                # trần / bỏ qua min_left, miễn mảnh trái còn >= 1 từ.
                while end > start + 1 and (
                    _conn_key(words[end - 1]), _conn_key(words[end])
                ) in _CONN_PAIRS:
                    end -= 1
        pieces.append(" ".join(words[start:end]))
        start = end
    return pieces


def pack_sentences_into_chunks(sentences: List[str], max_chars: int = 256) -> List[str]:
    """Đóng gói các CÂU đã cho thành chunk <= ``max_chars`` (greedy, giữ thứ tự).

    Câu dài hơn ``max_chars`` mới bị cắt phụ — trước theo dấu ngắt trong câu
    (``,;:``), sau cùng mới theo từ (ưu tiên cắt trước từ nối, xem
    :func:`_split_long_part`).
    """
    final_chunks: List[str] = []
    buffer = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            if buffer:
                final_chunks.append(buffer)
                buffer = ""

            sub_parts = RE_MINOR_PUNCT.split(sentence)
            for part in sub_parts:
                part = part.strip()
                if not part:
                    continue
                if len(buffer) + 1 + len(part) <= max_chars:
                    buffer = (buffer + ' ' + part) if buffer else part
                else:
                    if buffer:
                        final_chunks.append(buffer)
                    buffer = part
                    if len(buffer) > max_chars:
                        pieces = _split_long_part(buffer, max_chars)
                        final_chunks.extend(pieces[:-1])
                        buffer = pieces[-1] if pieces else ""
        else:
            if buffer and len(buffer) + 1 + len(sentence) > max_chars:
                final_chunks.append(buffer)
                buffer = sentence
            else:
                buffer = (buffer + ' ' + sentence) if buffer else sentence

    if buffer:
        final_chunks.append(buffer)

    return [c.strip() for c in final_chunks if c.strip()]


def split_text_into_chunks(text: str, max_chars: int = 256) -> List[str]:
    """Split raw text (chưa phonemize) thành chunks <= max_chars."""
    if not text:
        return []

    final_chunks: List[str] = []
    for para in RE_NEWLINE.split(text.strip()):
        para = para.strip()
        if para:
            final_chunks.extend(
                pack_sentences_into_chunks(split_into_sentences(para), max_chars)
            )
    return final_chunks


def _classify_gap(chunk: str) -> str:
    """Phân loại ranh giới NGAY SAU ``chunk`` dựa trên dấu câu cuối: hết câu
    (``.!?``) -> ``"sentence"``; còn lại (``,;:`` hoặc cắt cưỡng bức giữa câu)
    -> ``"minor"``. Ranh giới ``"para"`` (ngắt đoạn) do caller gán riêng."""
    c = chunk.rstrip()
    return "sentence" if c and c[-1] in ".!?" else "minor"


def split_text_into_chunks_with_gaps(
    text: str, max_chars: int = 256
) -> Tuple[List[str], List[str]]:
    """Như :func:`split_text_into_chunks` nhưng trả kèm loại ranh giới GIỮA các
    chunk để ghép audio nghỉ dài/ngắn khác nhau.

    Trả về ``(chunks, gaps)`` với ``gaps[i] in {"para","sentence","minor"}`` là
    ranh giới giữa ``chunks[i]`` và ``chunks[i+1]`` (``len(gaps) == len(chunks)-1``):
      * ``"para"``     — hai chunk khác ĐOẠN (cách nhau bởi ``\\n``) -> nghỉ dài
      * ``"sentence"`` — hết câu (chunk trái tận cùng ``.!?``)       -> nghỉ vừa
      * ``"minor"``    — ngắt trong câu (``,;:`` / cắt cưỡng bức)     -> gần như liền
    """
    if not text:
        return [], []

    paragraphs = RE_NEWLINE.split(text.strip())
    chunks: List[str] = []
    gaps: List[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_chunks = split_text_into_chunks(para, max_chars=max_chars)
        if not para_chunks:
            continue
        if chunks:                       # ranh giới với đoạn TRƯỚC đó là ngắt đoạn
            gaps.append("para")
        for j, ch in enumerate(para_chunks):
            if j > 0:                    # ranh giới trong CÙNG đoạn: theo dấu câu
                gaps.append(_classify_gap(para_chunks[j - 1]))
            chunks.append(ch)

    return chunks, gaps

# ─── v2 helpers ──────────────────────────────────────────────────────────────

def _pick_strongest(m: re.Match) -> str:
    s = m.group(0)
    return '!' if '!' in s else '?' if '?' in s else '.'


def _clean_phoneme_noise(text: str) -> str:
    for pattern, repl in _NOISE_RULES:
        text = pattern.sub(repl, text)
    return _MULTI_PUNCT.sub(_pick_strongest, text).strip()


def _find_best_split(text: str, max_size: int) -> Tuple[int, bool]:
    mid = max_size // 2
    best_comma_pos, best_comma_dist = -1, max_size
    best_space_pos, best_space_dist = -1, max_size

    for i in range(min(max_size, len(text))):
        ch = text[i]
        if ch == ',':
            d = abs(i - mid)
            if d < best_comma_dist:
                best_comma_dist, best_comma_pos = d, i
        elif ch == ' ':
            d = abs(i - mid)
            if d < best_space_dist:
                best_space_dist, best_space_pos = d, i

    if best_comma_pos != -1:
        return best_comma_pos, True
    if best_space_pos != -1:
        return best_space_pos, False
    return -1, False


def _smart_split_body(text: str, max_chunk_size: int) -> List[str]:
    result: List[str] = []
    stack = [text.strip()]

    while stack:
        seg = stack.pop()
        if not seg:
            continue
        if len(seg) <= max_chunk_size:
            result.append(seg)
            continue

        pos, _ = _find_best_split(seg, max_chunk_size)
        if pos != -1:
            left  = seg[:pos].rstrip()
            right = seg[pos + 1:].lstrip()
        else:
            cut = max_chunk_size
            while cut > 0 and seg[cut - 1] != ' ':
                cut -= 1
            if cut == 0:
                cut = max_chunk_size
            left  = seg[:cut].rstrip()
            right = seg[cut:].lstrip()

        if right:
            stack.append(right)
        if left:
            stack.append(left)

    return result


def _split_sentence(sent: str, max_chunk_size: int) -> List[PhoneChunk]:
    sent = sent.strip()
    if not sent:
        return []

    if sent[-1] in '.!?':
        body, punct = sent[:-1].rstrip(), sent[-1]
    else:
        body, punct = sent, '.'

    if not body:
        return []

    if len(sent) <= max_chunk_size:
        return [PhoneChunk(text=body + punct, is_sentence_end=True)]

    sub_chunks = _smart_split_body(body, max_chunk_size)
    if not sub_chunks:
        return [PhoneChunk(text=punct, is_sentence_end=True)]

    last_idx = len(sub_chunks) - 1
    return [
        PhoneChunk(
            text=chunk + (punct if i == last_idx else '.'),
            is_sentence_end=(i == last_idx),
        )
        for i, chunk in enumerate(sub_chunks)
        if chunk
    ]

# ─── v2: split phoneme string ────────────────────────────────────────────────

def split_into_chunks_v2(
    full_phones: str,
    max_chunk_size: int = 256,
    min_chunk_size: int = 10,
) -> List[PhoneChunk]:
    """
    Phân đoạn chuỗi phoneme thành các PhoneChunk.
      is_sentence_end=True  → kết thúc câu thật → cần silence
      is_sentence_end=False → cắt nhân tạo → không cần silence
    """
    if not full_phones:
        return []

    full_phones = _clean_phoneme_noise(full_phones)

    raw_parts: List[PhoneChunk] = []
    for para in RE_NEWLINE.split(full_phones):
        para = para.strip()
        if not para:
            continue
        for sent in RE_SENTENCE_FINDALL.findall(para):
            sent = sent.strip()
            if sent:
                raw_parts.extend(_split_sentence(sent, max_chunk_size))

    if not raw_parts:
        return []

    merged: List[PhoneChunk] = []
    i, n = 0, len(raw_parts)
    while i < n:
        cur = raw_parts[i]
        while len(cur.text) < min_chunk_size and i + 1 < n:
            nxt       = raw_parts[i + 1]
            candidate = cur.text.rstrip('.!?').rstrip() + ' ' + nxt.text
            if len(candidate) <= max_chunk_size:
                cur = PhoneChunk(text=candidate, is_sentence_end=nxt.is_sentence_end)
                i += 1
            else:
                break
        merged.append(cur)
        i += 1

    if len(merged) >= 2 and len(merged[-1].text) < min_chunk_size:
        last      = merged.pop()
        candidate = merged[-1].text.rstrip('.!?').rstrip() + ' ' + last.text
        if len(candidate) <= max_chunk_size:
            merged[-1] = PhoneChunk(text=candidate, is_sentence_end=last.is_sentence_end)
        else:
            merged.append(last)

    return merged


def get_silence_duration_v2(chunk: PhoneChunk) -> float:
    """
    Silence sau chunk (giây).
      is_sentence_end=False → 0.0s
      kết thúc '!'/'?' → 0.4s
      kết thúc '.' → 0.3s
    """
    if not chunk.is_sentence_end:
        return 0.0
    return 0.4 if chunk.text.strip()[-1] in '!?' else 0.3

# ─── Misc ────────────────────────────────────────────────────────────────────

def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ('1', 'true', 'yes', 'y', 'on')