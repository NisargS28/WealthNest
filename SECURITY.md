# Security Policy

## Sensitive Financial Information Warning

Mutual Fund Consolidated Account Statements (CAS) contain highly sensitive personal and financial information, including:
- Permanent Account Numbers (PAN)
- Bank account details (numbers and IFSC codes)
- Folio numbers and holdings values
- Names, addresses, and email contacts

> [!WARNING]
> **NEVER commit real CAS PDFs, personal financial statements, or raw un-sanitized parsed JSON files to version control.**

### Test Fixture Guidelines
Any PDFs or text files added to `tests/fixtures/` or the repository for testing purposes must be **strictly anonymized and sanitized**. Do not use real bank accounts, real names, or real PAN numbers.

---

## Reporting a Vulnerability

If you discover any security vulnerability in this project (e.g., credential exposure, dependency vulnerabilities, security loopholes), please report it responsibly by contacting the maintainer directly. 

**Do NOT open a public GitHub issue for security vulnerabilities.**

Please email: `nisarg@example.com` (or contact through the maintainer's primary channel). We will investigate and respond to security reports within 48 hours.

---

## Secrets Management
- Always use environment variables for sensitive settings.
- Do not commit `.env` files to git.
- If you use external APIs (e.g. market data or NAV feeds), keep access keys restricted and stored in local, untracked configuration layers.
