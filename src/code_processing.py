"""Decoding and processing strings with short python programs. Mostly not written by me."""

# TODO specialize for this project

import ast
import re
import shutil
import subprocess
import urllib
from base64 import b64decode
from pathlib import Path
from tempfile import mkdtemp

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

    if failed:
        raise RuntimeError(f"Unexpected error while linting code: {code_string}")

    if result.stderr:
        raise RuntimeError(f"Finished with an error: {result.stderr} while lingting code: {code_string}")

    parsed = []
    for message in result.stdout.split("\n"):
        if message:  # ignores empty lines
            message = message[len(str(temp_file.resolve())) + 1 :]  # remove the name of the temporary file
            codes = re.findall(r"[A-Z]\d{3,4}", message)  # find codes e.g., E1234
            if not len(codes):  # if no code is found, the message is not valid
                raise RuntimeError(f"Failed to parse message: {message}")
            if codes[0] != "W292":  # ignore newline errors
                parsed.append((codes[0], message))

    return parsed
