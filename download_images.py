import requests
import os

url1 = "https://s3.polza.ai/f/213179/2026/09/t_61973185d9a26564.png"
url2 = "https://s3.polza.ai/f/213179/2026/09/t_e13820bfa3c2d25e.png"

out1 = "frontend/public/assets/russian_grandpa_neutral.png"
out2 = "frontend/public/assets/male_young/smiling_wide.png"

def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    resp = requests.get(url)
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"Downloaded {path}")

download(url1, out1)
download(url2, out2)
