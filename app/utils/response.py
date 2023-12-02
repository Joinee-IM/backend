import ast
import enum
import typing

import pydantic

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


class_names: typing.List[str] = ClassNameExtractor('app/exceptions/__init__.py').class_names
class_enum = enum.Enum('ErrorMessage', {class_name: class_name for class_name in class_names})


class Response(pydantic.BaseModel, typing.Generic[T]):
    data: T | None = None
    error: class_enum | None = None
