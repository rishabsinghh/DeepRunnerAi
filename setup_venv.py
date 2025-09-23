"""
Virtual Environment Setup Script for CLM Automation System
Creates and configures a virtual environment with all dependencies
"""
import os
import subprocess
import sys
import platform

def create_virtual_environment():
    """Create a virtual environment"""
    print("🔧 Creating virtual environment...")
    
    venv_name = "clm_env"
    
    if os.path.exists(venv_name):
        print(f"⚠️  Virtual environment '{venv_name}' already exists")
        response = input("Do you want to recreate it? (y/N): ").strip().lower()
        if response == 'y':
            print(f"🗑️  Removing existing virtual environment...")
            if platform.system() == "Windows":
                subprocess.run(f"rmdir /s /q {venv_name}", shell=True)
            else:
                subprocess.run(f"rm -rf {venv_name}", shell=True)
        else:
            print("✅ Using existing virtual environment")
            return venv_name
    
    try:
        subprocess.check_call([sys.executable, "-m", "venv", venv_name])
        print(f"✅ Virtual environment '{venv_name}' created successfully")
        return venv_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        return None

def get_activation_command(venv_name):
    """Get the activation command based on the operating system"""
    if platform.system() == "Windows":
        return f"{venv_name}\\Scripts\\activate"
    else:
        return f"source {venv_name}/bin/activate"

def install_packages(venv_name):
    """Install packages in the virtual environment"""
    print("📦 Installing packages...")
    
    # Get the Python executable in the virtual environment
    if platform.system() == "Windows":
        python_exe = f"{venv_name}\\Scripts\\python.exe"
        pip_exe = f"{venv_name}\\Scripts\\pip.exe"
    else:
        python_exe = f"{venv_name}/bin/python"
        pip_exe = f"{venv_name}/bin/pip"
    
    try:
        # Upgrade pip
        print("⬆️  Upgrading pip...")
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install core packages
        print("📦 Installing core packages...")
        subprocess.check_call([pip_exe, "install", "-r", "requirements_simple.txt"])
        
        # Install AI/ML packages
        print("🤖 Installing AI/ML packages...")
        ai_packages = [
            "langchain",
            "langchain-community", 
            "langchain-openai",
            "openai",
            "chromadb"
        ]
        subprocess.check_call([pip_exe, "install"] + ai_packages)
        
        print("✅ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def create_activation_scripts(venv_name):
    """Create convenient activation scripts"""
    print("📝 Creating activation scripts...")
    
    activation_cmd = get_activation_command(venv_name)
    
    # Windows batch file
    with open("activate_env.bat", "w") as f:
        f.write(f"@echo off\n")
        f.write(f"echo Activating CLM Environment...\n")
        f.write(f"call {activation_cmd}\n")
        f.write(f"echo Environment activated! You can now run:\n")
        f.write(f"echo   python main.py --mode chatbot\n")
        f.write(f"echo   python demo.py\n")
        f.write(f"echo   streamlit run chatbot_interface.py\n")
    
    # Unix shell script
    with open("activate_env.sh", "w") as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"echo 'Activating CLM Environment...'\n")
        f.write(f"{activation_cmd}\n")
        f.write(f"echo 'Environment activated! You can now run:'\n")
        f.write(f"echo '  python main.py --mode chatbot'\n")
        f.write(f"echo '  python demo.py'\n")
        f.write(f"echo '  streamlit run chatbot_interface.py'\n")
    
    # Make shell script executable on Unix
    if platform.system() != "Windows":
        os.chmod("activate_env.sh", 0o755)
    
    print("✅ Activation scripts created")

def test_installation(venv_name):
    """Test the installation"""
    print("🧪 Testing installation...")
    
    if platform.system() == "Windows":
        python_exe = f"{venv_name}\\Scripts\\python.exe"
    else:
        python_exe = f"{venv_name}/bin/python"
    
    try:
        # Test basic imports
        subprocess.check_call([python_exe, "-c", "import streamlit, pandas, numpy, chromadb, langchain; print('✅ All packages imported successfully')"])
        
        # Test the system
        subprocess.check_call([python_exe, "test_system.py"])
        
        print("✅ Installation test passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation test failed: {e}")
        return False

def create_usage_guide():
    """Create a usage guide"""
    print("📚 Creating usage guide...")
    
    guide_content = """# CLM Automation System - Virtual Environment Usage

## 🚀 Quick Start

### Activate the Environment

**Windows:**
```cmd
activate_env.bat
```

**Linux/Mac:**
```bash
source activate_env.sh
```

### Run the System

1. **Web Interface:**
   ```bash
   streamlit run chatbot_interface.py
   ```
   Then open http://localhost:8501

2. **Demo:**
   ```bash
   python demo.py
   ```

3. **Test System:**
   ```bash
   python test_system.py
   ```

4. **Command Line:**
   ```bash
   python main.py --mode chatbot
   python main.py --mode question --question "What contracts are expiring?"
   python main.py --mode similarity --query "contract expiration"
   ```

## 📁 Project Structure

```
clm-automation-system/
├── clm_env/                 # Virtual environment
├── documents/               # Contract documents
├── main.py                 # Main application
├── chatbot_interface.py    # Web interface
├── demo.py                 # Demonstration
├── test_system.py          # System tests
├── activate_env.bat        # Windows activation
├── activate_env.sh         # Unix activation
└── .env                    # Environment config
```

## 🔧 Configuration

Edit `.env` file to configure:
- OpenAI API key
- Email settings
- Database settings

## 🆘 Troubleshooting

1. **Activation issues:** Make sure you're in the project directory
2. **Package errors:** Re-run `python setup_venv.py`
3. **Port conflicts:** Change port in streamlit command
4. **API errors:** Check your `.env` configuration

## 📞 Support

Check the logs in `clm_system_*.log` for detailed error information.
"""
    
    with open("VENV_USAGE.md", "w") as f:
        f.write(guide_content)
    
    print("✅ Usage guide created")

def main():
    """Main setup function"""
    print("🚀 CLM Automation System - Virtual Environment Setup")
    print("=" * 60)
    
    # Step 1: Create virtual environment
    venv_name = create_virtual_environment()
    if not venv_name:
        print("❌ Setup failed at virtual environment creation")
        return False
    
    # Step 2: Install packages
    if not install_packages(venv_name):
        print("❌ Setup failed at package installation")
        return False
    
    # Step 3: Create activation scripts
    create_activation_scripts(venv_name)
    
    # Step 4: Test installation
    if not test_installation(venv_name):
        print("❌ Setup failed at installation test")
        return False
    
    # Step 5: Create usage guide
    create_usage_guide()
    
    print("\n🎉 Virtual Environment Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Activate the environment:")
    if platform.system() == "Windows":
        print("   activate_env.bat")
    else:
        print("   source activate_env.sh")
    print("\n2. Start the web interface:")
    print("   streamlit run chatbot_interface.py")
    print("\n3. Or run the demo:")
    print("   python demo.py")
    print("\n4. Configure your settings in .env file")
    print("\n📚 See VENV_USAGE.md for detailed instructions")
    
    return True

if __name__ == "__main__":
    main()
