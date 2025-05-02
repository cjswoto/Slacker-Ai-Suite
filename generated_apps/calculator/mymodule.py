from typing import Optional, Union
class Calculator:
    """Class for performing basic arithmetic operations."""
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def multiply(a: int, b: int) -> Optional[int]:
        """Multiply two numbers.
        
        Args:
            a (int): The first number to multiply.
            b (int): The second number to multiply.
        
        Returns:
            Optional[int]: The result of the multiplication, or None if the input is invalid.
        
        Raises:
            ValueError: If `b` is zero.
        """
        try:
            return a * b
        except ZeroDivisionError as e:
            raise ValueError("Cannot divide by zero") from e
