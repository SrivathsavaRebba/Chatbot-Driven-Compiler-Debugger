import streamlit as st
import subprocess
import requests
import os
from fix_engine import validate_ai_fix
from secure_scan import run_security_guardrail
from error_logger import log_error
from error_classifier import classify_error, get_diagnostic_prompt

# LLM config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

#FUNCTION : CALLING LOCAL LLAMA 3
def get_ai_explanation(prompt):
    """Sends the error/code to the local Ollama Llama 3 model."""
    payload ={
        "model":MODEL_NAME,
        "prompt":prompt,
        "stream":False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        if response.status_code ==200:
            return response.json()['response']
        else:
            return f"Error connecting to Ollama: {response.status_code}"
    except Exception as e:
        return f"Connection Failed. Is Ollama running? Error:{str(e)}"

#FUNCTION : COMPILE & RUN C++ CODE with kill switch
def compile_code(cpp_code):
    """Saves code, compiles it, runs it with a timeout, and cleans up."""
    file_name = "temp_code.cpp"
    binary_name = "./output_binary"
    
    #1. Save User Code
    with open(file_name, "w") as f:
        f.write(cpp_code)
    
    try:
        #2. COMPILE(Limit to 10 seconds)
        compile_result = subprocess.run(
            ["g++", file_name, "-o", "output_binary"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        #If compilation failed, return the compiler error
        if compile_result.returncode != 0:
            return compile_result.returncode, "", compile_result.stderr

        #3. RUN(The Kill Switch-Limit to 5 seconds)
        run_result = subprocess.run(
            [binary_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Return Success and the actual Output 
        return 0, run_result.stdout, ""

    except subprocess.TimeoutExpired:
        return -1, "", "❌ ERROR: Time Limit Exceeded! Your code might have an infinite loop (e.g., while(true))."
    except Exception as e:
        return -1, "", f"❌ System Error: {str(e)}"
    finally:
        # Cleanup: Remove temp files to keep folder clean
        if os.path.exists(file_name): os.remove(file_name)
        if os.path.exists("output_binary"): os.remove("output_binary")

#UI
st.set_page_config(page_title="AI C++ Debugger", layout="wide")

st.title("Chatbot-Driven C++ Compiler & Debugger")
st.markdown("### Secure Coding Assistant running on Local LLM")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 C++ Code Editor")
    default_code = """#include <iostream>
using namespace std;

int main() {
    while(true){
        cout << "Hello, Server!" << endl;
    }

    return 0;
}"""
    user_code = st.text_area("Write your C++ code here:", value=default_code, height=400)
    
    if st.button("Compile & Analyze"):
        if not user_code.strip():
            st.warning("Please write some code first!")
        else:
            is_safe, warning_msg = run_security_guardrail(user_code)
            
            if not is_safe:
                # Stop everything immediately!
                st.session_state['compile_status'] = -1 
                st.session_state['logs'] = f"🚫 SECURITY BLOCK: {warning_msg}"
                st.session_state['user_code'] = user_code
                st.rerun() # Refresh to show the error
            
            # Only compile if safe
            with st.spinner("Compiling..."):
                return_code, stdout, stderr = compile_code(user_code)
            # Store results
            st.session_state['compile_status'] = return_code
            st.session_state['output'] = stdout
            st.session_state['errors'] = stderr
            st.session_state['user_code'] = user_code

with col2:
    st.subheader("AI & Security Feedback")
    
    # Check if we have results in the session state
    if 'compile_status' in st.session_state:
        status = st.session_state['compile_status']
        
        # FIX: Use 'errors' instead of 'logs' 
        errors = st.session_state['errors']  
        output = st.session_state['output']
        code_to_analyze = st.session_state['user_code']


    # PATH A: COMPILATION ERROR 
        if status != 0:
            st.error("❌ Execution Failed!")
            
            # 1. Log the error to CSV (Week 6)
            if errors:
                log_error(errors, code_to_analyze)
                st.code(errors, language="text")
            
            # 2. Classify the Error (Week 7)
            with st.spinner("🤖 Diagnosing Error..."):
                category, strategy = classify_error(errors)
                st.info(f" **---> Detected Error Category:** {category}")
            
            st.info(" Asking LLM for a secure fix...")
            
            # 3. Generate Dynamic Prompt & Get AI Explanation
            prompt = get_diagnostic_prompt(category, strategy, code_to_analyze, errors)
            explanation = get_ai_explanation(prompt)
            
            # WEEK 8: SECURE FIX SUGGESTION MODULE
            st.markdown("### AI Diagnostic Report")
            st.write(explanation) # Printing explanation

            # 4. Validate the AI's generated code!
            is_fix_safe, suggested_code, security_status = validate_ai_fix(explanation)
            
            st.markdown("### Secure Code Validation")
            if is_fix_safe:
                st.success("✅ " + security_status)
                # Deliverable: Sample corrected code output!
                with st.expander("View Verified & Corrected Code"):
                    st.code(suggested_code, language="cpp")
            else:
                # If the AI hallucinates bad code, block it!
                if suggested_code:
                    st.error("🚫 AI generated insecure code! " + security_status)
                    st.warning("The AI's code has been blocked from direct copy-pasting to protect your system.")
                else:
                    st.warning("⚠️ " + security_status)

        # PATH B: SUCCESS 
        else:
            st.success("✅ Execution Successful!")
            st.markdown("**Output:**")
            st.code(output, language="text")
            
            st.info("🔍 Running Security Scan...")
            
            # 1. Regex Guardrail
            is_safe, warning_msg = run_security_guardrail(code_to_analyze)
            
            if not is_safe:
                st.error(f"🚫 SECURITY BLOCK: {warning_msg}")
            else:
                st.markdown("✅ **Guardrail Passed.** Checking Logic...")
                
                # 2. Logic Check
                prompt = f"""
                Review this C++ code for logical flaws.
                CODE:
                {code_to_analyze}
                """
                ai_feedback = get_ai_explanation(prompt)
                st.write(ai_feedback)