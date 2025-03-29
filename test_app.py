import os
import sys
import time
import asyncio
import aiohttp
import subprocess
import signal
import json
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout
from rich import print as rprint

console = Console()

class AppTester:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_data = {
            "city": "Mumbai",
            "specialization": "cardiologist"
        }

    def check_environment(self) -> Dict[str, bool]:
        """Check if all required environment variables are set"""
        required_vars = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "FRONTEND_URL": os.getenv("FRONTEND_URL"),
            "PORT": os.getenv("PORT")
        }
        
        results = {}
        for var, value in required_vars.items():
            results[var] = bool(value)
        
        return results

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required Python packages are installed"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "python-dotenv",
            "google-generativeai",
            "pandas",
            "pydantic",
            "fuzzywuzzy",
            "python-Levenshtein",
            "aiohttp",
            "tenacity",
            "rich",
            "SQLAlchemy",
            "python-multipart"
        ]
        
        results = {}
        try:
            # Run pip list to get installed packages
            output = subprocess.check_output(["pip3", "list"], text=True).lower()
            for package in required_packages:
                results[package] = package.lower() in output
        except subprocess.CalledProcessError:
            for package in required_packages:
                results[package] = False
        
        return results

    def check_node_dependencies(self) -> Dict[str, bool]:
        """Check if all required Node.js packages are installed"""
        required_packages = [
            "next",
            "react",
            "react-dom",
            "framer-motion",
            "tailwindcss",
            "typescript"
        ]
        
        results = {}
        try:
            # Run npm list to get installed packages
            output = subprocess.check_output(["npm", "list"], cwd="doctor-search-ui", text=True)
            for package in required_packages:
                results[package] = package in output
        except subprocess.CalledProcessError:
            for package in required_packages:
                results[package] = False
        
        return results

    async def check_backend_health(self) -> Dict[str, bool]:
        """Check if the backend API is healthy"""
        results = {}
        try:
            async with aiohttp.ClientSession() as session:
                # Check root endpoint
                async with session.get(f"{self.backend_url}/") as response:
                    results["root_endpoint"] = response.status == 200
                
                # Check search endpoint
                async with session.post(
                    f"{self.backend_url}/api/search",
                    json=self.test_data
                ) as response:
                    results["search_endpoint"] = response.status == 200
        except Exception as e:
            results["error"] = str(e)
            results["status"] = False
        return results

    async def check_frontend_health(self) -> Dict[str, bool]:
        """Check if the frontend is healthy"""
        results = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url) as response:
                    results["frontend"] = response.status == 200
        except Exception as e:
            results["error"] = str(e)
            results["status"] = False
        return results

    def start_backend(self) -> bool:
        """Start the backend server"""
        try:
            self.backend_process = subprocess.Popen(
                ["python", "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Wait for server to start
            return True
        except Exception as e:
            console.print(f"[red]Error starting backend: {e}[/red]")
            return False

    def start_frontend(self) -> bool:
        """Start the frontend server"""
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd="doctor-search-ui",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(5)  # Wait for server to start
            return True
        except Exception as e:
            console.print(f"[red]Error starting frontend: {e}[/red]")
            return False

    def stop_servers(self):
        """Stop both backend and frontend servers"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()

    def display_results(self, results: Dict):
        """Display test results in a formatted table"""
        table = Table(title="Test Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        for component, status in results.items():
            if isinstance(status, bool):
                status_text = "✅" if status else "❌"
            else:
                status_text = str(status)
            table.add_row(component, status_text, "")

        console.print(table)

    async def run_tests(self):
        """Run all tests and display results"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            # Environment check
            env_task = progress.add_task("Checking environment variables...", total=1)
            env_results = self.check_environment()
            progress.update(env_task, completed=1)
            self.display_results(env_results)

            # Python dependencies check
            deps_task = progress.add_task("Checking Python dependencies...", total=1)
            deps_results = self.check_dependencies()
            progress.update(deps_task, completed=1)
            self.display_results(deps_results)

            # Node dependencies check
            node_task = progress.add_task("Checking Node.js dependencies...", total=1)
            node_results = self.check_node_dependencies()
            progress.update(node_task, completed=1)
            self.display_results(node_results)

            # Start servers
            backend_task = progress.add_task("Starting backend server...", total=1)
            backend_started = self.start_backend()
            progress.update(backend_task, completed=1)

            frontend_task = progress.add_task("Starting frontend server...", total=1)
            frontend_started = self.start_frontend()
            progress.update(frontend_task, completed=1)

            if backend_started and frontend_started:
                # Health checks
                health_task = progress.add_task("Performing health checks...", total=2)
                backend_health = await self.check_backend_health()
                progress.update(health_task, advance=1)
                frontend_health = await self.check_frontend_health()
                progress.update(health_task, advance=1)

                # Display health check results
                console.print("\n[bold]Backend Health Check:[/bold]")
                self.display_results(backend_health)
                console.print("\n[bold]Frontend Health Check:[/bold]")
                self.display_results(frontend_health)

                # Display any errors from the servers
                if self.backend_process:
                    backend_output = self.backend_process.stdout.read().decode()
                    if backend_output:
                        console.print("\n[bold]Backend Server Output:[/bold]")
                        console.print(Panel(backend_output, title="Backend Logs"))

                if self.frontend_process:
                    frontend_output = self.frontend_process.stdout.read().decode()
                    if frontend_output:
                        console.print("\n[bold]Frontend Server Output:[/bold]")
                        console.print(Panel(frontend_output, title="Frontend Logs"))

            # Stop servers
            self.stop_servers()

def main():
    tester = AppTester()
    asyncio.run(tester.run_tests())

if __name__ == "__main__":
    main() 