from fastapi import HTTPException, status


class DocSuiteException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedException(DocSuiteException):
    def __init__(self, detail: str = "Credenciales invalidas") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)
