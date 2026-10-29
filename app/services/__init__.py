from __future__ import annotations

from dataclasses import dataclass

from app.repositories.uow import UnitOfWork
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.dashboard_service import DashboardService
from app.services.export_service import ExportService
from app.services.ticket_service import TicketService


@dataclass(frozen=True, slots=True)
class Services:
    auth: AuthService
    tickets: TicketService
    comments: CommentService
    dashboard: DashboardService
    export: ExportService


def build_services(uow: UnitOfWork) -> Services:
    return Services(
        auth=AuthService(uow),
        tickets=TicketService(uow),
        comments=CommentService(uow),
        dashboard=DashboardService(uow),
        export=ExportService(uow),
    )
