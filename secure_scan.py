import re

def run_security_guardrail(code_snippet):
    """
    Scans the provided code/text for banned C++ functions using Regex.
    Returns: (is_safe: bool, warning_message: str)
    """
    
    # 'Never-List'(Regex patterns)
    banned_patterns = {
        r'gets\s*\(': "CRITICAL: The function 'gets()' is banned because it causes Buffer Overflows. Use 'fgets()' instead.",
        r'system\s*\("pause"\)': "WARNING: 'system(\"pause\")' is platform-dependent and resource heavy. Use 'cin.get()' instead.",
        r'strcpy\s*\(': "RISK: 'strcpy' does not check buffer size. Use 'strncpy' to prevent memory corruption.",
        r'void\s+main\s*\(': "STANDARD: 'void main()' is non-standard C++. Use 'int main()' and return 0."
    }

    # Check the code against patterns
    for pattern, warning in banned_patterns.items():
        if re.search(pattern, code_snippet):
            return False, warning 

    return True, "Code looks safe."