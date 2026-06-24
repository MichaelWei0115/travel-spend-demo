> **Deprecated Notice**:
> This document may contain historical references to the old 5-state / dual-status reimbursement model.
> The current authoritative model is the 4-state model documented in CURRENT_STATE.md:
>
> - pending_receipt
> - pending_submit
> - submitted
> - error
>
> Do not restore or extend the deprecated fields:
>
> - ai_check_result
> - sync_status
> - need_supplement
> - sync_failed

# DingTalk Auto Reimbursement Interactive H5 v2

## Final Delivery Document

Version: DingTalk_Auto_Reimbursement_Interactive_H5_v2
Date: 2026-06-18

---

## 1. Retained Original Conversational Capabilities

The original AI-powered chat assistant remains fully functional:

- **Event-driven AI responses**: payment.auth.success, receipt.uploaded, etc.
- **Template fallback mode**: Works without API keys using pre-built responses
- **Prompt engineering lab** (Tab 2): Prompt version comparison (v1/v2), KV cache friendliness estimation, working memory visualization, injection detection, JSON validation
- **Evaluation and observability** (Tab 3): Run eval cases, metrics dashboard, alerts, low-confidence monitoring
- **Security guardrails**: Indirect prompt injection detection, locked field override prevention, confidence calibration (never > 0.95)
- **Tool calling framework**: Registered tools with error simulation capability
- **DingTalk-style chat UI**: Mobile-first responsive iframe with card messages, confidence bars, status badges

---

## 2. New H5 Reimbursement Record Capabilities

- Full-page H5 reimbursement record management (list, detail, supplement)
- Five-status filter tabs with real-time count updates
- Record detail page with AI verification explanation
- Supplement material upload flow (invoice + receipt voucher + note + expense type)
- One-click sync and retry-sync with status transitions
- H5-to-chat linkage: operations in H5 pages produce result messages in chat
- Duplicate prevention: same action on same record only appends one chat message

User Journey: Chat -> Quick action/More menu -> Reimbursement list -> Filter/Detail/Supplement -> Auto-return to chat with result message

---

## 3. New Page List

| Page ID | Name | Entry Point | Description |
|---------|------|-------------|-------------|
| chat | Main chat | Default | DingTalk-style AI assistant chat |
| reimbursement_list | Reimbursement records | Quick action / More menu | Filterable list of expense records |
| reimbursement_detail | Verification detail | List card button | Full record detail with AI check explanation |
| supplement_material | Supplement materials | List/Detail button | Upload invoice/receipt, select type, submit |

Router: app.py checks st.session_state.current_page, renders H5 page via h5_pages.py if not "chat".

---

## 4. New Data Model

### Record Schema (reimbursement_data.py)

Fields per record:
- id: Unique record ID (e.g. "record_001")
- merchant_name: Merchant display name
- amount: Transaction amount (numeric)
- currency: Currency code (CNY/HKD/USD/JPY)
- transaction_time: Full datetime string (e.g. "2026-06-11 18:30")
- expense_type: Category label
- ai_check_result: AI verification result (enum, see Section 5)
- ai_check_message: Human-readable AI explanation
- sync_status: Sync state (enum, see Section 5)
- sync_time: Last sync timestamp or None
- sync_order_no: Generated order number or empty string
- sync_error_message: Error details if sync failed
- attachments: List of attachment filenames

### Supplement Form Schema (session_state.supplement_form)

- invoice_uploaded: Boolean - whether invoice was uploaded
- invoice_name: Uploaded invoice filename
- receipt_uploaded: Boolean - whether receipt voucher was uploaded
- receipt_name: Uploaded receipt filename
- note: User-entered supplementary note
- expense_type: Selected expense type

### Mock Data: 6 records covering all key states
- record_001: passed + synced (happy path complete)
- record_002: passed + not_synced (ready to sync)
- record_003: need_supplement + not_synced (needs invoice)
- record_004: passed + sync_failed (retry scenario)
- record_005: failed + not_synced (over limit)
- record_006: need_supplement + not_synced (needs ticket)

---

## 5. New Status Enums

### AI Check Result (ai_check_result)
| Value | Label | Color | Description |
|-------|-------|-------|-------------|
| pending | Pending | #999 | Not yet checked |
| passed | Passed | #2E7D32 | Meets policy rules |
| need_supplement | Need Supplement | #E65100 | Missing documents |
| failed | Failed | #C62828 | Violates policy |

### Sync Status (sync_status)
| Value | Label | Color | Description |
|-------|-------|-------|-------------|
| not_synced | Not Synced | #999 | Not yet submitted |
| syncing | Syncing | #1565C0 | In progress |
| synced | Synced | #2E7D32 | Successfully synced |
| sync_failed | Sync Failed | #C62828 | Sync error |

---

## 6. Full Button Interaction List (51 + extras)

### iframe Chat Buttons (9 fixed + 6 card-dynamic = 15)
1. Header back (top_back) -> Toast
2. Header more (open_more_menu) -> Modal
3. Quick: Report Records (open_reimbursement_records) -> Navigate
4. Quick: Travel Rules (open_travel_rule) -> Modal
5. Input: + (open_attachment_menu) -> Modal
6. Input: Send (send_message) -> Toast
7. Input: Emoji (emoji_click) -> Toast
8. Input: Voice (voice_click) -> Toast
9. FAB: Demo Flow (toggle_demo_flow) -> Toast
10. Card: Upload Receipt (upload_receipt) -> Action
11. Card: View/Edit Detail (open_edit_detail) -> Modal
12. Card: Confirm and Sync (confirm_and_sync) -> Action
13. Card: Update Detail (save_detail_update) -> Message
14. Card: Confirm Diff (confirm_diff) -> Message
15. Card: Re-upload (reupload_receipt) -> Message

### Streamlit Flow Panel (18 buttons: #16-33)
16-20: Main flow steps 1-5
21-22: Exception flows (mismatch, payment failed)
23: One-click full flow (primary button)
24: Reset Demo
25-31: Card button responses (7 buttons)
32-33: Modal close buttons (2)

### H5 Page Buttons (12 buttons: #34-45)
34: List back button
35-39: Filter tabs (All/Need Supplement/Passed/Synced/Sync Failed)
40: Go Supplement
41: View Detail
42: Confirm and Sync (list card)
43: Retry Sync (detail page)
44: Upload Invoice
45: Upload Receipt Voucher

### Tab 2/3 Buttons (6 buttons: #46-51)
46-49: Lab tools (injection, override, JSON validate, malformed)
50-51: Run evals, reset metrics

### Extra Modal Buttons (not in 51 count)
- More menu: 5 buttons (Report Records, Travel Rules, Reset, About, Close)
- Attachment menu: 4 buttons (Invoice, Receipt, Photo, Close)
- About Demo: 1 close button
- Detail page: 5 state-dependent bottom buttons
- Supplement page: Submit + expense type selectbox

Full action registry: action_map.py (27 registered actions)
Full handler: demo_actions.py handle_demo_action() (29 handled action IDs)

---

## 7. H5 Full Flow Description

### Happy Path (Supplement -> Sync)
1. User clicks "Report Records" from chat quick actions or More menu
2. List page shows 6 mock records with 5 filter tabs
3. User clicks filter tabs - counts update, list filters
4. User clicks "Go Supplement" on a need_supplement record
5. Supplement page shows: record summary, AI check result, upload areas, note, type selector
6. User uploads invoice (mock) -> uploaded badge + success toast
7. User uploads receipt voucher (mock) -> uploaded badge + toast
8. User enters note and selects expense type
9. User clicks Submit -> loading -> record updated (passed + synced) -> navigate to chat
10. Chat page shows AI result message
11. If user returns to list, counts are refreshed

### Retry Path (Sync Failed -> Synced)
1. User views sync_failed record detail
2. User clicks "Retry Sync" -> record synced -> navigate to chat
3. Chat shows sync success message

### Confirm Path (Passed -> Synced)
1. User clicks "Confirm and Sync" on passed+not_synced record
2. Record synced with order number generated -> navigate to chat

---

## 8. Mock Logic Description

| Component | Mock Behavior | Location |
|-----------|--------------|----------|
| AI verification | Instant result based on pre-set ai_check_result | reimbursement_data.py |
| File upload | Sets boolean flag + filename, no file storage | demo_actions.py |
| Sync to expense system | Instant status flip to "synced" + timestamp | demo_actions.py |
| Submit supplement | Instant ai_check->passed, sync->synced | demo_actions.py |
| Order number | Format: BX{datetime}{record_id_suffix} | demo_actions.py |
| Receipt OCR | Pre-set fields in step cards | demo_state.py |
| AI chat responses | Template-based, no real LLM call | services/ai_client.py |
| Transaction matching | Pre-set confidence values | demo_state.py |

Mock Data Reset: reset_demo() clears messages/steps/state. Records persist until app restart.

---

## 9. Real Interface Extension Points

| Feature | Replace With | File | Function |
|---------|-------------|------|----------|
| AI verification | Call AI model with policy + receipt | demo_actions.py | submit_supplement |
| File upload | S3/OSS upload + URL storage | h5_pages.py | Replace st.button with st.file_uploader |
| Sync to expense | REST API to enterprise system | demo_actions.py | confirm_single_sync, retry_sync |
| Receipt OCR | OCR service (Azure/Tencent) | services/receipt_parser.py | parse_receipt() |
| Record persistence | Database (PostgreSQL/DynamoDB) | reimbursement_data.py | Replace in-memory list |
| Transaction data | Bank/card API or enterprise feed | services/event_handler.py | load_data() |
| Chat AI responses | OpenAI API with prompts/v2 | services/ai_client.py | call_ai() |
| Push notifications | Webhook/event bus listener | demo_state.py | run_step_push_pending_receipt |

### Integration Pattern
1. Keep handle_demo_action() as the single entry point
2. Replace mock logic inside each handler with async API calls
3. Add error handling: show_error_toast on failure
4. Add real file upload: replace st.button with st.file_uploader in h5_pages.py
5. Add database layer: replace session_state.reimbursement_records with DB queries

---

## 10. Known Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Session state lost on refresh | Medium | Add persistence layer for production |
| No real file validation | Low | Add file type/size checks |
| No authentication | High | Add DingTalk OAuth/SSO |
| Concurrent state mutation | Low | Single-user; add locking for multi-user |
| iframe action delay | Low | ~100ms latency; acceptable for demo |
| No error boundaries for AI | Medium | Template fallback covers demo; add retry for prod |
| Mobile keyboard overlap | Low | Input bar is mock; real input needs keyboard avoidance |
| No i18n support | Low | Extract strings to locale files |

---

## File Structure

    app.py                    Main Streamlit app (687 lines) - tabs, routing, modals
    h5_pages.py               H5 page renderers (478 lines) - list, detail, supplement
    ui_components.py          Chat iframe HTML builder (667 lines) - CSS, cards
    demo_actions.py           Unified action dispatcher (396 lines) - all handlers
    demo_state.py             Chat state and flow steps (270 lines)
    reimbursement_data.py     Data model and mock records (220 lines)
    feedback.py               Unified feedback components (214 lines)
    action_map.py             Action registry spec (379 lines)
    services/                 AI client, event handler, evaluator, guardrails, etc.
    data/                     Mock JSON data files
    prompts/                  Prompt templates (v1/v2)
    assets/                   Images (receipts, avatars, icons)

---

## Quick Start

    pip install -r requirements.txt
    streamlit run app.py
    # Access at http://localhost:8501

---

## Demo Guide for Presenters

1. Open the app - DingTalk-style chat on Tab 1
2. Click "One-click full flow" in right panel for main 5-step demo
3. Click "Report Records" in chat quick actions to enter H5 pages
4. Try filter tabs, view details, go through supplement flow
5. After submitting supplement or retrying sync, chat shows result messages
6. Use Tab 2 (AI Lab) to demonstrate prompt engineering and security
7. Use Tab 3 (Eval) to run evaluation cases and show observability

---

## For Developers Continuing This Project

1. Start with demo_actions.py handle_demo_action() - single entry point
2. Data model in reimbursement_data.py - extend record schema as needed
3. New H5 page: add renderer in h5_pages.py, add page ID to router in app.py
4. New button: add handler in demo_actions.py, register in action_map.py
5. Replace mock with real API: see Section 9 for exact locations
6. CSS: ui_components.py (iframe) and feedback.py (Streamlit) - both mobile-first

---

## Version History

- v1.0: Original AI chat demo with event-driven responses
- v2.0 (current): H5 reimbursement records, detail, supplement, unified actions, mobile UX
