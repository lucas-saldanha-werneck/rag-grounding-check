# rag-grounding-check

Checks whether a RAG answer matches the sources it cites. It flags wrong numbers, made-up quotes, citations that point nowhere, and sentences with no citation.

Independent demo, not affiliated with Jobgether (the client is not named in the job post). I built it after applying for a Senior AI Developer role that lists RAG and LLM apps.

## The problem

A RAG answer can look sourced and still be wrong. The model writes `[S1]` after a sentence, but S1 says 14 days and the answer says 30. Reading every answer by hand does not scale. This tool does the cheap, mechanical checks first, with no LLM and no network, so it can run in CI on a fixed set of test questions.

## What it checks

For each sentence in the answer:

| Finding | Rule |
|---|---|
| `uncited_sentence` | The sentence has no `[id]` citation. |
| `unknown_citation` | The id is not in the retrieved sources. |
| `quote_not_in_source` | Text in quotes does not appear in the cited sources (case and whitespace ignored). |
| `number_not_in_source` | A number in the sentence does not appear in the cited sources. |

Numbers are checked against the sources the sentence cites, not against all sources. Quoted text is skipped by the number check.

## Run it

Python 3.10+, standard library only.

```sh
pip install -e ".[dev]"
rag-grounding-check examples/case.json          # Markdown report
rag-grounding-check examples/case.json --json   # JSON findings
```

Input is one JSON file: `{"sources": {"S1": "text"}, "answer": "Sentence [S1]."}`. Exit code is 1 if there are findings, 0 if none. `examples/case.json` is invented example data.

On the example, it finds all four kinds: a wrong refund period (30 vs 14 days), a fabricated quote, an uncited sentence and a citation to a source that does not exist.

## What was tested

- 11 offline tests (`pytest -q`) cover each finding type, case-insensitive quotes, per-source number checking, pooled evidence across two citations, and the CLI exit codes. They pass locally and in GitHub Actions.
- The example case produces exactly the four expected findings.

## What was not tested

- No real RAG output. All data is invented.
- No other languages. The sentence splitter and number matcher assume English text with `.` and `,`.
- No paraphrase check. A claim that is reworded but wrong is not caught, and a correct number written as a word ("fourteen") is flagged.
- Decimal and thousands formats (`1,000` vs `1000`) are compared as plain text.
- No large inputs, no performance test.

This is a first filter. It does not replace an LLM judge or a human review.
