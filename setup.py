import os
import subprocess
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import virtualenv
from pyngrok import ngrok, conf

console = Console()

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def create_virtual_environment():
    with console.status("[bold green]Creating virtual environment...") as status:
        if os.path.exists("venv"):
            console.print("[yellow]Virtual environment already exists[/yellow]")
            return True
        
        try:
            virtualenv.cli_run(["venv"])
            console.print("[green]✓[/green] Virtual environment created successfully")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to create virtual environment: {str(e)}[/red]")
            return False

def install_requirements():
    with console.status("[bold green]Installing requirements...") as status:
        pip_cmd = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
        if run_command(f"{pip_cmd} install -r requirements.txt"):
            console.print("[green]✓[/green] Requirements installed successfully")
            return True
        else:
            console.print("[red]✗ Failed to install requirements[/red]")
            return False

def setup_ngrok():
    config_file = "ngrok_config.json"
    
    # Check if config exists
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            try:
                ngrok.set_auth_token(config['auth_token'])
                # Verify token
                try:
                    ngrok.get_tunnels()
                    console.print("[green]✓[/green] Ngrok authentication successful")
                    return True
                except Exception:
                    console.print("[yellow]Existing ngrok token is invalid[/yellow]")
            except Exception:
                console.print("[yellow]Failed to load existing ngrok configuration[/yellow]")
    
    # Ask for new token
    while True:
        auth_token = console.input("[bold yellow]Please enter your ngrok auth token: [/bold yellow]")
        try:
            ngrok.set_auth_token(auth_token)
            # Verify token
            ngrok.get_tunnels()
            # Save token
            with open(config_file, 'w') as f:
                json.dump({'auth_token': auth_token}, f)
            console.print("[green]✓[/green] Ngrok authentication successful")
            return True
        except Exception as e:
            console.print(f"[red]✗ Invalid auth token. Please try again. Error: {str(e)}[/red]")

def main():
    console.print(Panel.fit(
        "[bold blue]Website Cloner Setup[/bold blue]\n"
        "[cyan]This script will set up your environment and configure ngrok[/cyan]",
        border_style="blue"
    ))
    
    # Create virtual environment
    if not create_virtual_environment():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Setup ngrok
    if not setup_ngrok():
        return
    
    console.print("\n[bold green]Setup completed successfully![/bold green]")
    console.print("\nTo start the tool, run:")
    if sys.platform == "win32":
        console.print("[bold]venv\\Scripts\\python website_cloner.py[/bold]")
    else:
        console.print("[bold]venv/bin/python website_cloner.py[/bold]")

if __name__ == "__main__":
    main() 