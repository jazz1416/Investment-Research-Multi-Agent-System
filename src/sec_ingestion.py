from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Any

import pandas as pd
import requests

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

OUTPUT_COLUMNS = [
    "ticker",
    "company_name",
    "owner_name",
    "owner_title",
    "transaction_date",
    "filing_date",
    "transaction_code",
    "acquired_disposed",
    "shares",
    "price",
    "accession_number",
    "source_url",
]


def _session(user_agent: str) -> requests.Session:
    """Create an SEC-friendly HTTP session."""
    if not user_agent or "@" not in user_agent:
        raise ValueError(
            "SEC_USER_AGENT must identify the application and include a contact email."
        )

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }
    )
    return session


def _get_json(
    session: requests.Session,
    url: str,
    sleep_seconds: float,
) -> dict[str, Any]:
    """GET a JSON resource while respecting a small delay between SEC requests."""
    response = session.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(sleep_seconds)
    return response.json()


def _get_text(
    session: requests.Session,
    url: str,
    sleep_seconds: float,
) -> str:
    """GET a text/XML resource while respecting a small SEC request delay."""
    response = session.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(sleep_seconds)
    return response.text


def get_ticker_cik_map(
    user_agent: str,
    sleep_seconds: float = 0.12,
) -> dict[str, str]:
    """Return a mapping like {'AAPL': '0000320193'}."""
    session = _session(user_agent)

    # company_tickers.json is served from www.sec.gov.
    payload = _get_json(session, TICKER_MAP_URL, sleep_seconds)

    return {
        item["ticker"].upper(): str(item["cik_str"]).zfill(10)
        for item in payload.values()
    }


def _issuer_submissions(
    cik: str,
    user_agent: str,
    sleep_seconds: float,
) -> dict[str, Any]:
    """Load the SEC submissions JSON for an issuer."""
    session = _session(user_agent)

    # data.sec.gov uses the same SEC User-Agent policy but a different host.
    session.headers.pop("Host", None)

    url = SUBMISSIONS_URL.format(cik=cik)
    return _get_json(session, url, sleep_seconds)


def _recent_form4_filings(
    submissions: dict[str, Any],
    limit: int,
) -> list[dict[str, str]]:
    """Extract recent Form 4 / Form 4-A metadata from submissions JSON."""
    recent = submissions.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])

    filings: list[dict[str, str]] = []

    for form, accession, filing_date in zip(
        forms,
        accessions,
        filing_dates,
        strict=False,
    ):
        if form not in {"4", "4/A"}:
            continue

        filings.append(
            {
                "form": form,
                "accession_number": accession,
                "filing_date": filing_date,
            }
        )

        if len(filings) >= limit:
            break

    return filings


def _filing_directory_url(cik: str, accession_number: str) -> str:
    """Return the SEC Archives directory URL for a filing."""
    cik_no_leading_zeros = str(int(cik))
    accession_no_dashes = accession_number.replace("-", "")

    return (
        f"{ARCHIVES_BASE_URL}/"
        f"{cik_no_leading_zeros}/"
        f"{accession_no_dashes}"
    )


def _find_ownership_xml_url(
    session: requests.Session,
    cik: str,
    accession_number: str,
    sleep_seconds: float,
) -> str:
    """Find the raw ownership XML file from a filing's index.json."""
    directory_url = _filing_directory_url(cik, accession_number)
    index_url = f"{directory_url}/index.json"

    payload = _get_json(session, index_url, sleep_seconds)
    items = payload.get("directory", {}).get("item", [])

    names = [
        item.get("name", "")
        for item in items
        if item.get("name")
    ]

    # Most ownership filings use form4.xml. Prefer it explicitly.
    preferred_names = [
        name
        for name in names
        if name.lower() == "form4.xml"
    ]

    if preferred_names:
        return f"{directory_url}/{preferred_names[0]}"

    # Fallback: use an XML file that is not an index/XSD file.
    xml_candidates = [
        name
        for name in names
        if name.lower().endswith(".xml")
        and "index" not in name.lower()
        and not name.lower().endswith(".xsd")
    ]

    if not xml_candidates:
        raise ValueError(
            f"No ownership XML found for accession {accession_number}. "
            f"Files in filing directory: {names}"
        )

    return f"{directory_url}/{xml_candidates[0]}"


def _strip_namespaces(root: ET.Element) -> None:
    """Remove XML namespaces so tag lookup is consistent."""
    for element in root.iter():
        if "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]


def _text(
    parent: ET.Element | None,
    path: str,
) -> str | None:
    """Safely return stripped text from a nested XML path."""
    if parent is None:
        return None

    element = parent.find(path)
    if element is None or element.text is None:
        return None

    value = element.text.strip()
    return value if value else None


def _number(
    parent: ET.Element | None,
    path: str,
) -> float | None:
    """Safely parse a numeric value from XML."""
    value = _text(parent, path)

    if value is None:
        return None

    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _owner_title(owner: ET.Element) -> str | None:
    """Create a readable owner role/title from Form 4 relationship fields."""
    relationship = owner.find("reportingOwnerRelationship")
    if relationship is None:
        return None

    officer_title = _text(relationship, "officerTitle")
    if officer_title:
        return officer_title

    roles: list[str] = []

    role_fields = [
        ("isDirector", "Director"),
        ("isOfficer", "Officer"),
        ("isTenPercentOwner", "10% Owner"),
        ("isOther", "Other"),
    ]

    for field, label in role_fields:
        value = _text(relationship, field)
        if value in {"1", "true", "TRUE"}:
            roles.append(label)

    return ", ".join(roles) if roles else None


def _transaction_rows(
    root: ET.Element,
    ticker: str,
    company_name: str | None,
    filing_date: str,
    accession_number: str,
    source_url: str,
) -> list[dict[str, Any]]:
    """Flatten ownership XML transactions into row dictionaries."""
    owners = root.findall("reportingOwner")

    owner_records: list[tuple[str | None, str | None]] = []
    for owner in owners:
        owner_name = _text(
            owner,
            "reportingOwnerId/rptOwnerName",
        )
        owner_records.append(
            (
                owner_name,
                _owner_title(owner),
            )
        )

    if not owner_records:
        owner_records = [(None, None)]

    transactions: list[ET.Element] = []
    transactions.extend(
        root.findall(
            "nonDerivativeTable/nonDerivativeTransaction"
        )
    )
    transactions.extend(
        root.findall(
            "derivativeTable/derivativeTransaction"
        )
    )

    rows: list[dict[str, Any]] = []

    for transaction in transactions:
        transaction_date = _text(
            transaction,
            "transactionDate/value",
        )
        transaction_code = _text(
            transaction,
            "transactionCoding/transactionCode",
        )
        shares = _number(
            transaction,
            "transactionAmounts/transactionShares/value",
        )
        price = _number(
            transaction,
            "transactionAmounts/transactionPricePerShare/value",
        )
        acquired_disposed = _text(
            transaction,
            "transactionAmounts/transactionAcquiredDisposedCode/value",
        )

        for owner_name, owner_title in owner_records:
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": company_name,
                    "owner_name": owner_name,
                    "owner_title": owner_title,
                    "transaction_date": transaction_date,
                    "filing_date": filing_date,
                    "transaction_code": transaction_code,
                    "acquired_disposed": acquired_disposed,
                    "shares": shares,
                    "price": price,
                    "accession_number": accession_number,
                    "source_url": source_url,
                }
            )

    return rows


def _parse_ownership_xml(
    xml_text: str,
    ticker: str,
    fallback_company_name: str | None,
    filing_date: str,
    accession_number: str,
    source_url: str,
) -> list[dict[str, Any]]:
    """Parse one raw Form 4 ownership XML document."""
    root = ET.fromstring(xml_text)
    _strip_namespaces(root)

    if root.tag != "ownershipDocument":
        raise ValueError(
            f"Expected ownershipDocument root, received {root.tag!r}"
        )

    company_name = (
        _text(root, "issuer/issuerName")
        or fallback_company_name
    )

    return _transaction_rows(
        root=root,
        ticker=ticker,
        company_name=company_name,
        filing_date=filing_date,
        accession_number=accession_number,
        source_url=source_url,
    )


def fetch_form4_transactions(
    tickers: list[str],
    user_agent: str,
    filings_per_ticker: int = 20,
    sleep_seconds: float = 0.12,
) -> pd.DataFrame:
    """Fetch recent SEC Form 4 transactions for one or more tickers."""
    ticker_map = get_ticker_cik_map(
        user_agent=user_agent,
        sleep_seconds=sleep_seconds,
    )

    archive_session = _session(user_agent)
    all_rows: list[dict[str, Any]] = []

    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()

        cik = ticker_map.get(ticker)
        if cik is None:
            print(f"SEC: ticker not found in SEC ticker map: {ticker}")
            continue

        submissions = _issuer_submissions(
            cik=cik,
            user_agent=user_agent,
            sleep_seconds=sleep_seconds,
        )

        company_name = submissions.get("name")

        filings = _recent_form4_filings(
            submissions=submissions,
            limit=filings_per_ticker,
        )

        print(
            f"SEC: {ticker} | CIK {cik} | "
            f"{len(filings)} recent Form 4 filing(s)"
        )

        for filing in filings:
            accession_number = filing["accession_number"]

            try:
                xml_url = _find_ownership_xml_url(
                    session=archive_session,
                    cik=cik,
                    accession_number=accession_number,
                    sleep_seconds=sleep_seconds,
                )

                xml_text = _get_text(
                    archive_session,
                    xml_url,
                    sleep_seconds,
                )

                rows = _parse_ownership_xml(
                    xml_text=xml_text,
                    ticker=ticker,
                    fallback_company_name=company_name,
                    filing_date=filing["filing_date"],
                    accession_number=accession_number,
                    source_url=xml_url,
                )

                all_rows.extend(rows)

                print(
                    f"SEC: parsed {ticker} {accession_number} "
                    f"({len(rows)} transaction row(s))"
                )

            except (
                requests.RequestException,
                ET.ParseError,
                ValueError,
            ) as exc:
                print(
                    f"SEC: failed {ticker} {accession_number}: {exc}"
                )

    if not all_rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    result = pd.DataFrame(all_rows)

    for column in OUTPUT_COLUMNS:
        if column not in result.columns:
            result[column] = pd.NA

    return result[OUTPUT_COLUMNS].reset_index(drop=True)
