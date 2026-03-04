import subprocess
import os

def compile_and_run(cpp_code):
    """
    Takes C++ code string, saves it, compiles it, and returns the output or error.
    """
    # We create these temporary files inside the current folder
    source_file = "temp_source.cpp"
    executable = "temp_program"

    # 1. Write the C++ code to a file
    with open(source_file, "w") as f:
        f.write(cpp_code)

    try:
        # 2. Run the Compiler (g++)
        # Command: g++ temp_source.cpp -o temp_program
        process = subprocess.run(
            ["g++", source_file, "-o", executable], 
            capture_output=True,
            text=True
        )

        # 3. Check for Errors
        if process.returncode != 0:
            return f"Compilation Error:\n{process.stderr}"
        else:
            return "✅ Compilation Successful! (Binary generated)"

    except Exception as e:
        return f"System Error: {str(e)}"

# Test
if __name__ == "__main__":
    # This code is missing a semicolon on purpose to test the error catcher
    broken_code = """
    #include <iostream>
    using namespace std;
    int main() {
        cout << "Hello World"
        return 0;
    }
    """
    print(compile_and_run(broken_code))