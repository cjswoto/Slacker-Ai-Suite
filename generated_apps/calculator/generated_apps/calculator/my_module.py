from .calculator import Calculator
def multiply(a: int, b: int) -> Optional[int]:
    """Multiply two numbers."""
    try:
        result = Calculator().multiply(a, b)
    except ZeroDivisionError as e:
        raise ValueError("Cannot divide by zero") from e
    return result
