import os
import subprocess
from mutagen.easyid3 import EasyID3
from pathlib import Path
import re
import streamlit as st
import zipfile

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

def zip_mp3s(output_dir, zip_name):
    zip_path = Path(output_dir) / zip_name
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for mp3_file in Path(output_dir).glob("*.mp3"):
            zipf.write(mp3_file, arcname=mp3_file.name)
    return zip_path

def download_and_process(playlist_url, artist, album):
    output_dir = "downloaded_mp3s"
    os.makedirs(output_dir, exist_ok=True)

    ytdlp_command = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", os.path.join(output_dir, "%(playlist_index)03d - %(title)s.%(ext)s"),
        playlist_url
    ]

    subprocess.run(ytdlp_command)

    mp3_files = sorted(Path(output_dir).glob("*.mp3"))
    for index, file_path in enumerate(mp3_files, start=1):
        try:
            title = file_path.stem.split(" - ", 1)[1]
        except IndexError:
            title = file_path.stem
        track_num = f"{index:02d}"
        new_filename = f"{track_num} - {sanitize_filename(title)}.mp3"
        new_file_path = file_path.with_name(new_filename)
        os.rename(file_path, new_file_path)

        audio = EasyID3(new_file_path)
        audio["title"] = title
        audio["artist"] = artist
        audio["album"] = album
        audio["tracknumber"] = str(index)
        audio.save()

    zip_path = zip_mp3s(output_dir, "playlist_download.zip")
    return len(mp3_files), zip_path

# -------------------------
# Streamlit App UI
# -------------------------

st.title("🎵 YouTube Playlist to MP3 + ZIP")

playlist_url = st.text_input("📺 YouTube Playlist URL")
artist = st.text_input("🎤 Artist Name")
album = st.text_input("💿 Album Name")

if st.button("Download Playlist"):
    if playlist_url and artist and album:
        with st.spinner("Downloading and converting... please wait..."):
            total_tracks, zip_file = download_and_process(playlist_url, artist, album)
        st.success(f"✅ Done! {total_tracks} tracks downloaded and tagged.")
        with open(zip_file, "rb") as f:
            st.download_button(
                label="⬇️ Download ZIP",
                data=f,
                file_name="playlist_download.zip",
                mime="application/zip"
            )
    else:
        st.warning("⚠️ Please fill in all fields before continuing.")
