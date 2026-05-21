import os
import time
import subprocess

# =========================
# CONFIG
# =========================

BROWSER_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

profile_dir = r"C:\Profiles"
profile_email = "Profile 1"

EXTENTION_EX3 = r"C:\RepProxy\Ext3"

url = "https://accounts.google.com"

# =========================
# COMMAND 1
# OPEN EDGE WITH EXTENSION
# =========================

command = [
    BROWSER_PATH,

    f"--user-data-dir={profile_dir}",
    f"--profile-directory={profile_email}",

    f"--disable-extensions-except={EXTENTION_EX3}",
    f"--load-extension={EXTENTION_EX3}",

    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",

    "--disable-popup-blocking",
    "--disable-notifications",
    "--disable-features=DownloadBubble",
]

# =========================
# COMMAND 2
# OPEN URL
# =========================

command1 = [
    BROWSER_PATH,

    f"--user-data-dir={profile_dir}",
    f"--profile-directory={profile_email}",

    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",

    "--disable-popup-blocking",
    "--disable-notifications",
    "--disable-features=DownloadBubble",

    url,
]

# =========================
# START EDGE
# =========================

print("START EDGE WITH EXTENSION")

process = subprocess.Popen(command)

print("PID 1 =", process.pid)

# WAIT 3s
time.sleep(3)

print("OPEN URL")

process1 = subprocess.Popen(command1)

print("PID 2 =", process1.pid)

# =========================
# WAIT 15s
# =========================

print("WAIT 15 SECONDS...")
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)
time.sleep(15)

# =========================
# CLOSE WINDOWS
# =========================

print("CLOSE EDGE")

try:
    subprocess.call(
        f'taskkill /F /PID {process.pid} /T',
        shell=True
    )
except:
    pass

# try:
#     subprocess.call(
#         f'taskkill /F /PID {process1.pid} /T',
#         shell=True
#     )
# except:
#     pass

print("DONE")