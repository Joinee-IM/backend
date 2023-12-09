import ast
import enum
import typing

import pydantic
from fastapi import responses

from app.const import COOKIE_ACCOUNT_KEY, COOKIE_TOKEN_KEY, EXCEPTION_CLASS_DEFINITION_PATH

T = typing.TypeVar('T')


class ClassNameExtractor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.class_names = []
        with open(file_path, 'r') as file:
            content = file.read()
            tree = ast.parse(content)
        self.visit(tree)

    def visit_ClassDef(self, node):
        self.class_names.append(node.name)
        self.generic_visit(node)


class_names: typing.List[str] = ClassNameExtractor(EXCEPTION_CLASS_DEFINITION_PATH).class_names
class_enum = enum.Enum('ErrorMessage', {class_name: class_name for class_name in class_names})


class Response(pydantic.BaseModel, typing.Generic[T]):
    data: T | None = None
    error: class_enum | None = None


def update_cookie(
        response: responses.Response,
        account_id: int = "",
        token: str = "",
) -> responses.Response:
    response.set_cookie(key=COOKIE_ACCOUNT_KEY, value=str(account_id), samesite='none', secure=True, httponly=True)
    response.set_cookie(key=COOKIE_TOKEN_KEY, value=str(token), samesite='none', secure=True, httponly=True)
    return response
