class AppError(Exception):
    """Базовое исключение приложения."""

    status_code: int = 400
    detail: str = "Ошибка"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class UnauthorizedError(AppError):
    """Если пользовать не авторизован, вызывай эту ошибку"""

    status_code = 401
    detail = "Пользователь, не авторизован"


class ForbiddenError(AppError):
    """У пользователя нету прав на это действие"""

    status_code = 403
    detail = "Доступ запрещён"


class NotFoundError(AppError):
    """Либо файла реально нету, либо у пользователя нет прав смотреть данный файл"""

    status_code = 404
    detail = "Не найдено"


class ConflictError(AppError):
    """Значит он уже создавал авторизацию"""

    status_code = 409
    detail = "Конфликт"
