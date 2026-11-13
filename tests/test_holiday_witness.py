import importlib.util
import sys
import types
from pathlib import Path


class _Decorators:
    @staticmethod
    def write(function):
        return function

    @staticmethod
    def view(function):
        return function


class _UserError(Exception):
    pass


_fake_genlayer = types.ModuleType("genlayer")
_fake_genlayer.gl = types.SimpleNamespace(
    Contract=object,
    public=_Decorators(),
    vm=types.SimpleNamespace(UserError=_UserError),
)
_fake_genlayer.u256 = int
_fake_genlayer.TreeMap = dict

_contract_path = (
    Path(__file__).resolve().parents[1]
    / "contracts"
    / "holiday_witness.py"
)
_previous_genlayer = sys.modules.get("genlayer")
sys.modules["genlayer"] = _fake_genlayer
try:
    _spec = importlib.util.spec_from_file_location(
        "holiday_witness_under_test",
        _contract_path,
    )
    _contract = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_contract)
finally:
    if _previous_genlayer is None:
        sys.modules.pop("genlayer", None)
    else:
        sys.modules["genlayer"] = _previous_genlayer


NAGER_SAMPLE = (
    '[{"date":"2026-01-01","name":"New Year\\u0027s Day",'
    '"localName":"Neujahr","global":true,"counties":null},'
    '{"date":"2026-01-06","name":"Epiphany",'
    '"localName":"Heilige Drei K\\u00f6nige","global":false,'
    '"counties":["DE-BW","DE-BY","DE-ST"]},'
    '{"date":"2026-06-04","name":"Corpus Christi",'
    '"localName":"Fronleichnam","global":false,'
    '"counties":["DE-BW","DE-HE","DE-NW"]},'
    '{"date":"2026-03-08","name":"International Women\\u0027s Day",'
    '"localName":"Internationaler Frauentag","global":false,'
    '"counties":["DE-BE","DE-MV"]}]'
)


def test_clean_date_accepts_standard_and_leap_dates():
    assert _contract._clean_date("2026-06-04") == "2026-06-04"
    assert _contract._clean_date("2000-02-29") == "2000-02-29"


def test_clean_date_rejects_invalid_format():
    try:
        _contract._clean_date("2026-6-04")
    except _UserError:
        return
    raise AssertionError("Invalid date format was accepted")


def test_clean_date_rejects_nonexistent_date():
    try:
        _contract._clean_date("2026-02-29")
    except _UserError:
        return
    raise AssertionError("Nonexistent date was accepted")


def test_extracts_hesse_specific_corpus_christi():
    holidays = _contract._extract_holidays(NAGER_SAMPLE, "2026-06-04")
    assert len(holidays) == 1
    assert holidays[0]["name"] == "Corpus Christi"
    assert holidays[0]["local_name"] == "Fronleichnam"
    assert "DE-HE" in holidays[0]["counties"]


def test_includes_global_public_holiday():
    holidays = _contract._extract_holidays(NAGER_SAMPLE, "2026-01-01")
    assert len(holidays) == 1
    assert holidays[0]["name"] == "New Year's Day"
    assert holidays[0]["global"] is True


def test_excludes_holiday_for_other_states():
    assert _contract._extract_holidays(NAGER_SAMPLE, "2026-01-06") == []
    assert _contract._extract_holidays(NAGER_SAMPLE, "2026-03-08") == []


def test_returns_empty_list_for_date_without_holiday():
    assert _contract._extract_holidays(NAGER_SAMPLE, "2026-06-05") == []


def test_rejects_malformed_json():
    assert _contract._extract_holidays("not-json", "2026-06-04") is None
