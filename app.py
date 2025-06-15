import yt_dlp
from rich import print
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel
import os
import time
import pyperclip
import requests
from PIL import Image
from io import BytesIO
import pyfiglet


def show_banner():
    banner = pyfiglet.figlet_format("YT8K Downloader")
    print(f"[bold cyan]{banner}[/bold cyan]")
    print("[bold magenta]by Shoaib Shaikh[/bold magenta]")
    print("[bold blue]github.com/shoaibbshaikhh[/bold blue]\n")

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def list_formats(formats):
    table = Table(title="Available Video Qualities")
    table.add_column("Index", style="cyan")
    table.add_column("Format ID", style="magenta")
    table.add_column("Resolution", style="green")
    table.add_column("Ext", style="yellow")

    indexed_formats = []
    index = 1

    for fmt in formats:
        if fmt.get('vcodec') != 'none' and fmt.get('acodec') == 'none':
            res = fmt.get('format_note') or fmt.get('height', 'Unknown')
            table.add_row(str(index), fmt['format_id'], str(res), fmt['ext'])
            indexed_formats.append(fmt)
            index += 1

    print(table)
    return indexed_formats

def wait_for_file_release(filepath, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(filepath, 'a'):
                return True
        except PermissionError:
            time.sleep(1)
    return False

def show_thumbnail(thumbnail_url):
    try:
        response = requests.get(thumbnail_url)
        image = Image.open(BytesIO(response.content))
        image.show()
    except Exception as e:
        print(f"[bold red]❌ Failed to show thumbnail:[/bold red] {e}")

def download_video(url, format_id, output_path, only_audio=False):
    if only_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                'nopostoverwrites': False,
            }],
            'postprocessor_args': ['-y'],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'keepvideo': True
        }
    else:
        ydl_opts = {
            'format': f"{format_id}+bestaudio/best",
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s')
        }

    with Progress() as progress:
        task = progress.add_task("[green]Downloading...", start=False)

        def hook(d):
            if d['status'] == 'downloading':
                if not progress.tasks[0].started:
                    progress.start_task(task)
                progress.update(task, completed=d.get('downloaded_bytes', 0), total=d.get('total_bytes', 1))
            elif d['status'] == 'finished':
                progress.update(task, completed=d.get('total_bytes', 1))
                if only_audio:
                    filepath = d['filename']
                    wait_for_file_release(filepath)
                    time.sleep(2)

        ydl_opts['progress_hooks'] = [hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

def main():
    show_banner()
    while True:
        print("[bold yellow]\n🎥 YouTube Video Downloader - 8K/4K + MP3 + Playlist Supported[/bold yellow]\n")
        mode = Prompt.ask("[bold cyan]📁 Select Mode[/bold cyan]", choices=["video", "mp3", "playlist", "exit"])

        if mode == "exit":
            print("[bold red]👋 Exiting the tool. Goodbye![/bold red]")
            break

        url = Prompt.ask("🔗 Enter YouTube URL (or press Enter to use clipboard)", default="").strip()
        if not url:
            url = pyperclip.paste().strip()
            print(f"[bold green]📋 URL fetched from clipboard:[/bold green] {url}")

        output_path = Prompt.ask("📂 Enter path to save downloads", default="")
        if not output_path.strip():
            output_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(output_path, exist_ok=True)
            print(f"[bold green]📂 Auto-created download folder:[/bold green] {output_path}")

        if mode == "mp3":
            print("\n🎵 [bold green]Extracting MP3...[/bold green]")
            download_video(url, None, output_path, only_audio=True)
            print("[bold green]✅ MP3 Downloaded![/bold green]")
            continue

        if mode == "playlist":
            print("[bold green]\n📜 Downloading full playlist...[/bold green]")
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(output_path, '%(playlist_title)s/%(title)s.%(ext)s')
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("[bold green]✅ Playlist Downloaded![/bold green]")
            continue

        print("\n[bold green]Fetching video info...[/bold green]")
        info = get_video_info(url)
        print(f"\n[bold]📌 Title:[/bold] {info['title']}")
        print(f"[bold]⏱️ Duration:[/bold] {info['duration']} seconds")

        if info.get("thumbnail"):
            print("[bold blue]\n🖼️ Previewing thumbnail...[/bold blue]")
            show_thumbnail(info["thumbnail"])

        formats = list_formats(info['formats'])
        choice = int(Prompt.ask("🎯 Enter [green]Index[/green] of quality to download")) - 1

        if 0 <= choice < len(formats):
            format_id = formats[choice]['format_id']
            print(f"\n[bold blue]📥 Downloading... Format ID: {format_id}[/bold blue]\n")
            download_video(url, format_id, output_path)
            print("[bold green]✅ Download Completed![/bold green]")
        else:
            print("[bold red]❌ Invalid selection![/bold red]")

if __name__ == "__main__":
    main()