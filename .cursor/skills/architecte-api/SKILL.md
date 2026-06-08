---
name: architecte-api
description: Architecte API FastAPI YurPass — modules métier, router/service/repository, schemas Pydantic, RBAC. Utiliser pour backend/**.
---

# Architecte API — YurPass

Rule : `architecte-api.mdc`.

## Module

`router → service → repository` + `schemas.py` + `permissions.py`

## Workflow

1. Domaine identifié
2. Module complet (pas juste router)
3. Pydantic in/out
4. RBAC dans permissions.py
5. Tests + migration Alembic

API : `/api/v1/`, UUID, pagination standard.
