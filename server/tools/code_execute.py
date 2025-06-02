def codeexecuter(code:str) -> str:
    import subprocess
    with open("temp_script.py", "w") as f:
        f.write(code)
    try:
        result = subprocess.run(["python", "temp_script.py"], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error executing code: {str(e)}"
    
codeexecuter_description = "Execute Python code and return output, make sure it's run and go.. since the there is no way to interact with the code being run, just the output is shared, Ideally use this tool to test certain things or perform analysis on the code, not to run long running tasks or tasks that require user input, as it will not work as expected."