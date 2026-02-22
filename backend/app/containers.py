from dependency_injector import containers, providers

from app.application.audit_service import AuditService
from app.application.category_service import CategoryService
from app.application.product_service import ProductService
from app.application.offer_service import OfferService
from app.application.sale_service import SaleService
from app.application.dashboard_service import DashboardService
from app.application.user_service import UserService
from app.application.report_service import ReportService
from app.infrastructure.file_service import FileService
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.logging import configure_logging


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.presentation.routers.product_router",
            "app.presentation.routers.category_router",
            "app.presentation.routers.offer_router",
            "app.presentation.routers.sale_router",
            "app.presentation.routers.dashboard_router",
            "app.presentation.routers.auth_router",
            "app.presentation.routers.user_router",
            "app.presentation.routers.audit_router",
        ]
    )
    
    logging = providers.Singleton(configure_logging)
    
    file_service = providers.Singleton(FileService)
    cache_service = providers.Singleton(CacheService)
    unit_of_work = providers.Factory(SqlAlchemyUnitOfWork)

    # Audit service (used by other services)
    audit_service = providers.Factory(
        AuditService,
        uow=unit_of_work,
        logger=logging,
    )

    product_service = providers.Factory(
        ProductService,
        uow=unit_of_work,
        file_service=file_service,
        cache_service=cache_service,
        audit_service=audit_service,
        logger=logging,
    )

    category_service = providers.Factory(
        CategoryService,
        uow=unit_of_work,
        cache_service=cache_service,
        audit_service=audit_service,
        logger=logging,
    )

    offer_service = providers.Factory(
        OfferService,
        uow=unit_of_work,
        cache_service=cache_service,
        audit_service=audit_service,
        logger=logging,
    )

    sale_service = providers.Factory(
        SaleService,
        uow=unit_of_work,
        audit_service=audit_service,
        logger=logging,
    )

    dashboard_service = providers.Factory(
        DashboardService,
        uow=unit_of_work,
        logger=logging,
    )

    user_service = providers.Factory(
        UserService,
        uow=unit_of_work,
        audit_service=audit_service,
        logger=logging,
    )

    report_service = providers.Factory(
        ReportService,
        uow=unit_of_work,
        logger=logging,
    )

