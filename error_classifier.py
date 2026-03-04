# error_classifier.py

def classify_error(error_message):
    """
    Analyzes the raw GCC error string and assigns a category.
    Returns: Category (str), Advice_Strategy (str)
    """
    msg = error_message.lower()

    # RULE BASE 1: SYNTAX ERRORS
    if "expected" in msg or "missing" in msg or "was not declared" in msg:
        return "Syntax Error", "Focus on C++ syntax rules (semicolons, braces, variable names)."

    # RULE BASE 2: LINKER ERRORS
    elif "undefined reference" in msg or "ld returned 1 exit status" in msg:
        return "Linker Error", "Explain that a function definition or library is missing."

    # RULE BASE 3: TYPE ERRORS
    elif "conversion" in msg or "cannot convert" in msg or "type" in msg:
        return "Type Mismatch", "Explain variable types (int vs string, pointers)."
        
    # RULE BASE 4: RUNTIME / TIMEOUT ERRORS
    elif "time limit exceeded" in msg or "infinite loop" in msg:
        return "Runtime Error (Infinite Loop)", "Explain why the loop never terminates. You MUST provide the corrected code by adding a proper exit condition (like a break statement or a finite loop counter)."

    # RULE BASE 5: SECURITY/WARNINGS
    elif "deprecated" in msg or "warning" in msg or "unsafe" in msg:
        return "Security Warning", "Explain why this function is dangerous and suggest a modern alternative."

    # DEFAULT
    else:
        return "General Error", "Analyze the provided code and error message. Explain exactly what went wrong and provide the corrected code."

def get_diagnostic_prompt(category, strategy, code, error):
    """
    Generates a highly-constrained system prompt. 
    Places the data FIRST and the command LAST to force immediate LLM execution.
    """
    return f"""Analyze the following C++ code and compiler error, then provide a secure fix.

--- BUGGY CODE ---
{code}

--- COMPILER ERROR ---
{error}

--- INSTRUCTIONS ---
Diagnosis Category: {category}
Teaching Strategy: {strategy}

You are a strict, automated C++ Compiler Assistant. You MUST NOT make conversation. Do not say "I am happy to help" or ask for the code. 
You must immediately fix the provided BUGGY CODE while keeping the original logic, variable names, and proper indentation.

You MUST format your response EXACTLY like this:

### EXPLANATION
(Explain exactly what went wrong and how you fixed it)

### SECURE FIXED CODE
```cpp
(Write the complete, corrected C++ code here)"""