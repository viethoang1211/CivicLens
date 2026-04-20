# English Demo Script

> Two scenarios: **Quick Scan** (Birth Registration + Citizen ID) and **Dossier Creation** (Complaint / Litigation).

---

## Accounts at a Glance

| Role | Login | Department | Password |
|------|-------|------------|----------|
| Reception Officer | NV001 | Reception | `password123` |
| Admin Officer | NV002 | Administration | `password123` |
| Leadership | NV007 | Leadership | `password123` |

---

## Scenario 1 — Quick Scan: Birth Registration + Citizen ID

> **Story**: A citizen walks in and hands over two documents. The officer scans them; the AI reads and classifies each one automatically.

**Documents to prepare:**
- Printed copy of `02_to_khai_khai_sinh.pdf` (Birth Registration Form) — print on A4
- Physical copy (or A4 print) of a Citizen ID card — use Giàng Thị Pà's CCCD

**Estimated time: ~5 minutes**

---

### Step 1 — Log in as Reception Officer

> *(Open Staff App on the device)*

"I'm logging in as NV001 — the Reception officer who handles all incoming documents."

- Staff ID: `NV001` · Password: `password123`
- You should see: *"Xin chào, Nguyễn Văn An — Tiếp nhận"*

---

### Step 2 — Quick Scan: Citizen ID Card

> *(Tap **"Quét nhanh"** / Quick Scan on the home screen)*

"Instead of filling out a form manually, the officer just taps Quick Scan and points the camera at the document."

1. Tap **Quick Scan**
2. Select security level: **Public** (Công khai)
3. Tap **"Tạo & Bắt đầu quét"** — camera opens
4. Point the camera at the **Citizen ID card** → capture the image
5. Tap **"Hoàn tất"**

> *(The AI processing screen appears)*

"Now watch the AI work. First it runs OCR to extract all the text from the image — this uses Qwen-VL-OCR, a vision-language model optimized for Vietnamese documents."

- Progress bar: *"Đang trích xuất văn bản (OCR)..."*
- Then: *"Đang phân loại tài liệu..."*
- After 10–30 seconds, the result appears.

> *(Show the AI result screen)*

"The model identified this as a **Citizen ID card** with ~95% confidence, and extracted the key fields: ID number **011167000556**, name **Giàng Thị Pà**, date of birth **01/01/1967**. No manual data entry required."

- Tap **"Xác nhận phân loại"** to confirm the classification.

---

### Step 3 — Quick Scan: Birth Registration Form

> *(Return to home screen, tap **Quick Scan** again)*

"Same flow for the second document — the system handles any document type the same way."

1. Tap **Quick Scan**
2. Security level: **Public**
3. Capture the **Birth Registration Form** (printed A4)
4. Tap **"Hoàn tất"**

> *(Wait for AI result)*

"This time the model recognizes a **Birth Registration Form** — ~90% confidence. It extracted the child's name **Sùng Thị Mỷ**, mother's name **Giàng Thị Pà**, and birth date **10/03/2026**."

- Tap **"Xác nhận phân loại"**

---

### Step 4 — What Just Happened

> *(Show the list of created dossiers, e.g., `HS-20260417-00001` and `HS-20260417-00002`)*

"Each Quick Scan created an independent dossier. Both are now in the Reception queue. If the citizen's ID number matches a registered citizen account, the dossier is automatically linked to their profile — so they can track it in the Citizen App without providing a separate reference number."

**Key points to highlight:**
- AI reads handwritten and printed Vietnamese text
- Classification is always overridable by the officer — AI is advisory, not final
- Full audit trail: who scanned, when, what the AI said, what the officer confirmed

---

## Scenario 2 — Full Dossier: Complaint / Litigation Case

> **Story**: A citizen files a formal complaint. The case is routed: Reception → Administration → Leadership, with each department reviewing and approving.

**Route: Reception → Administration (NV002) → Leadership (NV007)**

**Estimated time: ~8 minutes**

---

### Step 1 — Log in as Reception Officer

> *(Already logged in as NV001, or log in now)*

"For a formal complaint case, the officer creates a structured dossier rather than a quick scan — this captures the full case context and triggers the correct routing workflow."

---

### Step 2 — Create the Dossier

> *(Tap **"Tạo Hồ sơ mới"** / New Dossier)*

1. Tap **"Tạo Hồ sơ mới"**
2. Select procedure: **"Đơn khiếu nại / tố cáo"** (Complaint / Litigation)

> *(The system shows the required document slots)*

"The system knows exactly which documents are required for a complaint filing. Each slot must be filled before submission."

Required documents:
- Complaint letter (Đơn khiếu nại)
- Citizen ID of the complainant

3. For each document slot — tap the slot → camera opens → scan the document
4. The AI runs OCR and classification on each scanned page automatically

> *(After scanning)*

"You can see the AI result for each document — document type, confidence score, and extracted text. The officer reviews these and can override any AI judgment if needed."

---

### Step 3 — Submit the Dossier

1. Tap **"Nộp hồ sơ"** / Submit

> *(Dossier status changes to "Đã nộp" / Submitted)*

"The moment the officer submits, the system automatically routes the case to Administration — no manual assignment needed. The routing rules are defined per procedure type."

Note the **dossier reference number** (e.g., `HS-20260417-00003`).

---

### Step 4 — Administration Reviews (NV002)

> *(Switch to a second device, or log out and log in as NV002)*

- Staff ID: `NV002` · Password: `password123`
- Department: *Administration (Hành chính)*

1. Tap **"Hàng đợi"** (Queue)

> *(The complaint dossier appears in the queue)*

"Each department only sees the cases assigned to them. NV002 cannot see cases belonging to Finance or Judicial — separation of concern is enforced at the data level."

2. Tap the dossier → review scanned documents + AI-extracted text
3. Tap **"Phê duyệt"** → add a note: *"Complaint is within jurisdiction. Forwarding to Leadership."*

> *(Dossier automatically routes to Leadership)*

---

### Step 5 — Leadership Approves (NV007)

> *(Switch to device / account NV007)*

- Staff ID: `NV007` · Password: `password123`
- Role: *Manager — Leadership (Lãnh đạo)*

1. Tap **"Hàng đợi"**
2. Open the dossier → review the full case history including Administration's notes
3. Tap **"Phê duyệt"** → add final decision note

> *(Dossier status becomes "Hoàn thành" / Completed)*

"The case is now closed. Every action — who scanned, who approved, what was said — is permanently recorded in the audit log."

---

### Step 6 — Citizen Checks Status (Citizen App)

> *(Open Citizen App on a separate device)*

"Let's see what the citizen sees on their end — without calling the office or coming in person."

1. Log in via VNeID mock → select **"Trần Văn Hùng"** (CCCD: 012345678903)
2. Tap **"Hồ sơ của tôi"** (My Dossiers)
3. Find the complaint dossier
4. Tap it → see the full timeline:
   - ✅ Reception — Completed
   - ✅ Administration — Completed
   - ✅ Leadership — Completed — *"Hoàn thành"*

> *(Show the timeline screen)*

"The citizen has complete visibility into where their case is at every moment. No phone calls, no waiting at the counter — status updates in real time."

---

## Closing Points

| | Quick Scan | Full Dossier |
|---|---|---|
| **Use case** | Walk-in, unstructured documents | Formal procedure with defined steps |
| **AI role** | OCR + auto-classification | OCR + classification per slot |
| **Routing** | Single queue (Reception) | Multi-department workflow |
| **Citizen visibility** | Linked if ID matches | Full timeline tracking |
| **Audit trail** | Every scan logged | Every approval step logged |

"The platform handles both ends of the spectrum — a quick scan for a simple document check, and a full structured workflow for complex multi-department cases. The AI accelerates every step without removing human judgment at any point."

---

## Reference

| Item | Value |
|------|-------|
| API / Backend | http://43.98.196.158 |
| Swagger Docs | http://43.98.196.158/docs |
| VNeID Mock | http://43.98.196.158/vneid/authorize |
| AI model (OCR) | `qwen-vl-ocr` (Alibaba Cloud DashScope) |
| AI model (Classification) | `qwen2.5-vl-7b-instruct` |

### Troubleshooting

| Problem | Fix |
|---------|-----|
| VNeID code copy fails | Tap the code field → Select All → Copy from Android menu |
| Queue is empty | Dossier not yet submitted, or routed to a different department |
| "Cannot determine department" | Log out and log back in |
| AI result takes > 60 s | Server may be busy — wait and refresh |
| API 500 error | SSH to server: `docker logs public-sector-backend-1` |
