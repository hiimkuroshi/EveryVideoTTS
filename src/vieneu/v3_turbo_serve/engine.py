"""
Batched serving engine for v3 Turbo (static batching).

Ties the batched backbone + batched acoustic frame generation into one loop that
advances B requests together:

    prefill(prompts) -> loop { acoustic frame (B) -> EOS check -> backbone step (B) }

Finished requests are masked out (their last frame is kept) and the batch keeps
running until all finish or ``max_new_frames``. Each request's codes are decoded
to a waveform at the end. Pure PyTorch, runs on CUDA (or CPU).
"""
from __future__ import annotations

import logging
import math
import re
from typing import List, Optional

import numpy as np
import torch

from .batched_acoustic import generate_frame_batched
from .batched_backbone import BatchedBackbone
from .._v3_turbo_engine.rep_history import DEFAULT_REP_WINDOW, RepetitionHistory

logger = logging.getLogger("Vieneu.V3TurboServe")

# Guard chống "chunk câm": một row khỏe sinh ≥ ~0.4 frame trên mỗi ký tự phoneme
# (đo thực nghiệm 0.41–1.0); dưới 0.25 gần như chắc chắn là EOS sớm / cụt giữa
# chừng → sinh lại row đó. Độ dài phoneme được tính SAU khi loại các tag markup
# (<en>…</en>, <|emotion_k|>) vì chúng chiếm ký tự nhưng không tốn frame audio.
MIN_FRAMES_PER_PHONE = 0.25
_MARKUP_RE = re.compile(r"<\|emotion_\d+\|>|</?en>")


def _min_expected_frames(phonemes: str) -> int:
    eff_len = len(_MARKUP_RE.sub("", phonemes or ""))
    return max(3, math.ceil(MIN_FRAMES_PER_PHONE * eff_len))


# Chặn-trên đối xứng: trần frame theo độ dài phoneme (24 + 2.0/ký tự, đo trên
# dataset finetune — xem vieneu_utils.core_utils.max_expected_frames). Row ngắn
# bắn trượt stop token thì bị cắt tại trần của CHÍNH row đó thay vì chạy hết
# max_new_frames của cả batch.
from vieneu_utils.core_utils import max_expected_frames


class V3TurboBatchEngine:
    def __init__(self, tts):
        # tts: VieNeuTTSv3Turbo (provides prompt building, embeddings, heads, codec)
        self.tts = tts
        self.model = tts.model
        self.config = tts.config
        self.bb = BatchedBackbone(tts.model)
        self._graphs = {}  # (B, temp, top_k, top_p) -> CudaGraphedFrame (acoustic step)

    def _get_graph(self, B, temperature, top_k, top_p):
        key = (B, round(temperature, 4), top_k, round(top_p, 4))
        if key not in self._graphs:
            from .cudagraph import CudaGraphedFrame
            self._graphs[key] = CudaGraphedFrame(
                self.model, B, temperature=temperature, top_k=top_k, top_p=top_p
            )
        return self._graphs[key]

    @torch.no_grad()
    def _prompt_embeds(self, req) -> torch.Tensor:
        # Each request carries its own reference (speaker_emb + ref_codes) and optional
        # use_ref_codes switch. The speaker anchor is added to every prefill row.
        # A "style" key in the request is accepted but ignored (deprecated): the style
        # is implied by the reference, so the head token is always the natural style.
        style_id = self.tts._resolve_style_id()
        phonemes = req.get("phonemes")
        if phonemes is None:
            from vieneu_utils.phonemize_text import phonemize_text_with_emotions
            phonemes = phonemize_text_with_emotions(req["text"])
        ref_codes = req.get("ref_codes") if req.get("use_ref_codes", True) else None
        spk = self.tts._resolve_speaker_emb(req.get("speaker_emb"))
        prompt_2d = self.tts._build_prompt_2d(phonemes, None, ref_codes, style_id)
        return self.model._build_inputs_embeds(prompt_2d.unsqueeze(0).to(self.tts.device), speaker_emb=spk)[0]  # (T, H)

    @torch.no_grad()
    def generate_batch(
        self,
        requests: List[dict],
        *,
        temperature: float = 0.8,
        top_k: int = 25,
        top_p: float = 0.95,
        repetition_penalty: float = 1.2,
        repetition_window: int = DEFAULT_REP_WINDOW,
        max_new_frames: int = 300,
        use_cudagraph: bool = False,
        max_retries: int = 2,
        frame_cap: bool = True,
    ) -> List[np.ndarray]:
        """Generate a waveform for each request in one batched run.

        ``temperature`` is a scalar applied to every codebook. ``repetition_penalty``
        (default 1.2, matching the single-path engine) down-weights codes already
        produced per row/codebook to avoid repetition artifacts.

        Rows that come back suspiciously short (fewer than ``MIN_FRAMES_PER_PHONE``
        frames per phoneme char — an early-EOS "silent chunk") are regenerated as a
        smaller batch, up to ``max_retries`` times, keeping the longest attempt.
        Set ``max_retries=0`` to disable the guard.

        ``frame_cap=True`` (default) additionally caps each row at its own
        ``max_expected_frames(phonemes)`` — the upper-bound twin of the guard
        above: a short row that misses its stop token gets truncated at a
        length plausible for its text instead of babbling to ``max_new_frames``.

        ``use_cudagraph=True`` captures (and caches) a CUDA graph of the per-frame
        acoustic step for this batch size — big per-step speedup, reused across calls.
        It is ignored when ``repetition_penalty != 1.0`` (the penalty needs dynamic
        per-row history, which a static graph cannot hold).
        """
        # Fill in phonemes up front so the guard can size-check every row (and so
        # retries don't re-phonemize).
        reqs = []
        for r in requests:
            if r.get("phonemes") is None:
                from vieneu_utils.phonemize_text import phonemize_text_with_emotions
                r = {**r, "phonemes": phonemize_text_with_emotions(r["text"])}
            reqs.append(r)

        sampling = dict(
            temperature=temperature, top_k=top_k, top_p=top_p,
            repetition_penalty=repetition_penalty, repetition_window=repetition_window,
            max_new_frames=max_new_frames, use_cudagraph=use_cudagraph,
        )
        # Trần frame RIÊNG từng row (luôn > floor chặn-dưới nên không kích retry).
        caps = ([min(max_new_frames, max_expected_frames(r["phonemes"])) for r in reqs]
                if frame_cap else None)
        codes = self._generate_codes_batch(reqs, frame_caps=caps, **sampling)

        # Guard: re-run rows whose output is too short for their text.
        floors = [_min_expected_frames(r["phonemes"]) for r in reqs]
        for _ in range(max(0, max_retries)):
            bad = [i for i in range(len(reqs)) if len(codes[i]) < floors[i]]
            if not bad:
                break
            logger.warning(
                f"⚠️ v3 Turbo batch: {len(bad)} chunk ngắn bất thường "
                f"(rows {bad}) — đang sinh lại...")
            retry = self._generate_codes_batch(
                [reqs[i] for i in bad],
                frame_caps=[caps[i] for i in bad] if caps is not None else None,
                **sampling)
            for j, i in enumerate(bad):
                if len(retry[j]) > len(codes[i]):
                    codes[i] = retry[j]
        else:
            still_bad = [i for i in range(len(reqs)) if len(codes[i]) < floors[i]]
            if still_bad and max_retries > 0:
                logger.warning(
                    f"⚠️ v3 Turbo batch: rows {still_bad} vẫn ngắn hơn ngưỡng sau "
                    f"{max_retries} lần thử — giữ bản dài nhất.")

        wavs: List[np.ndarray] = []
        for c in codes:
            if len(c):
                wavs.append(self.tts._decode_codes(c.cpu()))
            else:
                wavs.append(np.zeros(0, dtype=np.float32))
        return wavs

    @torch.no_grad()
    def _generate_codes_batch(
        self,
        requests: List[dict],
        *,
        temperature: float = 0.8,
        top_k: int = 25,
        top_p: float = 0.95,
        repetition_penalty: float = 1.2,
        repetition_window: int = DEFAULT_REP_WINDOW,
        max_new_frames: int = 300,
        use_cudagraph: bool = False,
        frame_caps: Optional[List[int]] = None,
    ) -> List[torch.Tensor]:
        """One batched generation pass; returns per-row codes ``(T, n_vq)`` (no decode).

        ``frame_caps[b]`` (nếu có) là trần frame riêng của row ``b`` — chạm trần
        thì row đó coi như xong (mask ra khỏi batch) dù chưa thấy EOS.
        """
        cfg = self.config
        n_vq = cfg.n_vq
        eos_id = cfg.speech_generation_end_token_id
        sgs = cfg.speech_generation_start_token_id
        pad = cfg.audio_pad_token_id
        dev = self.tts.device

        embeds_list = [self._prompt_embeds(r) for r in requests]
        B = len(requests)

        # Per-request speaker anchor, stacked to (B, D), re-added at every decode step
        # (broadcast over the single new row). None when the model has no speaker encoder.
        spk_list = [self.tts._resolve_speaker_emb(r.get("speaker_emb")) for r in requests]
        batch_spk = torch.cat(spk_list, dim=0) if (spk_list and spk_list[0] is not None) else None

        # Per-row, per-codebook sliding-window history for the repetition penalty
        # (matches the single-path decode_one_frame). None when the penalty is disabled.
        history = ([RepetitionHistory(n_vq, repetition_window) for _ in range(B)]
                   if not math.isclose(repetition_penalty, 1.0) else None)
        # CUDA graph bakes in a static step → incompatible with dynamic rep-penalty.
        use_graph = use_cudagraph and dev.type == "cuda" and math.isclose(repetition_penalty, 1.0)
        graphed = self._get_graph(B, temperature, top_k, top_p) if use_graph else None

        h, cache, mask, pos = self.bb.prefill(embeds_list)   # h: (B, H)
        finished = [False] * B
        codes_per_req: List[List[torch.Tensor]] = [[] for _ in range(B)]

        for _ in range(max_new_frames):
            if graphed is not None:
                codes, is_eos = graphed.run(h)               # acoustic frame via CUDA graph
            else:
                codes, prefill_out = generate_frame_batched(
                    self.model, h, temperature=temperature, top_k=top_k, top_p=top_p,
                    repetition_penalty=repetition_penalty, history=history,
                )
                is_eos = (self.model.text_lm_head(prefill_out[:, 0]).float().argmax(-1) == eos_id)
            for b in range(B):
                if not finished[b]:
                    codes_per_req[b].append(codes[b])   # include the EOS frame (matches single path)
                    if bool(is_eos[b]) or (
                        frame_caps is not None and len(codes_per_req[b]) >= frame_caps[b]
                    ):
                        finished[b] = True
            if all(finished):
                break

            # Feed the generated frame back as the next backbone input.
            slot = torch.full((B, 1, n_vq + 1), pad, dtype=torch.long, device=dev)
            slot[:, :, 0] = sgs
            slot[:, 0, 1:] = codes
            se = self.model._build_inputs_embeds(slot, speaker_emb=batch_spk)
            h, cache, mask, pos = self.bb.decode_step(se, cache, mask, pos)

        return [
            torch.stack(codes_per_req[b]) if codes_per_req[b]
            else torch.zeros(0, cfg.n_vq, dtype=torch.long)
            for b in range(B)
        ]
