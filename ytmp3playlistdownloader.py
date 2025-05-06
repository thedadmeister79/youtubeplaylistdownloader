import os
import subprocess
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TALB, TPE1
from pathlib import Path
import re

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

def main():
    # Prompt for playlist URL
    playlist_url = input("Enter the YouTube playlist URL: ").strip()

    # Create output directory
    output_dir = "downloaded_mp3s"
    os.makedirs(output_dir, exist_ok=True)

    # yt-dlp command
    ytdlp_command = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", os.path.join(output_dir, "%(playlist_index)03d - %(title)s.%(ext)s"),
        playlist_url
    ]

    # Run yt-dlp
    subprocess.run(ytdlp_command)

    # Rename and tag files
    mp3_files = sorted(Path(output_dir).glob("*.mp3"))

    print("\nTagging MP3 files...")
    artist = input("Enter artist name: ").strip()
    album = input("Enter album name: ").strip()

    for index, file_path in enumerate(mp3_files, start=1):
        title = file_path.stem.split(" - ", 1)[1]
        track_num = f"{index:02d}"
        new_filename = f"{track_num} - {sanitize_filename(title)}.mp3"
        new_file_path = file_path.with_name(new_filename)
        os.rename(file_path, new_file_path)

        # Set ID3 tags
        audio = EasyID3(new_file_path)
        audio["title"] = title
        audio["artist"] = artist
        audio["album"] = album
        audio["tracknumber"] = str(index)
        audio.save()

        print(f"Tagged and renamed: {new_filename}")

    print("\nAll files processed successfully.")

if __name__ == "__main__":
    main()
