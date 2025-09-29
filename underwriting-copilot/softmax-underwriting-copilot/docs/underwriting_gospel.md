# Underwriting Copilot Operating Gospel

These directives describe the underwriting simulation workflow and must be followed exactly.

## Data Intake
- Raw job payload may include any subset of: credit bureau data, social insurance (ND), collateral, loan request, bank statements.
- Every component is optional. Missing sources must not be called out to the LLM; simply omit them.

## Credit & Social Insurance
- Credit bureau JSON is passed to the LLM untouched.
- Social insurance JSON is passed untouched when present.

## Collateral Handling
- When collateral is offered, inspect `type`:
  - **Vehicle**: Call the ML price API first using the payload schema:
    ```json
    {
      "brand": "Toyota",
      "model": "Camry",
      "year_made": 2018,
      "imported_year": 2019,
      "odometer": 95000,
      "hurd": "Зөв",
      "Хурдны хайрцаг": "Автомат",
      "Хөдөлгүүр": "2.5",
      "Өнгө": "Хар"
    }
    ```
    - If the ML call succeeds, forward the raw response to downstream consumers.
    - If the ML call fails, fall back to a web search using the pattern `"<brand> <model> <year> зарна үнэ"`.
    - **API call requirements**:
      - Endpoint base URL: `https://softmax.mn`
      - Resource path: `/api/predict-price/`
      - Headers must include:
        ```json
        {
          "Content-Type": "application/json",
          "X-API-KEY": "<value of X_API_KEY from .env>"
        }
        ```
      - Always log and forward the raw JSON body (and any error message) to the LLM payload.
  - **Real Estate & Other**: Skip ML; perform a web search immediately and return raw results unmodified.
- Web search results must contain raw textual content (HTML or consolidated text) exactly as returned.

## Bank Statements
- When a bank statement URL is provided:
  - Download the PDF.
  - Parse it and compute **only**:
    - Average monthly income (MNT).
    - Statement span (e.g., `2025-05 to 2025-11`).
  - Supply only these derived values to the LLM.

## LLM Interaction
- There is **no sandbox fallback**. If the LLM call fails, stop and report the error; do not synthesize memos locally.
- The LLM is solely responsible for Accept/Review/Decline decisions and interest-rate suggestions within the memo.

## Simulation Output Contract
- For each simulated applicant, output exactly three structures:
  1. `raw_input` – the incoming payload as provided upstream (bank/partner JSON).
  2. `llm_input` – the assembled request to the LLM (includes derived bank income, raw ML/web search artifacts, etc.).
  3. `llm_output` – the LLM response. If an error occurs, record the failure without modification attempts.
- Do not include extra commentary, reports, or synthesized summaries.

## Error Policy
- When any step fails (e.g., ML service, LLM invocation), surface the failure verbatim and recommend remediation separately. Do **not** auto-correct or mask issues.

Keep this document in sync with workflow changes. EOF
