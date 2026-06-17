# Plantillas — copiar al crear un módulo CRUD

Ver `app/services/catalog_service.py` y `app/routers/catalog.py` como referencia completa.

## repository.py.template

```python
from app.models.{model_module} import {ModelClass}
from app.repositories.base import BaseRepository


class {ModelClass}Repository(BaseRepository[{ModelClass}]):
    model = {ModelClass}
```

## service.py.template

```python
from sqlalchemy.orm import Session

from app.repositories.{repo_module} import {ModelClass}Repository
from app.schemas.{schema_module} import {ModelClass}Create, {ModelClass}Update
from app.services.base import BaseService


class {ModelClass}Service(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = {ModelClass}Repository(db, tenant_id=tenant_id)

    def list_items(self):
        return self.repo.list_all()

    def create_item(self, payload: {ModelClass}Create):
        entity = {ModelClass}(tenant_id=self.repo.tenant_id, **payload.model_dump())
        self.repo.add(entity)
        self.commit()
        return self.repo.refresh(entity)
```

## router.py.template

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.{schema_module} import {ModelClass}Create, {ModelClass}Out, {ModelClass}Update
from app.services.{service_module} import {ModelClass}Service

router = APIRouter(prefix="/{route_prefix}", tags=["{route_prefix}"])


@router.get("", response_model=list[{ModelClass}Out])
def list_items(ctx: TenantContext = Depends(get_tenant_context), db: Session = Depends(get_db)):
    service = {ModelClass}Service(db, tenant_id=ctx.tenant.id)
    return service.list_items()
```
