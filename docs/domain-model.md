# Domain model — ported from `law-system`

This document is the **specification** for the SaaS rewrite. All values, choices, and field names below come from the legacy desktop app (`/home/sergioseva/projects/law-system`) and should be re-implemented faithfully unless noted.

The legacy file references in this document are anchors (`file:line`) — read them while implementing the corresponding piece of `law-saas`.

---

## RBAC

Three roles, hierarchical (higher level inherits everything from below).

| Role | Level | Description |
|---|---|---|
| `admin` | 30 | Full control: user management, delete operations, demo seed. |
| `abogado` | 20 | Create/edit clients, actuaciones, documents. Cannot delete. |
| `secretario` | 10 | Read-only: view dashboard, clients, actuaciones, download docs. |

Permission constants (port to DRF permission classes in `tenants/permissions.py`):

- `PERM_READ` = `secretario`
- `PERM_WRITE` = `abogado`
- `PERM_DELETE` = `admin`
- `PERM_ADMIN` = `admin`

Source: `juridico_app/auth.py`.

---

## Entities

### Firm (tenant)

Not present in the legacy code (each install is one firm). New for SaaS:

- `id` UUID
- `subdomain` slug (unique; reserved list in `lawsaas/settings/base.py:RESERVED_SUBDOMAINS`)
- `name` text
- `wrapped_dek` text — per-firm data encryption key, wrapped with master KEK
- `created_at` timestamptz

### User

- `email` (unique, login identity)
- password (hashed via Django auth)
- standard `is_active`, `is_staff`, `is_superuser`

Note: legacy app had local `username`. SaaS uses email globally; firm membership is on `Membership`, not on `User`.

Source: `juridico_app/database.py:9–16` (legacy users table).

### Membership

- `user_id` → User
- `firm_id` → Firm
- `role` enum: `admin` | `abogado` | `secretario`
- `created_at`
- unique on `(user_id, firm_id)`

### Client

Encrypted JSON `payload` plus denormalized columns. Port the pattern from `juridico_app/database.py:23–37`.

**Encrypted in `payload`:**
- `full_name`
- `dni_cuil`
- `birth_date`
- `phone`
- `email`
- `address`
- `city`
- `employer`
- `insurer`
- `case_reason`
- `discharge_condition` (default: `"Sin incapacidad"`)
- `occupational_disease` (default: `"No"`)
- `document_checklist` — boolean per checklist item (see below)
- `profile_photo_path` — relative path under R2 prefix

**Denormalized plaintext columns (for filter/search/sort):**
- `tenant_id` (UUID, NOT NULL, RLS-policy gated)
- `full_name_display` (raw)
- `full_name_search` (lowercased, whitespace-collapsed)
- `dni_cuil_search` (digits only)
- `phone_search` (digits only)
- `city_display`
- `case_status` enum (see below; default `consulta`)
- `case_type` enum (see below; default `Extrajudicial`)
- `case_label` enum (see below)
- `first_visit_date` date
- `created_at`, `updated_at`

Indexes (port from `juridico_app/database.py:63–73`):
- `(full_name_search)`, `(dni_cuil_search)`, `(phone_search)`
- `(case_status, case_type, first_visit_date)`
- `(created_at DESC)`
- always include `(tenant_id, ...)` as a leading column for tenant-scoped scans

### Action (Actuación)

- `client_id` → Client (CASCADE)
- encrypted `payload`:
  - `description`
- denormalized columns:
  - `tenant_id`
  - `action_date` date
  - `next_action_date` date (nullable)
  - `next_step` text (the planned next step, plaintext for dashboard rollups)
  - `completed` bool
  - `created_at`

Indexes:
- `(client_id, action_date DESC)`
- `(client_id, next_action_date)`
- `(next_action_date, completed)` — for dashboard "upcoming" query

### Document

- `client_id` → Client (CASCADE)
- `tenant_id`
- `original_name_encrypted` text — encrypted with firm DEK
- `stored_key` text — opaque R2 object key (e.g., `firm-<uuid>/<client-id>/<random>`)
- `notes_encrypted` text (nullable)
- `mime_type` text
- `size_bytes` int
- `uploaded_at` timestamptz

Indexes:
- `(client_id, uploaded_at DESC)`

---

## Enumerations (Spanish — UI strings)

These are **not** translatable for v1; they're the canonical values in the DB.

```python
CASE_STATUSES = ["consulta", "en proceso", "demanda iniciada", "cerrado"]
CASE_TYPES = ["Extrajudicial", "Judicial"]
CASE_LABELS = ["", "+10", "-10"]
PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
PROFILE_PHOTO_SIZE = (280, 280)
DOCUMENT_CHECKLIST_ITEMS = [
    "DNI",
    "Denuncia",
    "Historia clinica",
    "Cd de la art",
    "Recibos de sueldo",
    "Informe",
    "Alta medica",
]
```

Source: `juridico_app/routes.py:36–49`.

Allowed upload extensions (legacy `Config.ALLOWED_EXTENSIONS`): `pdf, png, jpg, jpeg, webp, doc, docx, txt`. Max upload size: 16 MB.

---

## Pagination defaults

- Clients per page: 25
- Actions per page: 12
- Documents per page: 12

Source: `juridico_app/routes.py:51–53`. DRF `PAGE_SIZE` is set to 25 globally; override per-viewset where needed.

---

## Encryption

Two layers (envelope encryption):

1. **Master KEK** — single key in droplet env var (`MASTER_KEK`). Used only to wrap/unwrap firm DEKs. Never used to encrypt application data directly.
2. **Per-firm DEK** — generated at firm signup, stored as `firm.wrapped_dek` (= KEK-encrypted bytes), used to encrypt:
   - `client.payload`
   - `action.payload`
   - `document.original_name_encrypted`
   - `document.notes_encrypted`

Implementation: `apps/api/encryption/envelope.py`. Library: `cryptography.fernet.Fernet` (AES-128-CBC + HMAC-SHA256, authenticated). PBKDF2 not needed because KEK is already a Fernet key.

**Migration to KMS is purely an infra change** — re-wrap each `firm.wrapped_dek` with a KMS-derived KEK; data never gets re-encrypted.

---

## Tenant isolation (defense in depth)

Three layers, each independently sufficient:

1. **App layer.** `crm/managers.py:TenantManager` auto-applies `filter(tenant_id=request.firm.id)`. Devs never call `Client.objects.all()` without it.
2. **DB layer.** Every domain table has RLS policies. Set `app.tenant_id` per-connection in `tenants/middleware.py`. Migrations enable RLS with: `ALTER TABLE crm_client ENABLE ROW LEVEL SECURITY; CREATE POLICY tenant_isolation ON crm_client USING (tenant_id::text = current_setting('app.tenant_id', true));`
3. **API layer.** DRF serializers reject any payload whose `tenant_id` doesn't match `request.firm.id`.

---

## What's intentionally not ported

- **Werkzeug password hashing** → Django's default (PBKDF2-SHA256). Both are PBKDF2 underneath; no migration needed since there are no legacy users.
- **In-process rate limiter** (`juridico_app/routes.py:57–106`) → `django-ratelimit` with Redis backend.
- **Static KDF salt** (`juridico_app/security.py:12`) → not needed; Fernet keys *are* the salt-equivalent and are per-firm.
- **TTL dict cache** (`juridico_app/runtime_cache.py`) → Django cache framework backed by Redis.
- **Browser auto-open + PyInstaller logic** → irrelevant for a hosted SaaS.
- **`firm_settings` table** → small KV; if needed, model as a `JSONField` on `Firm` rather than a separate table.

---

## Open questions to resolve before Phase 2

- Is there a per-firm "billing tier" that gates feature access? (Likely deferred to post-beta.)
- Should `case_label` be free text instead of an enum? Legacy uses `["", "+10", "-10"]` — meaning is unclear from the code.
- Photo storage: encrypt the bytes too, or just rely on R2 ACLs + signed URLs? (Legacy stores photos under `static/` — i.e., publicly served. Reproducing that on R2 would require a public bucket policy, which is unsafe for client photos. Default to private bucket + signed GET URLs.)
