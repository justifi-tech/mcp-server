"""Auto-generate tool schemas from function signatures and docstrings.

This module provides functionality to automatically generate LangChain tool
schemas from JustiFi tool functions, including handling decorated functions
and parsing docstrings for parameter descriptions.
"""

from __future__ import annotations

import ast
import inspect
from typing import Any, get_type_hints


def extract_function_info(func) -> dict[str, Any]:
    """Extract parameter info from function, handling decorators.

    Args:
        func: The function to extract information from

    Returns:
        Dictionary containing function parameter information
    """
    # Find the function name by checking the tools module
    try:
        from .. import tools

        # Find the function name in the tools module
        target_func_name = None
        for attr_name in dir(tools):
            if not attr_name.startswith("_"):
                attr_value = getattr(tools, attr_name, None)
                if attr_value is func:
                    target_func_name = attr_name
                    break

        if target_func_name:
            # Now find the original module that defines this function
            # The function should be importable from one of the tool modules
            possible_modules = [
                "python.tools.payouts",
                "python.tools.payments",
                "python.tools.balances",
                "python.tools.checkouts",
                "python.tools.disputes",
                "python.tools.payment_method_groups",
                "python.tools.payment_methods",
                "python.tools.proceeds",
                "python.tools.refunds",
                "python.tools.sub_accounts",
            ]

            for module_name in possible_modules:
                try:
                    module = __import__(module_name, fromlist=[target_func_name])
                    if hasattr(module, target_func_name):
                        # Get the module source and parse it
                        module_source = inspect.getsource(module)
                        tree = ast.parse(module_source)

                        # Look for the function definition in the AST
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                                if node.name == target_func_name:
                                    # Found the function, build type hints from AST
                                    type_hints = {}
                                    for arg in node.args.args:
                                        if arg.annotation:
                                            try:
                                                if isinstance(arg.annotation, ast.Name):
                                                    if arg.annotation.id == "str":
                                                        type_hints[arg.arg] = str
                                                    elif arg.annotation.id == "int":
                                                        type_hints[arg.arg] = int
                                                    elif arg.annotation.id == "float":
                                                        type_hints[arg.arg] = float
                                                    elif arg.annotation.id == "bool":
                                                        type_hints[arg.arg] = bool
                                                    else:
                                                        type_hints[arg.arg] = (
                                                            str  # Default
                                                        )
                                                elif isinstance(
                                                    arg.annotation, ast.Constant
                                                ):
                                                    type_hints[arg.arg] = (
                                                        type(arg.annotation.value)
                                                        if arg.annotation.value
                                                        else str
                                                    )
                                                else:
                                                    type_hints[arg.arg] = str  # Default
                                            except Exception:
                                                type_hints[arg.arg] = str  # Default

                                    return parse_function_ast(node, type_hints)
                        break
                except (ImportError, AttributeError):
                    continue

    except Exception:
        pass

    # Try to get original function through __wrapped__
    original_func = func
    while hasattr(original_func, "__wrapped__"):
        original_func = original_func.__wrapped__

    # Fallback to basic signature inspection
    try:
        type_hints = get_type_hints(original_func)
    except Exception:
        type_hints = {}

    return parse_function_signature(original_func, type_hints)


def parse_function_ast(
    func_def: ast.FunctionDef, type_hints: dict[str, Any]
) -> dict[str, Any]:
    """Parse function AST to extract parameter information.

    Args:
        func_def: AST function definition
        type_hints: Type hints dictionary

    Returns:
        Dictionary containing function parameter information
    """
    parameters = {}

    for arg in func_def.args.args:
        param_name = arg.arg

        # Get type from type hints or AST annotation
        param_type = type_hints.get(param_name, str)
        if param_type is str and arg.annotation:
            # Try to extract type from AST annotation
            try:
                if isinstance(arg.annotation, ast.Name):
                    if arg.annotation.id == "str":
                        param_type = str
                    elif arg.annotation.id == "int":
                        param_type = int
                    elif arg.annotation.id == "float":
                        param_type = float
                    elif arg.annotation.id == "bool":
                        param_type = bool
                elif isinstance(arg.annotation, ast.Constant):
                    # Handle newer AST format
                    if arg.annotation.value is str:
                        param_type = str
            except Exception:
                param_type = str

        param_info = {"name": param_name, "type": param_type, "optional": False}

        # Check if parameter has a default value
        defaults_start = len(func_def.args.args) - len(func_def.args.defaults)
        arg_index = func_def.args.args.index(arg)
        if arg_index >= defaults_start:
            param_info["optional"] = True
            default_index = arg_index - defaults_start
            try:
                default_value = ast.literal_eval(func_def.args.defaults[default_index])
                param_info["default"] = default_value
            except (ValueError, SyntaxError):
                # If we can't evaluate the default, assume it exists but unknown
                param_info["default"] = None

        parameters[param_name] = param_info

    return {"parameters": parameters}


def parse_function_signature(func, type_hints: dict[str, Any]) -> dict[str, Any]:
    """Fallback method to parse function signature directly.

    Args:
        func: The function to parse
        type_hints: Type hints dictionary

    Returns:
        Dictionary containing function parameter information
    """
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        # If signature inspection fails, return minimal info
        return {"parameters": {}}

    parameters = {}

    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name, param.annotation)
        if param_type is inspect.Parameter.empty:
            param_type = str

        param_info = {
            "name": param_name,
            "type": param_type,
            "optional": param.default is not inspect.Parameter.empty,
        }

        if param.default is not inspect.Parameter.empty:
            param_info["default"] = param.default

        parameters[param_name] = param_info

    return {"parameters": parameters}


def generate_langchain_schema(tool_name: str, func) -> dict[str, Any]:
    """Generate LangChain schema from function.

    Args:
        tool_name: Name of the tool
        func: The tool function

    Returns:
        LangChain-compatible schema dictionary
    """
    func_info = extract_function_info(func)

    # Extract docstring for descriptions
    description = extract_description(func)
    arg_descriptions = extract_args_from_docstring(func)

    # Build schema
    schema = {
        "name": tool_name,
        "description": description,
        "parameters": {"type": "object", "properties": {}, "required": []},
    }

    # Add parameters (skip 'client' parameter)
    for param_name, param_info in func_info["parameters"].items():
        if param_name != "client":
            param_description = arg_descriptions.get(
                param_name, f"{param_name} parameter"
            )

            schema["parameters"]["properties"][param_name] = {
                "type": convert_python_type_to_json_schema(param_info["type"]),
                "description": param_description,
            }

            if not param_info.get("optional", False):
                schema["parameters"]["required"].append(param_name)

    return schema


def extract_description(func) -> str:
    """Extract description from function docstring.

    Args:
        func: The function to extract description from

    Returns:
        Description string
    """
    # Try to get the docstring from the original source
    doc = get_original_docstring(func)

    if not doc:
        # Fallback to the function name
        func_name = getattr(func, "__name__", "unknown")
        if func_name == "wrapper":
            # Try to find the original function name
            try:
                from .. import tools

                for attr_name in dir(tools):
                    if not attr_name.startswith("_"):
                        attr_value = getattr(tools, attr_name, None)
                        if attr_value is func:
                            func_name = attr_name
                            break
            except Exception:
                pass
        return f"Execute {func_name} operation"

    # Get the first line as the main description
    lines = doc.split("\n")
    description = lines[0].strip()

    # Remove trailing period if present for consistency
    if description.endswith("."):
        description = description[:-1]

    return description


def get_original_docstring(func) -> str | None:
    """Get the original docstring from a potentially decorated function."""
    # First try the standard approach
    doc = inspect.getdoc(func)
    if doc:
        return doc

    # For decorated functions, find the original docstring from the source
    try:
        from .. import tools

        # Find the function name in the tools module
        target_func_name = None
        for attr_name in dir(tools):
            if not attr_name.startswith("_"):
                attr_value = getattr(tools, attr_name, None)
                if attr_value is func:
                    target_func_name = attr_name
                    break

        if target_func_name:
            # Find the original module and get the AST
            possible_modules = [
                "python.tools.payouts",
                "python.tools.payments",
                "python.tools.balances",
                "python.tools.checkouts",
                "python.tools.disputes",
                "python.tools.payment_method_groups",
                "python.tools.payment_methods",
                "python.tools.proceeds",
                "python.tools.refunds",
                "python.tools.sub_accounts",
            ]

            for module_name in possible_modules:
                try:
                    module = __import__(module_name, fromlist=[target_func_name])
                    if hasattr(module, target_func_name):
                        # Get the module source and parse it
                        module_source = inspect.getsource(module)
                        tree = ast.parse(module_source)

                        # Look for the function definition in the AST
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                                if node.name == target_func_name:
                                    # Extract docstring from AST
                                    if (
                                        node.body
                                        and isinstance(node.body[0], ast.Expr)
                                        and isinstance(node.body[0].value, ast.Constant)
                                        and isinstance(node.body[0].value.value, str)
                                    ):
                                        return node.body[0].value.value
                        break
                except (ImportError, AttributeError):
                    continue
    except Exception:
        pass

    return None


def extract_args_from_docstring(func) -> dict[str, str]:
    """Extract argument descriptions from docstring.

    Args:
        func: The function to extract argument descriptions from

    Returns:
        Dictionary mapping parameter names to descriptions
    """
    doc = get_original_docstring(func)
    if not doc:
        return {}

    args = {}
    lines = doc.split("\n")

    in_args_section = False
    current_arg = None
    current_description = ""

    for line in lines:
        line = line.strip()

        if line.startswith("Args:"):
            in_args_section = True
            continue

        if in_args_section:
            if line.startswith(
                ("Returns:", "Raises:", "Example:", "Examples:", "Note:", "Notes:")
            ):
                # Save the last argument if we were processing one
                if current_arg and current_description:
                    args[current_arg] = current_description.strip()
                break

            # Check if this line starts a new argument
            if ":" in line and not line.startswith(" "):
                # Save previous argument if exists
                if current_arg and current_description:
                    args[current_arg] = current_description.strip()

                # Parse new argument
                parts = line.split(":", 1)
                current_arg = parts[0].strip()
                current_description = parts[1].strip() if len(parts) > 1 else ""
            elif current_arg and line:
                # Continue description on next line
                current_description += " " + line

    # Don't forget the last argument
    if current_arg and current_description:
        args[current_arg] = current_description.strip()

    return args


def convert_python_type_to_json_schema(python_type: Any) -> str:
    """Convert Python type annotation to JSON Schema type.

    Args:
        python_type: Python type annotation

    Returns:
        JSON Schema type string
    """
    # Handle None type
    if python_type is type(None):
        return "null"

    # Handle basic types
    if python_type is str:
        return "string"
    elif python_type is int:
        return "integer"
    elif python_type is float:
        return "number"
    elif python_type is bool:
        return "boolean"
    elif python_type is list:
        return "array"
    elif python_type is dict:
        return "object"

    # Handle type strings (when type hints fail)
    if isinstance(python_type, str):
        type_str = python_type.lower()
        if "str" in type_str:
            return "string"
        elif "int" in type_str:
            return "integer"
        elif "float" in type_str:
            return "number"
        elif "bool" in type_str:
            return "boolean"
        elif "list" in type_str:
            return "array"
        elif "dict" in type_str:
            return "object"

    # Handle generic types and unions
    try:
        type_str = str(python_type)
    except Exception:
        # If str() fails, default to string
        return "string"

    # Handle Optional[T] and Union[T, None]
    if "Union" in type_str and "NoneType" in type_str:
        # Extract the non-None type from Union
        if "str" in type_str:
            return "string"
        elif "int" in type_str:
            return "integer"
        elif "float" in type_str:
            return "number"
        elif "bool" in type_str:
            return "boolean"
        elif "list" in type_str:
            return "array"
        elif "dict" in type_str:
            return "object"

    # Handle list[T] generic
    if type_str.startswith("list[") or "List[" in type_str:
        return "array"

    # Handle dict[K, V] generic
    if type_str.startswith("dict[") or "Dict[" in type_str:
        return "object"

    # Default fallback
    return "string"
