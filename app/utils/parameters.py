from fastapi import Query

Limit: int = Query(default=10, lt=50, gt=0)
Offset: int = Query(default=0, ge=0)
