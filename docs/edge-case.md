# RupeeRadar — Edge Cases & Corner Cases

> **Project:** AI-Powered Personal Finance Assistant  
> **Source:** docs/architecture.md, docs/implementation-plan.md  
> **Version:** 1.0

---

## Table of Contents

1. [File Ingestion & Upload](#1-file-ingestion--upload)
2. [Transaction Parsing](#2-transaction-parsing)
3. [Cleaning & Normalization](#3-cleaning--normalization)
4. [AI Categorization](#4-ai-categorization)
5. [Recurring Detection](#5-recurring-detection)
6. [Financial Metrics](#6-financial-metrics)
7. [Insight Generation](#7-insight-generation)
8. [Report Generation](#8-report-generation)
9. [Frontend / UI](#9-frontend--ui)
10. [API & Backend](#10-api--backend)
11. [Async Job Processing](#11-async-job-processing)
12. [Privacy & Security](#12-privacy--security)
13. [Deployment & Environment](#13-deployment--environment)

---

## 1. File Ingestion & Upload

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 1.1 | **Empty file (0 bytes)** | Reject with clear error: "The uploaded file is empty." | 1 |
| 1.2 | **Wrong file format** (image, .exe, .txt, .zip) | Reject with supported format list: "Please upload a CSV or PDF file." | 1 |
| 1.3 | **Corrupted/invalid file** | Catch parse exception, return error: "Unable to read file. It may be corrupted." | 1 |
| 1.4 | **Very large file (>10 MB)** | Reject with size limit message. Configurable limit in `core/config.py`. | 1 |
| 1.5 | **Password-protected PDF** | Catch read error, return: "PDF is password-protected. Please upload an unprotected file." | 1 |
| 1.6 | **Scanned PDF (image-based, no text layer)** | Attempt OCR fallback or return: "PDF appears to be a scanned image. OCR support is limited." | 1 |
| 1.7 | **CSV with no transactions** (headers only) | Accept but return zero transactions with appropriate message: "No transaction data found." | 1 |
| 1.8 | **CSV with BOM character** | Strip BOM (Byte Order Mark) before parsing to avoid column detection failure. | 1 |
| 1.9 | **CSV with different encodings** (UTF-8, UTF-16, ISO-8859-1) | Try UTF-8 first, fallback to chardet auto-detection, then ISO-8859-1. | 1 |
| 1.10 | **Unicode text in descriptions** (Hindi, Tamil, mixed scripts) | Preserve Unicode through pipeline; ensure PDF report fonts support Devanagari/Tamil. | 1, 3 |
| 1.11 | **Multiple files uploaded simultaneously** | Process first file, ignore subsequent; or process sequentially with separate job_ids. | 1 |
| 1.12 | **Same file uploaded twice** | Deduplicate by transaction hash; report: "X duplicate transactions skipped." | 1 |
| 1.13 | **CSV with no headers** | Attempt heuristics (first row might be data); fallback to column position detection. | 1 |
| 1.14 | **CSV with inconsistent delimiter** (`,` vs `;` vs `tab`) | Auto-detect delimiter using sniffer; if ambiguous, return with sample preview. | 1 |
| 1.15 | **XLSX file uploaded** (not in supported list) | Initially reject; consider adding XLSX support in future iterations. | 1 |

---

## 2. Transaction Parsing

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 2.1 | **Different date formats** (DD/MM/YYYY, MM/DD/YYYY, DD-MMM-YYYY, YYYYMMDD, etc.) | Normalize all to YYYY-MM-DD. Use date parser library with format inference. Flag ambiguous dates (e.g., 03/04/2025) to user. | 1 |
| 2.2 | **Different amount formats** (₹1,234.56, ₹1.234,56, 1234.56, 1,234, 1.234,56) | Strip currency symbols, detect decimal separator (`.` vs `,`), parse to float. | 1 |
| 2.3 | **Negative amounts vs "Dr"/"Cr" indicators** | If column has signed numbers, debits = negative, credits = positive. If column has Dr/Cr text, convert accordingly. Standardize to `type` field. | 1 |
| 2.4 | **Missing amounts** | Flag as suspicious, exclude from metrics, display with "Amount missing" badge. | 1 |
| 2.5 | **Null/empty descriptions** | Keep as empty string; merchant extraction will return None. Display as "(No description)". | 1 |
| 2.6 | **Very long descriptions (>500 chars)** | Truncate for display; keep full text in `original_description`. | 1 |
| 2.7 | **Descriptions with only special characters** ("****", "---", "!!") | Keep as-is; category will likely fall to "Other". | 2 |
| 2.8 | **Duplicate transactions** (identical date, description, amount) | Deduplicate via transaction_hash (MD5 of date+description+amount). Keep first occurrence. | 1 |
| 2.9 | **Future-dated transactions** | Flag as suspicious. Include in list but highlight with warning badge. | 1 |
| 2.10 | **Very old transactions** (decades ago, e.g., 1990) | Parse and store as-is. Don't reject — user may have historical data. | 1 |
| 2.11 | **Missing date field** | Flag as invalid. Cannot include in time-based metrics or recurring detection. | 1 |
| 2.12 | **Multiple currencies in one statement** (INR + USD transactions) | Flag for user attention. Compute metrics separately per currency or convert using exchange rate from the date. | 1 |
| 2.13 | **Reversed debit/credit indicators** | Auto-detect if total balance change contradicts indicator; flag for manual review. | 1 |
| 2.14 | **Extra columns not in expected schema** | Silently ignore extra columns; warn in processing log but don't fail. | 1 |
| 2.15 | **Header rows mixed with data** | Detect and skip re-occurring header rows mid-file. | 1 |
| 2.16 | **Transaction with amount 0** | Include in list but zero amounts will not meaningfully contribute to metrics. Flag if numerous. | 1 |
| 2.17 | **Date appears as Excel serial number** (e.g., 45000 instead of 2023-03-15) | Detect numeric dates in date column and convert from Excel epoch. | 1 |

---

## 3. Cleaning & Normalization

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 3.1 | **Merchant names with random suffixes** ("Swiggy\*12345", "Swiggy\*99999") | Normalize to base merchant name ("Swiggy") by stripping trailing `*` codes. | 1 |
| 3.2 | **UPI transaction IDs in descriptions** ("paytm@upi", "googlepay@upi", "upi@icici") | Extract meaningful merchant name if present; else categorize as transfer. | 1 |
| 3.3 | **Multiple merchants in one description** ("Zomato/ Swiggy refund") | Take first meaningful merchant; or pass full text to AI categorizer. | 1, 2 |
| 3.4 | **Transfers between own accounts** | Detect via keywords ("transfer", "IMPS", "NEFT", "RTGS" to same name). Option to exclude from spend/income metrics. | 1 |
| 3.5 | **Refunds** — negative debit or positive credit? | Standardize: refunds are positive credits. Deduct from category spend, not from income. | 1 |
| 3.6 | **Cashback/reward credits** | Categorize as "Other" or "Income" depending on amount and context. Small credits (<₹100) likely cashback. | 2 |
| 3.7 | **GST/tax amounts as separate line items** | Merge with parent transaction if adjacent; else categorize as "Bills". | 1 |
| 3.8 | **International transaction fees** | Flag as "Fee" — add to tags. Categorize under "Bills" or "Other". | 2 |
| 3.9 | **Failed/declined transactions** | Detect via keywords ("failed", "declined", "reversed"). Exclude from metrics. | 1 |
| 3.10 | **Reversed/chargeback transactions** | Pair with original transaction if possible. Net amount should be zero. | 1 |
| 3.11 | **Opening balance doesn't match sum of transactions + closing balance** | Flag validation warning. Still process data but note discrepancy. | 1 |
| 3.12 | **Missing opening/closing balance** | Process transactions without balance validation. Skip Golden Rule check. | 1 |
| 3.13 | **Rounding discrepancies** (sum off by ₹0.01–₹0.05) | Accept if within tolerance (₹0.50). Common in bank statements. | 1 |
| 3.14 | **Same-day multiple transactions at same merchant** | Keep all as separate transactions. Only deduplicate if all fields match exactly. | 1 |
| 3.15 | **White-space-only description after cleaning** | Fallback to original description; mark as "uncleanable". | 1 |

---

## 4. AI Categorization

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 4.1 | **Ambiguous descriptions** (e.g., "Apple" — food or electronics?) | LLM should infer from amount/context. Rule fallback may misclassify. Accept confidence drop. | 2 |
| 4.2 | **Multi-word merchant matching multiple categories** ("BigBasket" = Food, also sells household items) | LLM more reliable; rule fallback picks first match. | 2 |
| 4.3 | **Groceries — Food vs Shopping?** | Default to "Food" for grocery stores. Allow manual override. | 2 |
| 4.4 | **ATM withdrawal** — spending or transfer? | Default to "Other" with note: "ATM withdrawal — actual spend unknown." | 2 |
| 4.5 | **Credit card payment** — should not count as spending | Categorize as transfer. Exclude from spend metrics. Detect via "credit card payment", "CC payment" keywords. | 2 |
| 4.6 | **Investment redemption (credit)** vs **Salary (credit)** | LLM distinguish via description and amount. Redemption will have merchant keywords. | 2 |
| 4.7 | **Loan disbursement vs Income** | Categorize as transfer/other, not income. Detect via "loan", "disbursement" keywords. | 2 |
| 4.8 | **Insurance premium payment** — Investment or Expense? | Default to "Bills" or "Other". Allow user to categorize manually. | 2 |
| 4.9 | **Wallet top-up** (Paytm, Amazon Pay) — spending or transfer? | Default to transfer. Exclude from spend unless user marks as spend. | 2 |
| 4.10 | **EMI transactions that include interest** | Keep as single transaction with full amount. Categorize as "EMI". | 2 |
| 4.11 | **Merchant with no keyword match at all** | Default to "Other". LLM may still classify based on semantic understanding. | 2 |
| 4.12 | **Descriptions in non-English languages** | LLM can handle multi-language. Rule fallback will fail — fall to "Other". | 2 |
| 4.13 | **Abbreviated merchant names** ("AMZN MKTPL" vs "Amazon Marketplace") | LLM handles abbreviations well. Rule fallback needs regex patterns for common abbreviations. | 2 |
| 4.14 | **Confidence exactly at thresholds** (0.89, 0.90, 0.91) | Use strict comparison. 0.90+ → use LLM result. <0.90 → re-check with rules. | 2 |
| 4.15 | **Empty description after cleaning** | Cannot categorize. Default to "Other". | 2 |
| 4.16 | **OpenAI API returns invalid JSON** | Retry up to 2 times. If still failing, fallback entirely to rules. | 2 |
| 4.17 | **OpenAI API returns unexpected categories** | Validate against allowed category list. Map unknown categories to "Other" with warning. | 2 |
| 4.18 | **Batch of 15 descriptions: 14 succeed, 1 fails** | Accept partial results. Apply fallback categorization to the failed item only. | 2 |

---

## 5. Recurring Detection

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 5.1 | **Only 1-2 occurrences of a recurring pattern** (insufficient data) | Do not flag as recurring. Note: "More data needed to confirm recurring pattern." | 2 |
| 5.2 | **Irregular intervals** (e.g., Netflix billed on different dates each month: 5th, 3rd, 7th) | Accept ±3 day tolerance. Flag if intervals are consistently 28-31 days apart. | 2 |
| 5.3 | **Amount changes slightly** (EMI with reducing balance: ₹5,432 → ₹5,321 → ₹5,210) | Use amount tolerance of ±5% when grouping by merchant. | 2 |
| 5.4 | **Amount changes significantly** (variable utility bills: ₹800, ₹1,200, ₹950) | Threshold at ±5% of average. If outside, don't group by amount — rely on merchant + interval matching. | 2 |
| 5.5 | **Merchant name varies slightly** ("Netflix.com", "Netflix", "NETFLIX") | Use case-insensitive matching. Strip TLD suffixes. Consider fuzzy string matching (Levenshtein distance ≤ 3). | 2 |
| 5.6 | **Subscription cancelled mid-period** | If cancellation detected by keyword, stop recurring flag for future dates. | 2 |
| 5.7 | **Annual subscription appearing only once in data** | Cannot detect as recurring with only 1 occurrence. Note: "Possible annual subscription — needs more data." | 2 |
| 5.8 | **Bi-weekly vs monthly patterns** | Check interval mode. 14±2 days = bi-weekly. 28-31 days = monthly. Distinguish in frequency field. | 2 |
| 5.9 | **False positive: monthly groceries at same store** | May be flagged as recurring. This is acceptable — user can unflag manually. | 2 |
| 5.10 | **Promotional discounts varying amounts** | Detect base price pattern before discount. Flag with note: "Amount varies due to discounts." | 2 |
| 5.11 | **Free trial transactions (₹0)** | Include in recurring check if merchant matches. Note: "Currently ₹0 — possible free trial." | 2 |
| 5.12 | **Refund of a recurring payment** | Exclude refund from recurring detection. Pair with original payment. | 2 |
| 5.13 | **Credit-side recurring** (salary, SIP redemptions) | Detect same as debit-side: consistent amount + interval + merchant. Flag as "Recurring Income". | 2 |
| 5.14 | **Split payments for same subscription** (50% on card A, 50% on card B) | Difficult to detect. Flag if amounts sum to known subscription price. | 2 |
| 5.15 | **Quarterly payments matching monthly patterns** (e.g., 4 payments per year spaced 90 days apart) | Group as quarterly (85-95 day intervals) instead of monthly. | 2 |

---

## 6. Financial Metrics

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 6.1 | **All transactions are debits** (no income — user only uploaded expense statements) | Show ₹0 income. Savings = negative of total spend. Display appropriate message: "No income transactions found in this statement." | 1 |
| 6.2 | **All transactions are credits** (no spending — e.g., salary account with no debits) | Show ₹0 spend. Display: "No spending transactions found in this statement." | 1 |
| 6.3 | **Only 1 transaction total** | Metrics still compute; trend chart has no meaningful comparison. Show single data point. | 1 |
| 6.4 | **Spending exceeds income** (negative savings) | Show negative savings in red. Provide insight: "Your spending exceeded income by ₹X." | 1, 3 |
| 6.5 | **Zero savings** (income exactly equals spend) | Show ₹0 savings. Rate = 0%. | 1 |
| 6.6 | **₹0 transactions** | Exclude from monetary metrics. Count in transaction count. | 1 |
| 6.7 | **Extremely large numbers** (crores/lakhs — e.g., property purchase) | Handle large floats without overflow. Format display as ₹1,00,00,000 (Indian numbering). | 1 |
| 6.8 | **Fractional amounts** (paise — e.g., ₹499.99) | Preserve precision through calculations. Display with 2 decimal places. | 1 |
| 6.9 | **Categories with 0 transactions** | Show as 0% in breakdown. Don't include in top categories list. | 1 |
| 6.10 | **All transactions in same category** | Single category dominates at 100%. All other categories at 0%. | 1 |
| 6.11 | **Multiple transactions tie for "biggest"** amount | Show all tied transactions. Pick most recent if only one needs to be highlighted. | 1 |
| 6.12 | **Empty transaction list** (no data) | Return zeroed metrics. Display "No data available" in dashboard. | 1 |
| 6.13 | **Transfer transactions skew metrics** | Option to exclude transfers (NEFT/IMPS between own accounts) from income/spend. | 1 |
| 6.14 | **Category percentage rounding** (categories summing to 99.9% or 100.1%) | Round to 1 decimal. Display note: "Percentages may not sum to 100% due to rounding." | 1 |

---

## 7. Insight Generation

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 7.1 | **AI fails to generate insights** (API error, timeout, malformed response) | Fallback to rule-based template insights using available metrics. | 3 |
| 7.2 | **AI generates fewer than 3 insights** | Accept what's generated. Add fallback insights to reach minimum of 3. | 3 |
| 7.3 | **AI generates incoherent/contradictory insights** | Validate — if fields are missing or nonsensical, fallback to rules for that insight. | 3 |
| 7.4 | **Insight reveals sensitive pattern** (e.g., "You visited this ATM 12 times at 1 AM") | Still display. Consider adding tone/filtering for sensitive insights in future. | 3 |
| 7.5 | **LLM hallucination** (amounts that don't exist in data) | Validate referenced amounts against actual data. Remove or correct any hallucinated values. | 3 |
| 7.6 | **Very long insight text** (>500 chars) | Truncate in card view with "Read more" expand option. | 3 |
| 7.7 | **Empty/blank insight from LLM** | Catch and replace with rule-based fallback. | 3 |
| 7.8 | **Non-constructive or purely negative insights** ("You wasted money on X") | Rephrase to constructive tone: "Consider reviewing X spending — it was ₹Y this month." | 3 |
| 7.9 | **Insights for very short time period** (1 day's data) | Still generate but note: "Based on limited data (1 day)." | 3 |
| 7.10 | **Insights comparing across months when only 1 month present** | Skip month-over-month comparisons. Generate only single-month insights. | 3 |
| 7.11 | **Duplicate insights** (same insight generated twice) | Deduplicate by title/description before storing. | 3 |
| 7.12 | **Insight severity mismatches** (positive insight marked as "warning") | Validate severity based on type + amount. Override if clearly wrong. | 3 |
| 7.13 | **User generates insights multiple times** | Cache latest. Overwrite previous insights. Show regeneration timestamp. | 3 |

---

## 8. Report Generation

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 8.1 | **PDF generation fails mid-way** | Return error with message: "Report generation failed. Please try downloading as HTML instead." | 3 |
| 8.2 | **Very large transaction list** (>1000 transactions in report) | Paginate in report or summarize with top 50. Include note: "Full transaction log contains X entries." | 3 |
| 8.3 | **Unicode characters not rendering in PDF** | Use font with wide Unicode support (e.g., Noto Sans). Fallback to HTML report if PDF fails. | 3 |
| 8.4 | **Chart rendering in report fails** | Skip chart, show data as table. Report still usable. | 3 |
| 8.5 | **HTML-to-PDF conversion breaks layout** | Ensure print CSS is robust. Offer both PDF and HTML download options. | 3 |
| 8.6 | **Report requested for non-existent job_id** | Return 404 with message: "Analysis not found for this ID." | 3 |
| 8.7 | **Report requested while analysis still processing** | Return 409 Conflict: "Analysis still in progress. Please wait." | 3 |
| 8.8 | **Empty data sections in report** | Show "No data available" for empty sections rather than omitting them. | 3 |
| 8.9 | **Report download with unsupported format** | Validate format param (`pdf` or `html`). Default to HTML if invalid. | 3 |

---

## 9. Frontend / UI

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 9.1 | **User drags and drops multiple files** | Process only the first file. Show: "Multiple files detected. Only the first file will be processed." | 4 |
| 9.2 | **User uploads while another upload is processing** | Disable upload button during processing. Show existing job status. | 4 |
| 9.3 | **Network failure during upload** (partial upload) | Detect failure, show error with retry button. Polling should resume from server side if possible. | 4 |
| 9.4 | **Browser refresh during processing** | On reload, check if job_id exists in URL/localStorage. Resume polling if found. | 4 |
| 9.5 | **User navigates away and comes back** — job_id lost | Show list of recent analyses from backend (future feature). For now, prompt re-upload. | 4 |
| 9.6 | **Very long transaction list (>10,000)** causing browser freeze | Virtualized table (React Window). Lazy load chunks of 50. Paginate API response. | 4 |
| 9.7 | **Empty state — no data uploaded yet** | Show welcome screen with upload prompt. No error, no empty tables. | 4 |
| 9.8 | **All filters return no results** | Show "No transactions match your filters" with clear filters button. | 4 |
| 9.9 | **Dark mode partially implemented** | Ensure all components are covered. Test dark mode on all pages. | 5 |
| 9.10 | **Mobile screen width breaking dashboard** | Responsive grid: 1 column on mobile, 2 on tablet, 3+ on desktop. Test breakpoints at 640px, 768px, 1024px. | 5 |
| 9.11 | **Browser back/forward navigation** | Use React Router properly. State should persist or re-fetch via API. | 4 |
| 9.12 | **Very long merchant/description names breaking table layout** | Truncate with ellipsis. Tooltip shows full text on hover. Max column width. | 4 |
| 9.13 | **Concurrent inline edit conflicts** (user changes category, API returns old data) | Optimistic update: apply immediately, revert on error. Show conflict notification. | 4 |
| 9.14 | **Polling timeout** — job never completes (>5 minutes) | Show timeout message: "This analysis is taking longer than expected. You can check back later using this link." Provide job_id reference. | 4 |
| 9.15 | **User clicks "Generate Insights" multiple times** | Debounce: disable button after click, show loading spinner, re-enable on completion. | 5 |
| 9.16 | **Screen reader / accessibility** — charts not readable | Add `aria-labels`, alt text, keyboard navigation for all interactive elements. | 5 |
| 9.17 | **Slow network / high latency** on initial load | Show skeleton loaders immediately. Stream data where possible. | 4, 5 |
| 9.18 | **Chart tooltip/slice interaction on touch devices** | Ensure touch works for mobile. Use tap instead of hover. | 5 |

---

## 10. API & Backend

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 10.1 | **Concurrent upload requests** | Each gets unique job_id. Process asynchronously without blocking. | 1 |
| 10.2 | **Job_id not found** | Return 404 with message: "Analysis job not found." | 1 |
| 10.3 | **Server restart during processing** — in-memory jobs lost | Return 404. Jobs that completed and stored to SQLite survive. Add persistence for active jobs in future. | 1 |
| 10.4 | **OpenAI API key not configured but cloud mode selected** | Return error: "AI API key not configured. Switch to offline mode in settings." | 2 |
| 10.5 | **OpenAI API rate limit exceeded** | Exponential backoff retry (1s, 2s, 4s). If still failing, fallback to rule-based categorization. | 2 |
| 10.6 | **OpenAI API returns unexpected response format** | Validate JSON structure with Pydantic. Retry once. If still malformed, fallback to rules. | 2 |
| 10.7 | **OpenAI API timeout** (>30s) | Set client timeout. On timeout, fallback to rules for that batch. | 2 |
| 10.8 | **CORS errors from incorrect frontend origin** | Configure CORS to allow only frontend origin (`localhost:5173` in dev). | 1 |
| 10.9 | **Very large response payload** (>10MB for 10,000 transactions) | Paginate API response. Default page size = 50, max = 200. | 1 |
| 10.10 | **Invalid query parameters** (negative page number, non-integer limit) | Validate with Pydantic. Return 422 with descriptive error. | 1 |
| 10.11 | **SQLite concurrent write contention** (rare for single-user) | Use WAL mode for SQLite. Queue writes if necessary. | 1 |
| 10.12 | **File system full during upload** | Catch file write error. Return: "Server storage is full. Please free up space and try again." | 1 |
| 10.13 | **Alembic migration fails on first run** | Log migration error. Attempt auto-create tables if migration fails. | 1 |
| 10.14 | **Port already in use** (8000 or 5173) | Show clear error message with instructions to change port. | 1 |
| 10.15 | **Malformed job_id in URL** (not a valid UUID) | Return 400: "Invalid job ID format." | 1 |

---

## 11. Async Job Processing

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 11.1 | **Job processing pipeline crashes mid-step** | Log error. Set job_status = "failed". Return error details in API response. | 1 |
| 11.2 | **Job processing hangs indefinitely** (e.g., AI call stuck) | Set overall timeout (5 minutes). Kill job on timeout, set status to "failed". | 1 |
| 11.3 | **Frontend polls a completed job** | Return cached result immediately. No re-processing. | 1 |
| 11.4 | **Frontend polls a failed job** | Return `{ "status": "failed", "error": "..." }`. Display error to user. | 1 |
| 11.5 | **User uploads new file while previous job is still processing** | Process independently. Both jobs run in parallel. | 1 |
| 11.6 | **In-memory job store grows too large** (many abandoned jobs) | Implement TTL (time-to-live) — purge jobs older than 1 hour. | 1 |
| 11.7 | **SQLite write during job processing fails** | Retry 3 times. If still failing, mark job as "failed". | 1 |
| 11.8 | **Step N succeeds but step N+1 fails** | Keep successfully processed data. Report partial failure: "Categorization completed, but insight generation failed." | 1, 2, 3 |

---

## 12. Privacy & Security

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 12.1 | **User's bank statement contains PII** (account number, IFSC, address) | Auto-detect and redact PII patterns (account numbers, phone numbers, email) before storing or sending to AI. | 1, 6 |
| 12.2 | **User enables cloud AI without realizing data leaves machine** | Show explicit confirmation dialog on first use: "This will send transaction descriptions to OpenAI. No account numbers or balances will be shared." | 6 |
| 12.3 | **User changes AI toggle from cloud to local mid-session** | No in-flight jobs affected. New jobs use new setting. | 6 |
| 12.4 | **OpenAI API key accidentally exposed in frontend** | Env var only accessible to backend. Never send API key to frontend. | 6 |
| 12.5 | **User tries to access another user's job_id** | No auth system — all local. Security through locality. | 6 |
| 12.6 | **SQLite file accessed by unauthorized user on shared machine** | Document that data is stored in a local file and advise on OS-level file permissions. | 6 |
| 12.7 | **User wants to delete all data** | Provide a "Clear all data" button that drops SQLite tables. | 6 |
| 12.8 | **Uploaded file not deleted after processing** | Auto-delete after parsing. Have a cleanup scheduler if auto-delete fails. | 6 |
| 12.9 | **CORS misconfiguration exposes API to all origins** | Restrict to specific origin in production. Document in setup. | 6 |
| 12.10 | **Logging accidentally captures raw statement data** | Configure logger to redact/truncate transaction descriptions and amounts. | 6 |

---

## 13. Deployment & Environment

| # | Edge Case | Expected Behaviour | Phase |
|---|-----------|-------------------|-------|
| 13.1 | **Docker not installed** | Document alternative local setup in README with step-by-step instructions. | 6 |
| 13.2 | **Node.js / Python not installed** | Version check in launcher script. Display: "Please install Python 3.10+ and Node.js 18+." | 6 |
| 13.3 | **Wrong Python version** (e.g., Python 2.7 or 3.8) | Check `python --version`. Minimum 3.10. Show upgrade message if below. | 6 |
| 13.4 | **Missing system dependencies** (weasyprint, libxml2, etc. on Linux) | Include in README. Docker handles this automatically. For local setup, provide install commands per OS. | 6 |
| 13.5 | **Port conflict** (8000 or 5173 already in use) | Auto-detect and increment port. Display final URL to user. | 6 |
| 13.6 | **File permission issues on Linux/macOS** | Document `chmod +x run.sh`. Use virtualenv to avoid system permission issues. | 6 |
| 13.7 | **Windows vs Unix path separator** (`\` vs `/`) | Use `pathlib` (Python) and `path` module (Node) for cross-platform path handling. | 6 |
| 13.8 | **Case-insensitive filesystem** (Windows/macOS) vs **case-sensitive** (Linux) | Be consistent with import paths in both Python and TypeScript. | 6 |
| 13.9 | **Antivirus blocking file processing** | Can't solve programmatically. Document: "Antivirus may temporarily quarantine uploaded files." | 6 |
| 13.10 | **Proxy/firewall blocking AI API calls** | Detect network error to OpenAI. Message: "Unable to reach AI API. Check your network/proxy settings or switch to offline mode." | 6 |
| 13.11 | **Running on headless server** (no browser) | Dashboard requires a browser. Document that the app is a local web UI, not a CLI tool. | 6 |
| 13.12 | **macOS Gatekeeper blocking app** | Sign scripts or document how to bypass. | 6 |
| 13.13 | **npm install fails** due to network or dependency conflicts | Provide `package-lock.json` and `requirements.txt` with pinned versions. Clear error message for network issues. | 6 |
| 13.14 | **Docker image platform mismatch** (ARM vs AMD64) | Provide multi-arch Docker builds for both Intel and Apple Silicon. | 6 |

---

## Appendix: Edge Case Severity Classification

| Severity | Meaning | Example |
|----------|---------|---------|
| 🔴 **Critical** | Causes data loss, incorrect metrics, or application crash | Invalid file causes server crash |
| 🟠 **High** | Significantly reduces accuracy or usability | AI categorization returns garbage |
| 🟡 **Medium** | Affects specific features, has workaround | PDF chart rendering fails, but HTML report works |
| 🟢 **Low** | Minor cosmetic or edge cases | Very long name breaks table layout |

---

## Appendix: Recommended Unit Tests

For each edge case above, at minimum the following should have automated tests:

| Area | Minimum Test Coverage |
|------|----------------------|
| **Parsing** | Empty file, malformed CSV, different date formats, different amount formats, missing fields |
| **Cleaning** | Deduplication, merchant normalization, balance validation, special characters |
| **Categorization** | All 10 categories, empty description, ambiguous description, offline fallback |
| **Recurring** | 3+ monthly pattern, 2 occurrences only, variable amounts, irregular intervals |
| **Metrics** | Zero savings, all debits, all credits, empty list, rounding |
| **Insights** | AI success, AI failure, hallucinated amounts, duplicate insights |
| **API** | Invalid job_id, concurrent uploads, large payloads, missing parameters |
| **Frontend** | Empty state, error state, loading state, large dataset, mobile viewport |

---

*Last updated: June 2026*
*Version: 1.0*
