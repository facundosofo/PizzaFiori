from dependency_injector import containers, providers

from app.application.category_service import CategoryService
from app.application.product_service import ProductService
from app.infrastructure.file_service import FileService
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.presentation.routers.product_router",
            "app.presentation.routers.category_router",
        ]
    )

    # Singleton: una sola instancia de FileService para toda la app
    file_service = providers.Singleton(FileService)

    # Factory: nueva instancia de UnitOfWork para cada request
    unit_of_work = providers.Factory(SqlAlchemyUnitOfWork)

    # ProductService con sus dependencias inyectadas
    product_service = providers.Factory(
        ProductService,
        uow=unit_of_work,
        file_service=file_service,
    )

    # CategoryService con su dependencia inyectada
    category_service = providers.Factory(
        CategoryService,
        uow=unit_of_work,
    )
