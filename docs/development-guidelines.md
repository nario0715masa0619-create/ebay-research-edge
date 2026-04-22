# docs/development-guidelines.md

# Development Guidelines for eBay-Research-Edge

## Code Change and Creation Rules

### Rule: Document Function Specifications First

When creating new functions or modifying existing ones, follow this process:

#### Step 1: Add to Function Specification Document
Before writing any code, update \docs/function-specification.md\:

1. Add a section for the new function under the appropriate module
2. Include the following information:
   - **Function Name**: Clear, descriptive name
   - **Purpose**: What the function does
   - **Parameters**: 
     - Parameter name
     - Type annotation
     - Description
     - Default values (if any)
   - **Returns**: Type and description of return value
   - **Algorithm**: Step-by-step explanation of how it works
   - **Raises**: Exceptions that may be raised
   - **Example**: Usage example with expected output
   - **Notes**: Special considerations, TODOs, edge cases
   - **Global Variables**: Any module-level variables used

#### Step 2: Write Code with Docstring
When writing the actual code:

1. Use the function specification as a reference
2. Write comprehensive English docstring in the code (using """ """ format)
3. The docstring should closely mirror the specification document
4. Use proper type hints (PEP 484)

#### Step 3: Keep Specification and Code in Sync
- If you change code logic, update docs/function-specification.md
- If you add new global variables, update the specification
- Use docs/function-specification.md as the source of truth

### Format for Function Specification (in docs/function-specification.md)

\\\markdown
### Module: module_name.py

#### Function: function_name()

**Purpose**: One-line description of what it does

**Parameters**:
- \param_name\ (type): Description. Default: value.

**Returns**:
- type: Description of return value

**Algorithm**:
1. Step one
2. Step two
3. Step three

**Raises**:
- ExceptionType: When this exception occurs

**Example**:
\\\python
>>> result = function_name(arg1, arg2)
>>> print(result)
expected_output
\\\

**Notes**:
- Important consideration 1
- TODO: Implementation item
- Edge case handling

**Global Variables Used**:
- \config\ (Config): For accessing settings
\\\

### Format for Code Docstring

\\\python
def function_name(param1: str, param2: int = 10) -> Dict[str, Any]:
    \"\"\"
    One-line summary of what the function does.
    
    Longer description explaining the purpose and behavior,
    including any important context or caveats.
    
    Args:
        param1 (str): Description of param1.
        param2 (int, optional): Description of param2. Defaults to 10.
    
    Returns:
        Dict[str, Any]: Description of return value and keys.
        
    Raises:
        ValueError: When param1 is empty.
        TypeError: When param2 is not an integer.
    
    Example:
        >>> result = function_name("test", 5)
        >>> print(result)
        {'status': 'ok', 'count': 5}
    
    Notes:
        - Important implementation detail
        - Edge case consideration
    
    Global Variables:
        config (Config): Accessed for configuration values.
    \"\"\"
    # Implementation here
    pass
\\\

## Workflow Example

### Adding a new function to analyzer.py

1. **Update docs/function-specification.md**:
   - Add section under "3. analyzer.py"
   - Write full specification including algorithm and examples

2. **Write code in src/analyzer/analyzer.py**:
   - Copy specification structure into docstring
   - Implement the function with proper type hints
   - Test implementation

3. **Commit**:
   - Commit message should reference both specification and code
   - Example: \git commit -m "Implement calculate_demand_score() with specification"\

4. **If specifications change later**:
   - Update docs/function-specification.md
   - Update code docstring
   - Both must stay in sync

## Type Hints (PEP 484)

Always use type hints:

\\\python
# Good
def calculate_score(records: List[MarketRecord], threshold: float = 0.5) -> float:
    pass

# Bad
def calculate_score(records, threshold=0.5):
    pass
\\\

## Global Variables

For any module-level variables (logger, config, etc.):

1. Document in the module docstring
2. Document in function-specification.md section "7. Global Variables"
3. Include when a function uses them in its docstring

Example:

\\\python
\"\"\"
Analysis module for metric calculation.

Global Variables:
    logger (logging.Logger): Module logger for this component.
    config (Config): Global config object for settings access.
\"\"\"

logger = logging.getLogger(__name__)
config = config  # Imported from config.py
\\\

## Documentation Update Checklist

- [ ] Updated docs/function-specification.md with full function spec
- [ ] Added comprehensive docstring to code
- [ ] Included type hints for all parameters and returns
- [ ] Added examples in both specification and docstring
- [ ] Listed any global variables used
- [ ] Updated if any existing specs changed
- [ ] All docstrings are in English

## Review Process

Before committing:

1. Check that specification document is complete
2. Check that code docstring matches specification
3. Verify type hints are present
4. Verify example works as documented
5. Ensure global variables are documented

## Tools to Help

- Use IDE docstring generators (Ctrl+/ in most editors)
- Validate docstring format with pydoc
- Keep docs/function-specification.md open alongside code

---

**Last Updated**: 2026-04-22
**Status**: Active (enforced from Phase 1 implementation onwards)
