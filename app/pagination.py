import typing
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Query, Session
from starlette.requests import Request

from app.candidates.schemas import PaginationResult


class Paginator:

    def __init__(self, objects, session: Session, query: Query, page: int, per_page: int, request: Request):
        self.session = session
        self.total_objects = objects
        self.query = query
        self.page = page
        self.per_page = per_page
        self.limit = per_page * page
        self.offset = (page - 1) * per_page
        self.request = request
        self.next_page = ''
        self.previous_page = ''

    def _get_total_count(self, model) -> int:
        total_objects = self.total_objects
        total_pages = self._get_number_of_pages(model)
        if total_objects == 0:
            return 0
        if self.page > total_pages:
            print(f"Page {self.page} is out of range (Max: {total_pages}). Returning 0.")
            return 0
        if self.per_page >= total_objects:
            return total_objects
        return self.session.execute(select(func.count()).select_from(self.query.subquery())).scalar()

    def _get_number_of_pages(self, model: str) -> int:
        total_objects = self.total_objects
        if total_objects == 0:
            return 1
        pages = ceil(total_objects / self.per_page)
        return pages

    def _get_next_page(self, model) -> typing.Optional[str]:
        if self.page >= self._get_number_of_pages(model=model):
            return None
        return str(self.request.url.include_query_params(page=self.page + 1))

    def _get_previous_page(self) -> typing.Optional[str]:
        if self.page == 1:
            return None
        return str(self.request.url.include_query_params(page=self.page - 1))

    async def get_response(self, model: str, response_model_schema) -> PaginationResult:
        return PaginationResult(
            count=self._get_total_count(model),
            next_page=self._get_next_page(model),
            previous_page=self._get_previous_page(),
            current_page=self.page,
            total_pages=self._get_number_of_pages(model),
            items=[response_model_schema.model_validate(item).model_dump() for item in self.session.scalars(self.query.limit(self.per_page).offset(self.offset))]
        )


async def paginate(model, response_model_schema, request: Request, db: Session, query: Query, page: int, per_page: int, objects) -> dict:
    with db as session:
        paginator = Paginator(session=session, query=query, page=page, per_page=per_page, request=request, objects=objects)
        return await paginator.get_response(model, response_model_schema)
