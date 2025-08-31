#!/usr/bin/env python3
"""
Setup Script for Automated Math Solver
FOR TESTING PURPOSES ONLY

This script helps set up the environment and verify all dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version}")
        return True


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract OCR: {version}")
            return True
        else:
            print("❌ Tesseract OCR not found")
            return False
    except FileNotFoundError:
        print("❌ Tesseract OCR not installed")
        print("Install with:")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        print("  Windows: Download from GitHub releases")
        return False


def create_directories():
    """Create necessary directories."""
    directories = [
        'logs',
        'temp_files',
        'docs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_environment_file():
    """Set up environment file if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('env_example.txt')
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual credentials")
        return True
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ Could not create .env file")
        return False


def check_virtual_environment():
    """Check if running in virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
        return True
    else:
        print("⚠️  Not running in virtual environment")
        print("Recommended: python -m venv math_solver_venv && source math_solver_venv/bin/activate")
        return False


def install_dependencies():
    """Install Python dependencies."""
    try:
        print("📦 Installing Python dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print("❌ Error installing dependencies:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def verify_imports():
    """Verify that all required modules can be imported."""
    required_modules = [
        'flask',
        'flask_cors',
        'loguru',
        'github',
        'sympy',
        'numpy',
        'PIL',
        'pytesseract',
        'PyPDF2',
        'pdfplumber',
        'nltk',
        'spacy',
        'beautifulsoup4',
        'lxml',
        'schedule',
        'apscheduler',
        'email_validator',
        'python_dotenv',
        'yaml',
        'watchdog',
        'pytest',
        'py_expression_eval',
        'mpmath'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ All required modules imported successfully")
        return True


def test_configuration():
    """Test configuration loading."""
    try:
        from backend.utils.config_manager import ConfigManager
        config_manager = ConfigManager('config.yaml')
        config = config_manager.get_config()
        print("✅ Configuration loaded successfully")
        
        # Check GitHub repository
        repo = config['github']['repository']
        if repo == "TheEMeraldNetwork/Compiti-test":
            print(f"✅ GitHub repository: {repo}")
        else:
            print(f"⚠️  GitHub repository: {repo}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def main():
    """Main setup function."""
    print("🔧 Automated Math Solver Setup")
    print("=" * 40)
    print("FOR TESTING PURPOSES ONLY")
    print("=" * 40)
    
    checks = []
    
    # Run all checks
    print("\n📋 System Requirements:")
    checks.append(check_python_version())
    checks.append(check_tesseract())
    check_virtual_environment()  # Warning only
    
    print("\n📁 Directory Setup:")
    create_directories()
    
    print("\n⚙️ Environment Configuration:")
    checks.append(setup_environment_file())
    
    print("\n📦 Dependencies:")
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        checks.append(False)
    else:
        checks.append(install_dependencies())
    
    print("\n🔍 Import Verification:")
    checks.append(verify_imports())
    
    print("\n⚙️ Configuration Test:")
    checks.append(test_configuration())
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Setup Summary:")
    
    if all(checks):
        print("✅ Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Edit .env file with your GitHub token and email credentials")
        print("2. Run: python app.py test --email --github")
        print("3. Start the system: python app.py start --web")
        print("4. Access web interface: http://localhost:5000")
        return True
    else:
        print("❌ Setup completed with errors")
        print("Please resolve the issues above before running the system")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
