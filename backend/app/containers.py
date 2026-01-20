from dependency_injector import containers, providers

from app.application.category_service import CategoryService
from app.application.product_service import ProductService
from app.application.offer_service import OfferService
from app.infrastructure.file_service import FileService
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.logging import configure_logging


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.presentation.routers.product_router",
            "app.presentation.routers.category_router",
            "app.presentation.routers.offer_router",
        ]
    )
    
    logging = providers.Singleton(configure_logging)
    
    file_service = providers.Singleton(FileService)
    unit_of_work = providers.Factory(SqlAlchemyUnitOfWork)

    product_service = providers.Factory(
        ProductService,
        uow=unit_of_work,
        file_service=file_service,
        logger=logging,
    )

    category_service = providers.Factory(
        CategoryService,
        uow=unit_of_work,
        logger=logging,
    )

    offer_service = providers.Factory(
        OfferService,
        uow=unit_of_work,
        logger=logging,
    )
