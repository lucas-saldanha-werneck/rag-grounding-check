import json
from pathlib import Path

from grounding_check.check import check_answer, split_sentences
from grounding_check.cli import main

SRC = {"S1": "Refunds are issued within 14 days. Orders above 500 EUR need approval.",
       "S2": 'The plan includes "priority email support" and a 99.5% uptime target.'}


def kinds(ans):
    return [f.kind for f in check_answer(ans, SRC)]


def test_clean_answer_has_no_findings():
    assert kinds("Refunds are issued within 14 days [S1]. Uptime is 99.5% [S2].") == []


def test_wrong_number():
    assert kinds("Refunds are issued within 30 days [S1].") == ["number_not_in_source"]


def test_fabricated_quote():
    assert kinds('The plan includes "24/7 phone support" [S2].') == ["quote_not_in_source"]


def test_real_quote_passes_and_case_insensitive():
    assert kinds('The plan has "Priority Email Support" [S2].') == []


def test_unknown_citation():
    assert kinds("See the policy [S9].") == ["unknown_citation"]


def test_uncited_sentence():
    assert kinds("Weekend support is available.") == ["uncited_sentence"]


def test_number_checked_against_cited_source_only():
    # 99.5% exists in S2 but the sentence cites S1
    assert kinds("Uptime is 99.5% [S1].") == ["number_not_in_source"]


def test_multiple_citations_pool_evidence():
    assert kinds("Refunds take 14 days and uptime is 99.5% [S1][S2].") == []


def test_split_sentences():
    assert len(split_sentences("One [S1]. Two [S2]. Three [S1].")) == 3


def test_cli_example(capsys):
    case = Path(__file__).parent.parent / "examples" / "case.json"
    assert main([str(case), "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert sorted(f["kind"] for f in out) == [
        "number_not_in_source", "quote_not_in_source", "uncited_sentence", "unknown_citation"]


def test_cli_clean_returns_zero(tmp_path, capsys):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"sources": SRC, "answer": "Refunds are issued within 14 days [S1]."}))
    assert main([str(f)]) == 0
