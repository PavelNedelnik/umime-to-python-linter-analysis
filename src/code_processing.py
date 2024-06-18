"""Decoding and processing strings with short python programs. Mostly not written by me."""

# TODO specialize for this project

import ast
import re
import urllib
from base64 import b64decode

from unidecode import unidecode


def decode_code_string(code: str) -> str:
    """Decode and standardize base64 encoded python code."""
    return unidecode(clean_code(parse_code(code)))


def parse_code(encoded_field, raise_error=False):
    """Parse url encoded, base64 encoded python code."""
    try:
        unquoted = urllib.parse.unquote(encoded_field, errors="strict")
    except ValueError:
        if raise_error:
            raise
        return "INVALID: url-unquoting"

    try:
        code = b64decode(unquoted, altchars="  ").decode("utf-8", errors="strict")
        # code = um.utils.code_processing.decode_program(unquoted)
    except ValueError:
        if raise_error:
            raise
        return "INVALID: b64-decoding"

    return code.strip()


def clean_code(code, raise_error=False):
    """Fix some quirks allowed by the online python interpreter."""
    code = fix_indent(code, raise_error=raise_error)
    if code.startswith("INVALID"):
        return code
    err = get_parse_error(code)
    if not err:
        return code
    if "leading zeros" in str(err):
        code = re.sub(r"0+(\d+)", r"\1", code)
    if "<>" in code:
        code = code.replace("<>", "!=")
    if is_valid_python(code):
        return code
    if raise_error:
        raise ValueError(f"{err}\n{code}")
    return "INVALID: syntax"


def fix_indent(code, raise_error=False):
    """Fix indent."""
    if valid_indent(code):
        return code
    for spaces_per_tab in [8, 4]:
        code2 = code.replace("\t", " " * spaces_per_tab)
        # It's not sufficient to ask for valid indent, since
        # the attempted fix may lead to correct indent but
        # a syntax error (e.g., else clause too deep).
        if is_valid_python(code2):
            return code2
    if raise_error:
        raise ValueError(f"Invalid indent: {code}")
    return f"Invalid indent: {code}"


def valid_indent(code):
    """Fix indent."""
    err = get_parse_error(code)
    # TabError is subclass of IndentationError
    return not isinstance(err, IndentationError)


def get_parse_error(code):
    """Fix indent."""
    try:
        ast.parse(code)
    except SyntaxError as err:
        return err


def is_valid_python(code):
    """Check if code can be parsed by the AST."""
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def debug_invalid(submits):
    """Generate a report of invalid programs."""
    mask = submits.code.str.startswith("INVALID")
    invalid_submits = submits[mask]
    n_invalid = mask.sum()
    p_invalid = mask.mean()
    print(f"invalid programs: {n_invalid}/{len(submits)} ({p_invalid:.2%})\n")
    print(invalid_submits.code.value_counts())
    return submits


def filter_valid(submits, verbose=True):
    """Allow only valid programs to pass through."""
    if verbose:
        print("Filtering invalid programs.")
        debug_invalid(submits)
    return submits.query("~code.str.startswith('INVALID')")
