"""Decoding python code. TODO adapted from ..."""

# TODO specialize for this project

import ast
import re
import shutil
import subprocess
import urllib
import warnings
from base64 import b64decode
from pathlib import Path
from tempfile import mkdtemp

from unidecode import unidecode


def parse_code_string(code: str, raise_error: bool = False) -> str:
    """Decode and standardize base64 encoded python code."""
    return repair_code(decode_string(code, raise_error=raise_error), raise_error=raise_error)


def decode_string(encoded_string: str, raise_error: bool = False) -> str:
    """Decode a string containing base64 encoded python code."""
    try:
        unquoted = urllib.parse.unquote(encoded_string, errors="strict")
    except ValueError:
        if raise_error:
            raise RuntimeError("Could not unquote string.")
        return ""

    try:
        code = unidecode(b64decode(unquoted, altchars="  ").decode("utf-8", errors="strict"))
    except ValueError:
        if raise_error:
            raise RuntimeError("Could not decode string.")
        return ""

    return code.strip()


def repair_code(code, raise_error=False):
    """Fix known issues with the logging process."""
    code = fix_indent(code, raise_error=raise_error)
    err = get_parse_error(code)
    if err is None:
        return code
    if "leading zeros" in str(err):
        code = re.sub(r"0+(\d+)", r"\1", code)
    if "<>" in code:
        code = code.replace("<>", "!=")
    if get_parse_error(code) is None:
        return code
    if raise_error:
        raise ValueError(f"{err}\n{code}")
    return ""


def fix_indent(code, raise_error=False):
    """Fix indentation."""
    if valid_indent(code):
        return code
    for spaces_per_tab in [8, 4]:
        idented = code.replace("\t", " " * spaces_per_tab)
        # Change of indentation might lead to a syntax error
        if get_parse_error(idented) is None:
            return idented
    if raise_error:
        raise ValueError(f"Invalid indent: {code}")
    return f"Invalid indent: {code}"


def valid_indent(code):
    """Check whether the code is indented properly."""
    err = get_parse_error(code)
    # TabError is subclass of IndentationError
    return not isinstance(err, IndentationError)


def get_parse_error(code):
    """Check if the code can be parsed by the AST."""
    try:
        ast.parse(code)
    except SyntaxError as err:
        return err


def generate_linter_messages(code_string: str) -> list[tuple[str, str]]:
    """Generate linter messages for the given code string. Beware, I could not find a fixed format for the messages, so this is a bit of a hack.

    Arguments:
        code_string -- Python string with the code to be linted.

    Returns:
        Message code and text pairs.
    """
    failed = False
    try:
        temp_dir = Path(mkdtemp())
        temp_file = temp_dir / "temp.py"
        with open(temp_file, "w") as f:
            f.write(code_string)
        result = subprocess.run(["py", "-m", "edulint", "check", temp_file], text=True, capture_output=True)
    except:
        failed = True
    finally:
        shutil.rmtree(temp_dir)

    parsed = []

    if failed:
        if result.stderr:
            # handle edulint error messages
            return parsed.append(("SYNTAX_ERROR", result.stderr))
        raise RuntimeError(f"Unexpected error while linting code: {code_string}")

    if result.stderr:
        warnings.warn(result.stderr)

    if result.stderr:
        parsed.append(("SYNTAX_ERROR", result.stderr))

    for message in result.stdout.split("\n"):
        if message:  # ignores empty lines
            message = message[len(str(temp_file.resolve())) + 1 :]  # remove the name of the temporary file
            codes = re.findall(r"[A-Z]\d{3,4}", message)  # find codes e.g., E1234
            if not len(codes):  # if no code is found, the message is not valid
                raise RuntimeError(f"Failed to parse message: {message}")
            if codes[0] != "W292":  # ignore newline errors
                parsed.append((codes[0], message))

    return parsed
