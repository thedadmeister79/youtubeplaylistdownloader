import os
import subprocess
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TRCK
from pathlib import Path
import re
import streamlit as st
import zipfile
import shutil

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

def zip_mp3s(output_dir, zip_name):
    zip_path = Path(output_dir) / zip_name
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for mp3_file in Path(output_dir).glob("*.mp3"):
            zipf.write(mp3_file, arcname=mp3_file.name)
    return zip_path

def download_and_process(playlist_url, artist, album, log_area):
    output_dir = "downloaded_mp3s"

    # Step 1: Clean old MP3s folder entirely
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    log_area.text("🟡 Cleaned previous downloads...")

    # Step 2: Start downloading
    ytdlp_command = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", os.path.join(output_dir, "%(playlist_index)03d - %(title)s.%(ext)s"),
        playlist_url
    ]

    process = subprocess.Popen(
        ytdlp_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    output_log = "📥 Downloading songs...\n"
    for line in process.stdout:
        output_log += line
        log_area.text(output_log[-3000:])  # Stream output

    process.wait()

    # Step 3: Process downloaded MP3s
    mp3_files = sorted(Path(output_dir).glob("*.mp3"))

    for index, file_path in enumerate(mp3_files, start=1):
        try:
            title = file_path.stem.split(" - ", 1)[1]
        except IndexError:
            title = file_path.stem

        track_num = f"{index:02d}"
        formatted_title = f"{track_num} - {title}"
        new_filename = f"{track_num} - {sanitize_filename(title)}.mp3"
        new_file_path = file_path.with_name(new_filename)
        os.rename(file_path, new_file_path)

        audio = ID3(new_file_path)
        audio["TIT2"] = TIT2(encoding=3, text=formatted_title)
        audio["TPE1"] = TPE1(encoding=3, text=artist)
        audio["TALB"] = TALB(encoding=3, text=album)
        audio["TRCK"] = TRCK(encoding=3, text=str(index))
        audio.save()

        output_log += f'\n✅ Tagged: {formatted_title}'
        log_area.text(output_log[-3000:])

    # Step 4: Zip the folder using album name
    zip_name = f"{sanitize_filename(album)}.zip"
    zip_path = zip_mp3s(output_dir, zip_name)

    output_log += f"\n📦 Zipped all MP3s as: {zip_name}"
    log_area.text(output_log[-3000:])

    return len(mp3_files), zip_path

# -------------------------
# Streamlit UI
# -------------------------

st.title("🎵 YouTube Playlist to MP3 + ZIP")

playlist_url = st.text_input("📺 YouTube Playlist URL")
artist = st.text_input("🎤 Artist Name")
album = st.text_input("💿 Album Name (used for ZIP name too)")

if st.button("Download Playlist"):
    if playlist_url and artist and album:
        log_area = st.empty()
        with st.spinner("Downloading and tagging... please wait..."):
            total_tracks, zip_file = download_and_process(playlist_url, artist, album, log_area)
        st.success(f"✅ Done! {total_tracks} tracks downloaded and tagged.")
        with open(zip_file, "rb") as f:
            st.download_button(
                label="⬇️ Download ZIP",
                data=f,
                file_name=zip_file.name,
                mime="application/zip"
            )
    else:
        st.warning("⚠️ Please fill in all fields before continuing.")
