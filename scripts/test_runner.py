#!/usr/bin/env python3
"""
Comprehensive test runner for the LangGraph WhatsApp Agent.
Run this script to test all components systematically.
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = project_root
        self.test_results: List[Tuple[str, bool, Optional[str]]] = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        if self.verbose or level in ["ERROR", "SUCCESS"]:
            icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "📝")
            print(f"{icon} {message}")
    
    def check_environment(self) -> bool:
        """Check if the environment is properly configured"""
        self.log("Checking environment configuration...", "INFO")
        
        # Required for LangGraph
        langgraph_url = os.getenv("LANGGRAPH_URL")
        if not langgraph_url:
            self.log("LANGGRAPH_URL not set. Using default: http://localhost:8123", "WARNING")
            os.environ["LANGGRAPH_URL"] = "http://localhost:8123"
        
        # Check if LangGraph server is running
        try:
            import requests
            response = requests.get(f"{os.getenv('LANGGRAPH_URL')}/health", timeout=5)
            if response.status_code == 200:
                self.log("LangGraph server is running", "SUCCESS")
                return True
        except Exception:
            pass
        
        self.log("LangGraph server not accessible. Some tests may fail.", "WARNING")
        self.log("Start your LangGraph server with: langgraph up", "INFO")
        return False
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        self.log("Checking dependencies...", "INFO")
        
        required_packages = [
            "langgraph_sdk",
            "fastapi", 
            "twilio",
            "requests"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            self.log(f"Missing packages: {missing}", "ERROR")
            self.log("Install with: pip install " + " ".join(missing), "INFO")
            return False
        
        self.log("All dependencies are installed", "SUCCESS")
        return True
    
    async def run_test_file(self, test_file: Path, description: str) -> bool:
        """Run a specific test file"""
        self.log(f"Running {description}...", "INFO")
        
        try:
            # Import and run the test
            spec = __import__(f"tests.{test_file.stem}", fromlist=["main"])
            if hasattr(spec, "main"):
                success = await spec.main()
                status = "PASSED" if success else "FAILED"
                self.log(f"{description}: {status}", "SUCCESS" if success else "ERROR")
                self.test_results.append((description, success, None))
                return success
            else:
                self.log(f"{description}: No main() function found", "ERROR")
                self.test_results.append((description, False, "No main() function"))
                return False
                
        except Exception as e:
            self.log(f"{description}: {str(e)}", "ERROR")
            self.test_results.append((description, False, str(e)))
            return False
    
    def run_pytest(self) -> bool:
        """Run pytest if available"""
        self.log("Checking for pytest...", "INFO")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("Pytest: PASSED", "SUCCESS")
                return True
            else:
                self.log(f"Pytest: FAILED\n{result.stdout}\n{result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Pytest: TIMEOUT", "ERROR")
            return False
        except FileNotFoundError:
            self.log("Pytest not available", "WARNING")
            return True  # Not required
    
    async def run_all_tests(self, test_types: List[str] = None) -> bool:
        """Run all tests"""
        self.log("🚀 Starting Comprehensive Test Suite", "INFO")
        self.log("=" * 60, "INFO")
        
        # Check prerequisites
        if not self.check_dependencies():
            return False
        
        server_running = self.check_environment()
        
        # Define available tests
        available_tests = {
            "direct": ("test_agent_direct", "Direct Agent Tests"),
            "whatsapp": ("test_whatsapp_agent", "WhatsApp Agent Tests"),
            "integration": ("test_whatsapp_integration", "Integration Tests")
        }
        
        # Determine which tests to run
        if test_types is None:
            test_types = list(available_tests.keys())
        
        # Run async tests
        overall_success = True
        for test_type in test_types:
            if test_type in available_tests:
                test_file, description = available_tests[test_type]
                test_path = self.project_root / "tests" / f"{test_file}.py"
                
                if test_path.exists():
                    success = await self.run_test_file(test_path, description)
                    overall_success = overall_success and success
                else:
                    self.log(f"Test file not found: {test_path}", "ERROR")
                    overall_success = False
        
        # Run pytest
        if "pytest" in test_types or test_types is None:
            pytest_success = self.run_pytest()
            overall_success = overall_success and pytest_success
        
        # Summary
        self.print_summary()
        
        return overall_success
    
    def print_summary(self):
        """Print test results summary"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("📊 TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success, error in self.test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            self.log(f"{test_name}: {status}", "SUCCESS" if success else "ERROR")
            if error and self.verbose:
                self.log(f"  Error: {error}", "ERROR")
            if success:
                passed += 1
        
        self.log(f"\nOverall: {passed}/{total} tests passed", "SUCCESS" if passed == total else "ERROR")
        
        if passed == total:
            self.log("🎉 All tests passed! Your agent is working correctly.", "SUCCESS")
        else:
            self.log("❌ Some tests failed. Check the logs above for details.", "ERROR")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test the LangGraph WhatsApp Agent")
    parser.add_argument(
        "--tests", 
        nargs="+", 
        choices=["direct", "whatsapp", "integration", "pytest"], 
        help="Specific tests to run"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--setup-env", 
        action="store_true", 
        help="Setup environment variables interactively"
    )
    
    args = parser.parse_args()
    
    # Setup environment if requested
    if args.setup_env:
        setup_environment()
    
    # Run tests
    runner = TestRunner(verbose=args.verbose)
    success = asyncio.run(runner.run_all_tests(args.tests))
    
    sys.exit(0 if success else 1)


def setup_environment():
    """Interactive environment setup"""
    print("🔧 Environment Setup")
    print("=" * 40)
    
    # LangGraph URL
    current_url = os.getenv("LANGGRAPH_URL", "http://localhost:8123")
    langgraph_url = input(f"LangGraph URL [{current_url}]: ").strip() or current_url
    os.environ["LANGGRAPH_URL"] = langgraph_url
    
    # Assistant ID
    current_assistant = os.getenv("LANGGRAPH_ASSISTANT_ID", "agent")
    assistant_id = input(f"Assistant ID [{current_assistant}]: ").strip() or current_assistant
    os.environ["LANGGRAPH_ASSISTANT_ID"] = assistant_id
    
    # Config
    current_config = os.getenv("CONFIG", "{}")
    config = input(f"Config JSON [{current_config}]: ").strip() or current_config
    os.environ["CONFIG"] = config
    
    print("✅ Environment configured!")


if __name__ == "__main__":
    main() 