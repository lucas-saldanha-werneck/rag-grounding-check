"""Rule-based grounding checks for a RAG answer. No LLM, no network."""
from __future__ import annotations

import re
from dataclasses import dataclass

CITE_RE = re.compile(r"\[([A-Za-z0-9_-]+)\]")
QUOTE_RE = re.compile(r"[\"“]([^\"”]{4,})[\"”]")
NUM_RE = re.compile(r"\d[\d.,]*%?")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])")


@dataclass(frozen=True)
class Finding:
    kind: str  # unknown_citation | uncited_sentence | quote_not_in_source | number_not_in_source
    sentence: str
    detail: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("“", '"').replace("”", '"')).strip().lower()


def _numbers(text: str) -> set[str]:
    return {n.rstrip(".,") for n in NUM_RE.findall(text) if n.rstrip(".,")}


def split_sentences(answer: str) -> list[str]:
    return [s.strip() for s in SENT_RE.split(answer.strip()) if s.strip()]


def check_answer(answer: str, sources: dict[str, str]) -> list[Finding]:
    """Return findings. `sources` maps citation id -> source text."""
    findings: list[Finding] = []
    for sentence in split_sentences(answer):
        ids = CITE_RE.findall(sentence)
        if not ids:
            findings.append(Finding("uncited_sentence", sentence, "no [id] citation"))
            continue
        known = [i for i in ids if i in sources]
        for i in ids:
            if i not in sources:
                findings.append(Finding("unknown_citation", sentence, f"[{i}] is not in the retrieved sources"))
        if not known:
            continue
        evidence = _norm(" ".join(sources[i] for i in known))
        body = CITE_RE.sub("", sentence)
        for q in QUOTE_RE.findall(body):
            if _norm(q) not in evidence:
                findings.append(Finding("quote_not_in_source", sentence, f'quote "{q}" not found in {", ".join(known)}'))
        quote_free = QUOTE_RE.sub("", body)
        src_nums = _numbers(evidence)
        for n in sorted(_numbers(quote_free)):
            if n not in src_nums:
                findings.append(Finding("number_not_in_source", sentence, f"number {n} not found in {', '.join(known)}"))
    return findings


def render_markdown(findings: list[Finding], n_sentences: int) -> str:
    lines = [f"# Grounding report", "", f"{n_sentences} sentences checked, {len(findings)} findings.", ""]
    for f in findings:
        lines.append(f"- **{f.kind}**: {f.detail}\n  > {f.sentence}")
    if not findings:
        lines.append("No findings.")
    return "\n".join(lines) + "\n"
