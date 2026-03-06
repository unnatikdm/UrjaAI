"""
Real Data Integration Setup Script
Configures and starts all real data services for the recommendation system
"""

import os
import sys
import subprocess
import asyncio
import time
import logging
from pathlib import Path

def setup_environment():
    """Setup environment for real data integration"""
    
    print("Setting up Real Data Integration Environment...")
    print("=" * 60)
    
    # Create necessary directories
    directories = [
        "data",
        "knowledge_base", 
        "weather_cache",
        "models",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create environment configuration
    env_config = """# Real Data Integration Configuration

# API Servers
BOSCH_API_URL=http://localhost:8002
MODEL_API_URL=http://localhost:8003
WEATHER_API_URL=https://archive-api.open-meteo.com/v1

# Database Configuration (optional)
DATABASE_URL=sqlite:///./recommendations.db

# Cache Settings
WEATHER_CACHE_DURATION=3600
KNOWLEDGE_BASE_CACHE_DURATION=86400

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/real_integration.log

# Real Data Sources
USE_REAL_DATA=true
BOSCH_DATA_PATH=../browniepoint2/data
WEATHER_PROVIDER=open-meteo
MODEL_PROVIDER=xgboost

# API Keys (if needed)
OPENWEATHER_API_KEY=your_openweather_key_here
BOSCH_API_KEY=your_bosch_api_key_here
"""
    
    env_file = Path(".env.real")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_config)
        print("Created .env.real configuration file")
    else:
        print(".env.real file already exists")
    
    # Update requirements for real data
    real_requirements = """
# Real Data Integration Requirements
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.0
aiohttp>=3.8.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0

# Weather Service
requests>=2.31.0

# Model and SHAP
xgboost>=1.7.0
shap>=0.41.0
joblib>=1.3.0

# Data Processing
pyarrow>=10.0.0
openpyxl>=3.1.0

# Database (optional)
sqlalchemy>=2.0.0
sqlite3

# Caching
diskcache>=5.6.0

# Utilities
python-dotenv>=1.0.0
asyncio
uuid
"""
    
    req_file = Path("requirements_real.txt")
    with open(req_file, 'w') as f:
        f.write(real_requirements)
    print("✅ Created requirements_real.txt")

def install_real_dependencies():
    """Install dependencies for real data integration"""
    
    print("\n📦 Installing Real Data Dependencies...")
    
    requirements = [
        "aiohttp>=3.8.0",
        "requests>=2.31.0",
        "shap>=0.41.0",
        "pyarrow>=10.0.0",
        "diskcache>=5.6.0"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")

def start_bosch_api():
    """Start Bosch data API server"""
    
    print("\n🚀 Starting Bosch Data API Server...")
    
    try:
        # Start in background
        import subprocess
        import threading
        
        def run_bosch_api():
            subprocess.run([sys.executable, "bosch_api.py"])
        
        bosch_thread = threading.Thread(target=run_bosch_api, daemon=True)
        bosch_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        print("✅ Bosch API Server started on http://localhost:8002")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Bosch API: {e}")
        return False

def start_model_api():
    """Start Model API server"""
    
    print("\n🧠 Starting Model API Server...")
    
    try:
        import subprocess
        import threading
        
        def run_model_api():
            subprocess.run([sys.executable, "model_api.py"])
        
        model_thread = threading.Thread(target=run_model_api, daemon=True)
        model_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        print("✅ Model API Server started on http://localhost:8003")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Model API: {e}")
        return False

async def build_real_knowledge_base():
    """Build knowledge base with real data"""
    
    print("\n📚 Building Real Knowledge Base...")
    
    try:
        from real_knowledge_base import RealDataKnowledgeBaseBuilder
        
        builder = RealDataKnowledgeBaseBuilder()
        documents = await builder.build_real_knowledge_base(
            start_date="2025-01-01",
            end_date="2025-07-20",
            buildings=['A', 'B', 'C']
        )
        
        print(f"✅ Knowledge base built with {len(documents)} documents")
        
        # Print summary
        doc_types = {}
        for doc in documents:
            doc_type = doc.get('type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print("📊 Knowledge Base Summary:")
        for doc_type, count in doc_types.items():
            print(f"  {doc_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to build knowledge base: {e}")
        return False

def start_real_integration_api():
    """Start main real integration API"""
    
    print("\n🌐 Starting Real Data Integration API...")
    
    try:
        import subprocess
        import threading
        
        def run_integration_api():
            subprocess.run([sys.executable, "real_data_api.py"])
        
        integration_thread = threading.Thread(target=run_integration_api, daemon=True)
        integration_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        print("✅ Real Integration API started on http://localhost:8004")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Integration API: {e}")
        return False

async def test_real_integration():
    """Test real data integration"""
    
    print("\n🧪 Testing Real Data Integration...")
    
    try:
        import aiohttp
        
        # Test Bosch API
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8002/health") as response:
                if response.status == 200:
                    print("✅ Bosch API: Healthy")
                else:
                    print("❌ Bosch API: Unhealthy")
        
        # Test Model API
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8003/health") as response:
                if response.status == 200:
                    print("✅ Model API: Healthy")
                else:
                    print("❌ Model API: Unhealthy")
        
        # Test Integration API
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8004/api/v2/system/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Integration API: Healthy")
                    print(f"   Buildings: {status.get('total_buildings', 0)}")
                    print(f"   Documents: {status.get('total_documents', 0)}")
                    print(f"   Real Data: {status.get('real_data_available', False)}")
                else:
                    print("❌ Integration API: Unhealthy")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def create_startup_script():
    """Create startup script for easy deployment"""
    
    startup_script = """#!/bin/bash
# Real Data Integration Startup Script

echo "🚀 Starting Real Data Integration Services..."

# Start Bosch API
echo "Starting Bosch API Server..."
python bosch_api.py &
BOSCH_PID=$!

# Start Model API  
echo "Starting Model API Server..."
python model_api.py &
MODEL_PID=$!

# Wait for services to start
sleep 5

# Build Knowledge Base
echo "Building Real Knowledge Base..."
python -c "import asyncio; from real_knowledge_base import RealDataKnowledgeBaseBuilder; asyncio.run(RealDataKnowledgeBaseBuilder().build_real_knowledge_base())"

# Start Integration API
echo "Starting Real Integration API..."
python real_data_api.py &
INTEGRATION_PID=$!

echo "✅ All services started!"
echo "Bosch API: http://localhost:8002"
echo "Model API: http://localhost:8003" 
echo "Integration API: http://localhost:8004"
echo "API Docs: http://localhost:8004/docs"

# Save PIDs for cleanup
echo $BOSCH_PID > .bosch_pid
echo $MODEL_PID > .model_pid
echo $INTEGRATION_PID > .integration_pid

echo "To stop all services, run: ./stop_services.sh"
"""
    
    with open("start_real_services.sh", 'w') as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod("start_real_services.sh", 0o755)
    print("✅ Created start_real_services.sh")
    
    # Create stop script
    stop_script = """#!/bin/bash
# Stop Real Data Integration Services

echo "🛑 Stopping Real Data Integration Services..."

if [ -f .bosch_pid ]; then
    kill $(cat .bosch_pid) 2>/dev/null
    rm .bosch_pid
    echo "Stopped Bosch API"
fi

if [ -f .model_pid ]; then
    kill $(cat .model_pid) 2>/dev/null
    rm .model_pid
    echo "Stopped Model API"
fi

if [ -f .integration_pid ]; then
    kill $(cat .integration_pid) 2>/dev/null
    rm .integration_pid
    echo "Stopped Integration API"
fi

echo "✅ All services stopped!"
"""
    
    with open("stop_services.sh", 'w') as f:
        f.write(stop_script)
    
    os.chmod("stop_services.sh", 0o755)
    print("✅ Created stop_services.sh")

async def main():
    """Main setup function"""
    
    print("🎯 Real Data Integration Setup")
    print("=" * 60)
    print("This will configure your recommendation system to use real data sources:")
    print("• Bosch Energy Management API")
    print("• Open-Meteo Weather Service") 
    print("• Real XGBoost Model with SHAP")
    print("• Real Knowledge Base")
    print()
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    install_real_dependencies()
    
    # Start services
    print("\n🚀 Starting Real Data Services...")
    
    bosch_started = start_bosch_api()
    model_started = start_model_api()
    
    if bosch_started and model_started:
        # Build knowledge base
        kb_built = await build_real_knowledge_base()
        
        if kb_built:
            # Start integration API
            integration_started = start_real_integration_api()
            
            if integration_started:
                # Test integration
                await test_real_integration()
                
                # Create startup scripts
                create_startup_script()
                
                print("\n🎉 Real Data Integration Setup Complete!")
                print("\n📋 Services Running:")
                print("• Bosch API: http://localhost:8002")
                print("• Model API: http://localhost:8003")
                print("• Integration API: http://localhost:8004")
                print("\n📚 API Documentation:")
                print("• Integration API: http://localhost:8004/docs")
                print("• Bosch API: http://localhost:8002/docs")
                print("• Model API: http://localhost:8003/docs")
                print("\n🔧 Management:")
                print("• Start services: ./start_real_services.sh")
                print("• Stop services: ./stop_services.sh")
                print("• Rebuild knowledge base: curl http://localhost:8004/api/v2/knowledge-base/rebuild")
                
                return True
    
    print("\n❌ Setup failed. Please check the error messages above.")
    return False

if __name__ == "__main__":
    asyncio.run(main())
