# Phase 03: NAV & Market Data Integration

## Objective
Introduce an external data layer to retrieve real-time and historical Mutual Fund Net Asset Values (NAV). Integrate this data with the reconstructed portfolio to calculate the current market valuation without mutating the original transaction history.

## Scope
- Abstract provider interface for NAV retrieval.
- Implementation of MFapi.in as the primary provider.
- Scheme mapping system prioritizing ISIN over exact name/fuzzy matching.
- Caching layer to eliminate duplicate API requests.
- Valuation Engine to calculate `current_value` across all folios using Decimal arithmetic.

## Architecture
The NAV Engine (`nav-engine/`) runs as a standalone CLI processing `portfolio_reconstructed.json`.
- **`app/provider`**: `NAVProvider` abstract base class and `MFAPIProvider` implementation.
- **`app/mapper`**: `SchemeMasterIndex` downloads the full list of Indian mutual funds and indexes them by ISIN and exact name. `SchemeMapper` maps CAS schemes to provider scheme codes.
- **`app/cache`**: `NAVCache` caches API results to disk to avoid rate-limiting and redundant requests.
- **`app/valuation`**: `ValuationEngine` executes the logic to fetch NAVs, calculate values, and assemble the final `portfolio_valued.json`.

## Provider Design
The system uses **MFapi.in** which requires no authentication and provides historical and latest NAV data updated 6 times a day. If MFapi needs to be replaced later, a new class inheriting from `NAVProvider` can be swapped into `main.py` without rewriting the mapping or valuation logic.

## Scheme Mapping Strategy
Schemes from the CAS are matched to the MFapi scheme database using the following priority:
1. **ISIN**: Exact match using the 12-character identifier (e.g., `INF209K01LF3`).
2. **Exact Name**: Matches the CAS scheme name precisely to the MFapi database.
3. **API Search**: Uses the first 5 words of the scheme name to search via the API.
4. **Fuzzy Matching**: Disambiguates search results using string similarity algorithms (requires >85% confidence).

Ambiguous matches (>60% but <85%) are flagged as `REQUIRES_REVIEW`.

## NAV Data Model
All financial data is handled natively as Python `Decimal` objects.
Output model is `ValuationResult`, producing a completely separate `portfolio_valued.json` state.
The total `current_value` always includes all successfully mapped and fetched schemes.

## Caching
The engine stores a local `mfapi_master.json` which is refreshed every 24 hours. Individual NAV requests are cached in `nav_cache.json`. If an identical scheme request occurs within the same day, the cache serves the response, reducing API overhead.

## Data Freshness & Error Handling
NAVs older than 5 calendar days are flagged as `STALE_DATA`.
API errors or unmatched schemes are surfaced explicitly via `NAVStatus` (`SCHEME_UNMATCHED`, `API_ERROR`, `NAV_UNAVAILABLE`).
Unavailable schemes do NOT default to `0` value. They are excluded from the `current_value` sum but tracked explicitly in the summary.

## Completion Criteria
- [x] ISIN parsing fix applied to CAS parser (Aditya Birla ISIN extraction).
- [x] MFAPI integration complete and working.
- [x] Caching and Indexing implemented.
- [x] Valuation Engine deterministic execution.
- [x] 19 Unit/Integration tests passing offline.
- [x] Live provider API test isolated and passing.
- [x] Valuation generated for `CAS_01` and `CAS_02`.
