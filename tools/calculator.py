import ast
import operator

from langchain_core.tools import tool

from core.logging import log_call

# Strict allowlist of safe mathematical operators
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

def _safe_eval(node: ast.AST) -> float:
    # Block implicit types (like booleans/strings matching isinstance checks)
    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, float):
            raise ValueError("Only literal numbers are allowed.")
        return node.value
        
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        
        # Prevent CPU/Memory exhaustion attacks (e.g., 9**9**9)
        if isinstance(node.op, ast.Pow):
            if right > 1000 or left > 10000:
                raise ValueError("Exponent or base too large to calculate safely.")
                
        return _ALLOWED_OPERATORS[type(node.op)](left, right)
        
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
        
    raise ValueError("Invalid mathematical syntax.")

@tool
@log_call("tool.calculator")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (+, -, *, /, %, **, parentheses) 
    and return the numeric result. Use this for any math instead of 
    computing it yourself - you are not reliable at arithmetic."""
    if not expression or not expression.strip():
        return "Error: Expression cannot be empty."
        
    try:
        # Enforce evaluation mode to prevent execution of multi-line statements
        tree = ast.parse(expression.strip(), mode="eval")
        return str(_safe_eval(tree.body))
        
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as e:
        # Fall back to a clean message if the internal error string is empty
        error_msg = str(e).strip()
        return f"Error: {error_msg if error_msg else 'Invalid mathematical expression.'}"
