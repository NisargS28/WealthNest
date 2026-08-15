We tested the CAS parser against a second Detailed CAS document: CAS_02.pdf.

Do NOT redesign the parser and do NOT modify unrelated functionality.

The parser currently produces:
- 73 financial transaction rows
- 0 unparsed transactions
- 67 NAV validation warnings
- Many "Systematic Investment Purchase" rows incorrectly classified as OTHER
- Two "Systematic Investment Purchase - (Reversal)" rows incorrectly parsed

We need to fix these issues carefully.

==================================================
1. FIX SYSTEMATIC INVESTMENT PURCHASE CLASSIFICATION
==================================================

The CAS contains transactions such as:

"Systematic Investment Purchase - 32/136"
"Systematic Investment Purchase - 33/136"
"Systematic Investment Purchase - 34/136"

These are genuine financial PURCHASE transactions.

They must NOT be classified as OTHER.

Parse them as:

transaction_type = PURCHASE
subtype = SIP
is_sip = true

When the description explicitly contains:

32/136

extract:

sip_installment_number = 32
sip_total_installments = 136

Do NOT infer SIP information from dates, recurring amounts, or transaction frequency.

Only extract SIP information that is explicitly present in the CAS text.

For example:

"Systematic Investment Purchase - 32/136"

must produce approximately:

{
    "transaction_type": "PURCHASE",
    "subtype": "SIP",
    "description": "Systematic Investment Purchase - 32/136",
    "is_sip": true,
    "sip_installment_number": 32,
    "sip_total_installments": 136
}

==================================================
2. FIX SIP REVERSAL TRANSACTIONS
==================================================

The CAS contains transactions such as:

"Systematic Investment Purchase - (Reversal)"

These represent a reversal of a SIP purchase.

In the CAS, the reversal row may contain values in parentheses, for example:

(999.95) (0.588) 1,701.0185

The current parser incorrectly extracts this row as something like:

amount = 98.271
units = null
nav = null

This is incorrect.

IMPORTANT:
Do NOT guess the column mapping.

Inspect the actual PDF extraction output and the transaction-table column positions to determine exactly which value represents:

- Amount
- Units
- Price / NAV
- Unit Balance

Understand how the CAS represents reversal transactions before implementing the fix.

The reversal should be represented explicitly as a reversal transaction, for example:

transaction_type = REVERSAL
subtype = SIP

If the existing enum/model architecture has a better appropriate representation, use it, but preserve the financial meaning clearly.

The reversal must correctly affect the portfolio's units.

If the CAS uses negative/parenthesized values, preserve the financial sign correctly in the normalized representation.

Do not convert the reversal into a normal PURCHASE.

Do not classify it as OTHER.

Do not silently discard it.

==================================================
3. IMPORTANT: VERIFY THE BUSINESS MEANING
==================================================

The expected business interpretation is:

SIP purchase
    ↓
Payment/mandate fails, e.g. insufficient bank balance
    ↓
Investment is reversed
    ↓
Units associated with the transaction are reversed

However, do NOT rely solely on this assumption.

Verify the actual transaction representation from CAS_02.pdf before deciding exactly how the reversal should be stored.

The parser must represent what the CAS actually records.

==================================================
4. DO NOT FIX NAV WARNINGS BY SIMPLY INCREASING TOLERANCE
==================================================

CAS_02 currently produces 67 NAV mismatch warnings.

For example, some transactions have:

calculated NAV = amount / units

which differs from the reported Price/Unit.

Before changing the validator tolerance, investigate the root cause.

Check whether the discrepancy is caused by:

1. Decimal precision
2. Rounding
3. Transaction charges
4. Amount representing something different from units × NAV
5. Incorrect column extraction
6. Parenthesized/reversal rows
7. Another legitimate CAS convention

Compare the raw extracted PDF row against the normalized transaction.

Do NOT simply increase tolerance until all warnings disappear.

The validation system must remain meaningful.

==================================================
5. UNIT BALANCE VALIDATION
==================================================

After fixing SIP purchases and reversals, rerun unit-balance reconciliation.

For each folio verify:

previous unit balance
+
purchase units
-
redemption/reversal units
+
switch-in units
-
switch-out units
=
new unit balance

Use the actual transaction semantics from the CAS.

Do not silently modify values to force reconciliation.

==================================================
6. IMPORT PREVIEW
==================================================

After classification is corrected, the import preview must report accurate transaction counts.

It should no longer show something like:

73 transactions
3 purchases
70 OTHER

if those 70 rows are actually SIP purchases.

The counts must reflect the corrected transaction classifications.

==================================================
7. REGRESSION TESTS
==================================================

Add regression tests for:

A. Systematic Investment Purchase

Input:
"Systematic Investment Purchase - 32/136"

Expected:
transaction_type = PURCHASE
subtype = SIP
is_sip = true
sip_installment_number = 32
sip_total_installments = 136

B. SIP without explicit installment number

If the CAS says:
"Systematic Investment Purchase Existing Folio with SIP"

Expected:
transaction_type = PURCHASE
subtype = SIP
is_sip = true
sip_installment_number = null
sip_total_installments = null

Do NOT infer them.

C. SIP reversal

Input:
"Systematic Investment Purchase - (Reversal)"

Expected:
transaction_type = REVERSAL
subtype = SIP

Verify amount, units, NAV, and sign using the actual CAS row.

D. NAV validation

Add a test representing the actual CAS_02 NAV discrepancy.

The test must document the actual reason for the discrepancy before changing validation behavior.

E. Unit balance

Verify that the corrected transactions reconcile with the CAS unit balance.

==================================================
8. IMPORTANT CONSTRAINTS
==================================================

Do NOT:

- Add SIP pattern inference
- Infer future SIP schedules
- Modify unrelated parser behavior
- Build MFapi integration
- Build the portfolio dashboard
- Build authentication
- Add unnecessary system events to JSON
- Hide validation warnings by increasing tolerance blindly
- Silently discard financial transactions

The parser's responsibility is:

CAS PDF
    ↓
Accurate financial transaction data
    ↓
Normalized JSON

The parser should extract facts explicitly represented in the CAS.

Do not invent missing information.

==================================================
9. FINAL VALIDATION
==================================================

After implementation:

1. Run the complete existing test suite.
2. Run the parser against CAS_01.
3. Run the parser against CAS_02.
4. Compare transaction counts before/after.
5. Report:
   - total transactions
   - purchases
   - SIP purchases
   - reversals
   - stamp duty
   - other financial transactions
   - unparsed transactions
   - validation warnings
6. Report every remaining discrepancy.
7. Explain the root cause of any remaining NAV warnings.

Do not declare the parser correct merely because the tests pass.

The final goal is:

"Every financially meaningful row in CAS_01 and CAS_02 is correctly classified and represented, with unit balances reconciled and no financial transaction silently lost."