"""Tests for the generic AST-based run_tests validator logic.

We test the logic directly (without importing the @tool wrapper) so
tests run without needing a live LLM or env vars.
"""
import ast


# ── Replicate validator logic for isolated testing ─────────────────────────

def _validate(code: str, original_code: str = "") -> dict:
    """Mirror of the generic run_tests() logic used in tools.py."""
    results = {"passed": False, "errors": [], "message": ""}

    # 1. Syntax check
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        results["errors"].append(f"Syntax error at line {e.lineno}: {e.msg}")
        results["message"] = f"Tests failed: {len(results['errors'])} issue(s) found"
        return results

    # 2. Preserve original function signatures
    if original_code:
        try:
            orig_tree = ast.parse(original_code)
            original_funcs = {
                node.name
                for node in ast.walk(orig_tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            fixed_funcs = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            missing = original_funcs - fixed_funcs
            if missing:
                results["errors"].append(
                    f"Functions removed from original code: {missing}. "
                    "All original functions must be preserved."
                )
                results["message"] = f"Tests failed: {len(results['errors'])} issue(s) found"
                return results
        except SyntaxError:
            pass  # original was broken — skip comparison

    # 3. Bare except check
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            results["errors"].append(
                "Bare 'except:' found — use specific exception types"
            )

    results["passed"] = len(results["errors"]) == 0
    results["message"] = (
        "All tests passed! The fix is valid."
        if results["passed"]
        else f"Tests failed: {len(results['errors'])} issue(s) found"
    )
    return results


# ── Test fixtures ───────────────────────────────────────────────────────────

ORIGINAL = '''
def get_user_data(user_id: int):
    user_config = {"name": "Alice"}
    api_key = user_config["api_key"]  # bug: key missing
    return {"api_key": api_key}
'''

FIXED = '''
def get_user_data(user_id: int):
    user_config = {"name": "Alice"}
    api_key = user_config.get("api_key", "default")
    return {"api_key": api_key}
'''

BROKEN_SYNTAX = '''
def get_user_data(user_id: int):
    user_config = {"name": "Alice"
    return user_config
'''

MISSING_FUNCTION = '''
def something_else():
    pass
'''

BARE_EXCEPT = '''
def get_user_data(user_id: int):
    try:
        return {"ok": True}
    except:
        return {"ok": False}
'''


# ── Tests ───────────────────────────────────────────────────────────────────

def test_valid_fix_passes():
    result = _validate(FIXED, ORIGINAL)
    assert result["passed"] is True
    assert result["errors"] == []


def test_syntax_error_fails():
    result = _validate(BROKEN_SYNTAX, ORIGINAL)
    assert result["passed"] is False
    assert any("Syntax error" in e for e in result["errors"])


def test_missing_function_fails():
    result = _validate(MISSING_FUNCTION, ORIGINAL)
    assert result["passed"] is False
    assert any("Functions removed" in e for e in result["errors"])


def test_bare_except_flagged():
    result = _validate(BARE_EXCEPT, ORIGINAL)
    assert result["passed"] is False
    assert any("Bare" in e and "except" in e for e in result["errors"])


def test_broken_original_skips_function_check():
    """If original code has syntax errors, skip function preservation check."""
    result = _validate(FIXED, "def broken(:")
    assert result["passed"] is True


def test_no_original_skips_function_check():
    """Without original_code, function check is skipped."""
    result = _validate(FIXED)
    assert result["passed"] is True
