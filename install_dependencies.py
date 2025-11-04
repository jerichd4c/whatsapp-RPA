import subprocess
import sys
import os

def run_command(command: str) -> bool:
    """Run a shell command and print it; return True on success, False on failure."""
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(command)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando {command}: {e.stderr}")
        return False

def install_requirements() -> None:
    """Install dependencies from requirements.txt if present; fallback to a basic list."""
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print("\nInstalando dependencias desde requirements.txt...")
        run_command(f"{sys.executable} -m pip install -r {req_file}")
    else:
        print("\nrequirements.txt no encontrado. Instalando lista básica de dependencias...")
        dependencies = [
            "pandas==1.5.3",
            # use >=3.1.0 for compatibility with pandas when reading Excel files
            "openpyxl>=3.1.0",
            "matplotlib==3.6.2",
            "twilio==7.16.0",
            "fpdf2==2.7.4",
            "python-dotenv==0.21.0",
            "requests==2.28.2",
            "schedule==1.2.0",
        ]
        for dep in dependencies:
            run_command(f"{sys.executable} -m pip install {dep}")

def main():
    print("Instalando dependencias...")
    print("=" * 50)

    # update pip first
    print("\nActualizando pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")

    # install dependencies from requirements.txt (preferred)
    install_requirements()

    # Selenium/ChromeDriver no longer required.

    print("\nInstalación de dependencias completada.")

if __name__ == "__main__":
    main()