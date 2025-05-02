import argparse
from mymodule import multiply
def main() -> None:
    """Entry point of the program."""
    # Parse command line arguments using argparse module
    parser = argparse.ArgumentParser(description="Perform basic arithmetic operations")
    parser.add_argument("--multiply", help="Multiply two numbers", type=int, nargs=2)
    args = parser.parse_args()
    
    # Instantiate a Calculator object and perform multiplication
    result = multiply(args.multiply[0], args.multiply[1])
    print(f"The result is: {result}")
