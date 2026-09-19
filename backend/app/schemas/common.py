import math
from typing import Generic, List, Optional, TypeVar
from fastapi import Request
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[T]


def paginate_queryset(
    items: List[T],
    total_count: int,
    page: int,
    page_size: int,
    request: Request,
) -> PaginatedResponse[T]:
    base_url = str(request.url).split("?")[0]
    query_params = dict(request.query_params)

    total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1

    next_url = None
    if page < total_pages:
        next_params = query_params.copy()
        next_params["page"] = str(page + 1)
        next_params["page_size"] = str(page_size)
        query_str = "&".join(f"{k}={v}" for k, v in next_params.items())
        next_url = f"{base_url}?{query_str}"

    prev_url = None
    if page > 1 and page <= total_pages + 1:
        prev_params = query_params.copy()
        if page - 1 == 1:
            prev_params.pop("page", None)
        else:
            prev_params["page"] = str(page - 1)
        prev_params["page_size"] = str(page_size)
        query_str = "&".join(f"{k}={v}" for k, v in prev_params.items())
        prev_url = f"{base_url}?{query_str}"

    return PaginatedResponse(
        count=total_count,
        next=next_url,
        previous=prev_url,
        results=items,
    )
