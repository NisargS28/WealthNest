# WealthNest Project Roadmap

This roadmap outlines the milestones for building a centralized family-level mutual fund portfolio aggregator.

| Phase | Description | Status | Progress | Key Deliverable |
|:---:|---|:---:|:---:|---|
| **00** | **Project Foundation** | ✅ | 100% | Repository setup, testing setup, coding guidelines, CI foundations. |
| **01** | **CAS PDF Ingestion Parser** | ✅ | 100% | Ingestion parser to extract statement metadata, folios, and financial transactions from CAMS/KFintech PDFs. |
| **02** | **Portfolio Reconstruction Engine** | 🚧 | NEXT | Holdings logic computing closing units, invested amounts, redemptions, switches, and reversals. |
| **03** | **NAV/Data Integration** | ⬜ | PLANNED | Integrate historical/realtime NAV APIs (such as MFapi.in) to evaluate current market valuations. |
| **04** | **Import Preview & User Confirmation** | ⬜ | PLANNED | Web flow displaying extracted data, allowing verification and manual adjustments before committing. |
| **05** | **Family Portfolio Model** | ⬜ | PLANNED | Multi-member grouping logic linking individual portfolios into aggregated family views. |
| **06** | **Portfolio Analytics** | ⬜ | PLANNED | Computation of XIRR, CAGR, absolute returns, asset allocation concentration, and SIP trackers. |
| **07** | **Interactive Dashboard** | ⬜ | PLANNED | Interactive frontend representing family holdings, portfolio splits, and investment charts. |
| **08** | **Authentication & Security** | ⬜ | PLANNED | Authentication layer, role-based family access permissions, and secure document handling. |
| **09** | **Automated Portfolio Refresh** | ⬜ | PLANNED | Scheduled tasks to retrieve NAV updates and calculate updated valuations daily. |
| **10** | **Advanced Risk Analytics** | ⬜ | FUTURE | Volatility tracking, benchmark overlap analysis, goal tracking, and tax-harvesting analytics. |

---

## Status Legend
- ✅ **COMPLETED**: The phase is fully coded, validated, and verified.
- 🚧 **IN PROGRESS**: The phase is currently being actively designed or implemented.
- ⬜ **PLANNED**: The phase is documented and scheduled for future development.
- ⚠️ **BLOCKED**: The phase cannot progress due to an open technical dependency.
