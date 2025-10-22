"""
Setup Script for arXiv Paper Agent

Handles initial setup, dependency installation, and configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any


class SetupManager:
    """Manages the setup process for the paper agent."""
    
    def __init__(self):
        """Initialize the setup manager."""
        self.project_root = Path(__file__).parent
        self.required_dirs = ["logs", "data", "config"]
        self.required_files = [
            "requirements.txt",
            "env.example",
            "main.py",
            "config.py"
        ]
    
    def run_setup(self) -> bool:
        """
        Run the complete setup process.
        
        Returns:
            True if setup was successful
        """
        print("🚀 Setting up arXiv Paper Agent...")
        
        try:
            # Check Python version
            if not self._check_python_version():
                return False
            
            # Create required directories
            if not self._create_directories():
                return False
            
            # Install dependencies
            if not self._install_dependencies():
                return False
            
            # Setup environment file
            if not self._setup_environment():
                return False
            
            # Validate setup
            if not self._validate_setup():
                return False
            
            print("✅ Setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Copy env.example to .env and configure your API keys")
            print("2. Set up your Notion integration and database")
            print("3. Run: python main.py --mode manual --days 7")
            print("4. Run: python main.py --mode scheduled")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def _check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        print("🐍 Checking Python version...")
        
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False
        
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        return True
    
    def _create_directories(self) -> bool:
        """Create required directories."""
        print("📁 Creating directories...")
        
        try:
            for dir_name in self.required_dirs:
                dir_path = self.project_root / dir_name
                dir_path.mkdir(exist_ok=True)
                print(f"  ✅ Created {dir_name}/")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            return False
    
    def _install_dependencies(self) -> bool:
        """Install Python dependencies."""
        print("📦 Installing dependencies...")
        
        try:
            requirements_file = self.project_root / "requirements.txt"
            
            if not requirements_file.exists():
                print("❌ requirements.txt not found")
                return False
            
            # Install dependencies
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error installing dependencies: {result.stderr}")
                return False
            
            print("✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def _setup_environment(self) -> bool:
        """Setup environment configuration."""
        print("⚙️ Setting up environment...")
        
        try:
            env_example = self.project_root / "env.example"
            env_file = self.project_root / ".env"
            
            if not env_example.exists():
                print("❌ env.example not found")
                return False
            
            # Copy example to .env if it doesn't exist
            if not env_file.exists():
                shutil.copy2(env_example, env_file)
                print("✅ Created .env file from template")
            else:
                print("ℹ️ .env file already exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up environment: {e}")
            return False
    
    def _validate_setup(self) -> bool:
        """Validate the setup."""
        print("🔍 Validating setup...")
        
        try:
            # Check required files
            for file_name in self.required_files:
                file_path = self.project_root / file_name
                if not file_path.exists():
                    print(f"❌ Required file missing: {file_name}")
                    return False
            
            # Check directories
            for dir_name in self.required_dirs:
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    print(f"❌ Required directory missing: {dir_name}")
                    return False
            
            # Test imports
            try:
                import requests
                import google.generativeai
                import notion_client
                print("✅ All required packages are available")
            except ImportError as e:
                print(f"❌ Missing package: {e}")
                return False
            
            print("✅ Setup validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def create_notion_database_instructions(self) -> str:
        """Generate instructions for setting up Notion database."""
        return """
📋 Notion Database Setup Instructions:

1. Create a new Notion page or use an existing one
2. Add a new database to the page
3. Configure the database with these properties:

   Required Properties:
   - Title (Title)
   - Authors (Text)
   - Abstract (Text)
   - ArXiv ID (Text)
   - Published Date (Date)
   - Categories (Multi-select)
   - ArXiv URL (URL)
   - Tags (Multi-select)
   - Relevance Score (Number)
   - Key Insights (Text)
   - Methodology (Text)
   - Limitations (Text)
   - Status (Select: New, Reviewed, Rejected)

4. Create a Notion integration:
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "arXiv Paper Agent")
   - Select the workspace
   - Copy the "Internal Integration Token"

5. Share the database with your integration:
   - Open your database
   - Click "Share" in the top right
   - Add your integration by name
   - Give it "Can edit" permissions

6. Get the database ID:
   - Open your database in a web browser
   - Copy the URL: https://notion.so/[workspace]/[database_id]?v=[view_id]
   - The database_id is the 32-character string between the last slash and the question mark

7. Update your .env file with:
   - NOTION_API_KEY=your_integration_token
   - NOTION_DATABASE_ID=your_database_id
        """
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test the current configuration."""
        print("🧪 Testing configuration...")
        
        results = {
            "environment_file": False,
            "api_keys": False,
            "notion_connection": False,
            "gemini_connection": False
        }
        
        try:
            # Check .env file
            env_file = self.project_root / ".env"
            if env_file.exists():
                results["environment_file"] = True
                print("✅ Environment file found")
            else:
                print("❌ Environment file not found")
                return results
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check API keys
            google_key = os.getenv("GOOGLE_API_KEY")
            notion_key = os.getenv("NOTION_API_KEY")
            notion_db = os.getenv("NOTION_DATABASE_ID")
            
            if google_key and notion_key and notion_db:
                results["api_keys"] = True
                print("✅ API keys configured")
            else:
                print("❌ Missing API keys in .env file")
                return results
            
            # Test Google Gemini connection
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                # Simple test call
                response = model.generate_content("Hello")
                results["gemini_connection"] = True
                print("✅ Google Gemini connection successful")
            except Exception as e:
                print(f"❌ Google Gemini connection failed: {e}")
            
            # Test Notion connection
            try:
                from notion_client import Client
                client = Client(auth=notion_key)
                # Try to retrieve database info
                db_info = client.databases.retrieve(database_id=notion_db)
                results["notion_connection"] = True
                print("✅ Notion connection successful")
            except Exception as e:
                print(f"❌ Notion connection failed: {e}")
            
            return results
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            return results


def main():
    """Main setup function."""
    setup_manager = SetupManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test configuration
        results = setup_manager.test_configuration()
        
        print("\n📊 Configuration Test Results:")
        for test, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {test.replace('_', ' ').title()}")
        
        if all(results.values()):
            print("\n🎉 All tests passed! Your configuration is ready.")
        else:
            print("\n⚠️ Some tests failed. Please check your configuration.")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "notion":
        # Show Notion setup instructions
        print(setup_manager.create_notion_database_instructions())
    
    else:
        # Run full setup
        success = setup_manager.run_setup()
        
        if success:
            print("\n🎉 Setup completed successfully!")
            print("\nTo test your configuration, run:")
            print("  python setup.py test")
            print("\nFor Notion setup instructions, run:")
            print("  python setup.py notion")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)


if __name__ == "__main__":
    main()
