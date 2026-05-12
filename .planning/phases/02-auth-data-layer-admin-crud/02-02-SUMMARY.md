---
plan: 02-02
phase: 02
status: complete
---

## Plan 02-02: Data Layer Models & Admin CRUD APIs — COMPLETE

### Tasks Completed
1. ✅ Category model created (category_code, name, sort_order, is_active)
2. ✅ Style model created (name, cover_image_url, rule_version, sort_order)
3. ✅ Term model created (type, content, weight, scope JSON, sort_order)
4. ✅ PromoRule model created (name, slot_template JSON, watermark_config JSON, version)
5. ✅ All models registered in models/__init__.py
6. ✅ Pydantic schemas created for all 4 entities (Create/Update/Out)
7. ✅ Generic CRUD helper service created (list/get/create/update/delete with tenant scoping)
8. ✅ CRUD API routers created for all 4 entities (5 endpoints each: list/create/get/update/delete)
9. ✅ Alembic migration 003_data_layer created and applied (4 tables)
10. ✅ Migration verified at head 003_data_layer

### Key Files Created/Modified
- python-bff/app/models/category.py — Category(TenantModel)
- python-bff/app/models/style.py — Style(TenantModel)
- python-bff/app/models/term.py — Term(TenantModel) with JSON scope
- python-bff/app/models/promo_rule.py — PromoRule(TenantModel) with JSON fields
- python-bff/app/schemas/category.py — CategoryCreate/Update/Out
- python-bff/app/schemas/style.py — StyleCreate/Update/Out
- python-bff/app/schemas/term.py — TermCreate/Update/Out
- python-bff/app/schemas/promo_rule.py — PromoRuleCreate/Update/Out
- python-bff/app/services/crud.py — Generic async CRUD with tenant isolation
- python-bff/app/api/v1/categories.py — 5 endpoints
- python-bff/app/api/v1/styles.py — 5 endpoints
- python-bff/app/api/v1/terms.py — 5 endpoints
- python-bff/app/api/v1/promo_rules.py — 5 endpoints
- python-bff/alembic/versions/003_data_layer.py — 4 tables migration

### Verification
- Alembic migration applied (003_data_layer at head)
- 20 new CRUD endpoints registered (5 per entity × 4 entities)
- All queries auto-scoped via get_current_tenant_id dependency
- Soft-delete pattern (is_active=False) for all entities

### Notes
- .gitignore fixed to track alembic migration files
- Term.scope uses MySQL JSON column for category_ids/style_ids arrays
- PromoRule.slot_template and watermark_config use MySQL JSON columns
