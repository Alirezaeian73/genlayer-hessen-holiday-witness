# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import hashlib
import json
import re


MAX_RESPONSE_LENGTH = 20000
COUNTRY_CODE = "DE"
REGION_CODE = "DE-HE"


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _clean_date(value: str) -> str:
    if not isinstance(value, str):
        raise gl.vm.UserError("Date must be text in YYYY-MM-DD format")
    date_text = value.strip()
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", date_text)
    if match is None:
        raise gl.vm.UserError("Use date format YYYY-MM-DD")

    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))
    if year < 2000 or year > 2100 or month < 1 or month > 12:
        raise gl.vm.UserError("Date is outside the supported range")

    days_in_month = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    maximum_day = days_in_month[month - 1]
    is_leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    if month == 2 and is_leap_year:
        maximum_day = 29
    if day < 1 or day > maximum_day:
        raise gl.vm.UserError("Date is not a valid calendar date")
    return date_text


def _extract_holidays(payload_text: str, target_date: str):
    if (
        not isinstance(payload_text, str)
        or not payload_text.strip()
        or len(payload_text) > MAX_RESPONSE_LENGTH
    ):
        return None
    try:
        payload = json.loads(payload_text)
    except Exception:
        return None
    if not isinstance(payload, list):
        return None

    matches = []
    for entry in payload:
        if not isinstance(entry, dict):
            return None
        if entry.get("date") != target_date:
            continue

        counties = entry.get("counties")
        is_global = entry.get("global") is True
        is_hesse_holiday = isinstance(counties, list) and REGION_CODE in counties
        if not is_global and not is_hesse_holiday:
            continue

        name = entry.get("name")
        local_name = entry.get("localName")
        if not isinstance(name, str) or not name:
            return None
        if not isinstance(local_name, str) or not local_name:
            return None
        matches.append({
            "date": target_date,
            "name": name,
            "local_name": local_name,
            "global": is_global,
            "counties": counties if isinstance(counties, list) else [],
        })

    matches.sort(key=lambda item: (item["name"], item["local_name"]))
    return matches


class HessenHolidayWitness(gl.Contract):
    check_count: u256
    checks: TreeMap[u256, str]

    def __init__(self):
        self.check_count = 0
        self.checks = TreeMap()

    @gl.public.write
    def check_date(self, local_date: str) -> u256:
        local_date = _clean_date(local_date)
        year = local_date[:4]
        source_url = (
            "https://date.nager.at/api/v3/PublicHolidays/"
            + year
            + "/"
            + COUNTRY_CODE
        )

        def evaluate_source() -> str:
            try:
                response = gl.nondet.web.get(source_url)
                response_text = response.body.decode("utf-8")
            except Exception:
                return _json({"status": "SOURCE_UNAVAILABLE"})

            holidays = _extract_holidays(response_text, local_date)
            if holidays is None:
                return _json({"status": "EXTRACTION_UNCLEAR"})

            return _json({
                "status": "OK",
                "source_url": source_url,
                "response_sha256": hashlib.sha256(
                    response_text.encode("utf-8")
                ).hexdigest(),
                "date": local_date,
                "holidays": holidays,
            })

        principle = (
            "Independently evaluate both results from the returned Nager.Date JSON. "
            "The results must agree on status. For status OK, require exact agreement "
            "on the source URL, queried date, and every matching holiday's English name, local name, "
            "global flag, and county list. A holiday matches only if it is global or "
            "explicitly includes the German state code DE-HE. Ignore response hash "
            "differences only when all required holiday facts agree. Do not infer or "
            "invent a holiday absent from the JSON."
        )
        consensus_output = gl.eq_principle.prompt_comparative(
            evaluate_source,
            principle=principle,
        )

        try:
            if isinstance(consensus_output, str):
                observed = json.loads(consensus_output)
            elif isinstance(consensus_output, dict):
                observed = consensus_output
            else:
                observed = {"status": "EXTRACTION_UNCLEAR"}
        except Exception:
            observed = {"status": "EXTRACTION_UNCLEAR"}

        status = "UNCLEAR"
        holidays = observed.get("holidays", []) if isinstance(observed, dict) else []
        response_sha256 = (
            observed.get("response_sha256", "")
            if isinstance(observed, dict)
            else ""
        )

        if (
            isinstance(observed, dict)
            and observed.get("status") == "SOURCE_UNAVAILABLE"
        ):
            status = "SOURCE_UNAVAILABLE"
        elif (
            isinstance(observed, dict)
            and observed.get("status") == "EXTRACTION_UNCLEAR"
        ):
            status = "UNCLEAR"
        elif (
            isinstance(observed, dict)
            and observed.get("status") == "OK"
            and observed.get("date") == local_date
            and isinstance(holidays, list)
        ):
            valid_matches = True
            for holiday in holidays:
                if not isinstance(holiday, dict):
                    valid_matches = False
                    break
                if holiday.get("date") != local_date:
                    valid_matches = False
                    break
                if not isinstance(holiday.get("name"), str) or not holiday.get("name"):
                    valid_matches = False
                    break
                if (
                    not isinstance(holiday.get("local_name"), str)
                    or not holiday.get("local_name")
                ):
                    valid_matches = False
                    break
                counties = holiday.get("counties", [])
                if not isinstance(counties, list):
                    valid_matches = False
                    break
                if holiday.get("global") is not True and REGION_CODE not in counties:
                    valid_matches = False
                    break

            if valid_matches:
                status = (
                    "PUBLIC_HOLIDAY"
                    if holidays
                    else "NOT_LISTED_AS_PUBLIC_HOLIDAY"
                )

        record_id = self.check_count
        record = {
            "id": int(record_id),
            "date": local_date,
            "country_code": COUNTRY_CODE,
            "region_code": REGION_CODE,
            "status": status,
            "holidays": holidays if isinstance(holidays, list) else [],
            "source_name": "Nager.Date",
            "source_url": source_url,
            "response_sha256": response_sha256,
            "notice": (
                "Nager.Date is a community-maintained data source, not a government authority. "
                "This record is informational and is not legal advice."
            ),
        }
        self.checks[record_id] = _json(record)
        self.check_count += 1
        return record_id

    @gl.public.view
    def get_check(self, check_id: u256) -> str:
        return self.checks.get(check_id, "")

    @gl.public.view
    def get_check_count(self) -> u256:
        return self.check_count
