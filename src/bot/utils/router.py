from typing import Any, Callable, Optional, Type, TypeVar

from aiogram import Router

# Type for dependency factory
T = TypeVar("T")


def create_router(name: Optional[str] = None, **kwargs) -> Router:
    """
    Create a router with predefined dependencies

    Args:
        name: Router name
        **kwargs: Additional router parameters

    Returns:
        Router: Configured router instance
    """
    router = Router(name=name, **kwargs)

    # Add dependencies for handlers
    router.message.middleware()
    router.callback_query.middleware()

    return router


def get_repository_factory(repo_class: Type[T], db_connector: Any) -> Callable[[], T]:
    """
    Create a factory function for repository instances

    Args:
        repo_class: Repository class
        db_connector: Database connector instance

    Returns:
        Callable: Factory function that returns repository instance
    """

    def factory() -> T:
        return repo_class(db_connector)

    return factory


# Example usage:
# db_connector = get_db_connector()  # Get database connector
# user_repo_factory = get_repository_factory(UserRepository, db_connector)
#
# # Create router with user repository dependency
# router = create_router(name="user_dialog")
# router.message.outer_middleware(UserRepositoryMiddleware(user_repo_factory))
# router.callback_query.outer_middleware(UserRepositoryMiddleware(user_repo_factory))
