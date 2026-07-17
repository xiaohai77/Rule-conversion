import os
import requests

LINKS_PATH = os.path.join(os.path.dirname(__file__), "..", "links", "links-geodata.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "geo-data", "geodata")


def read_urls(path):
    urls = []
    if not os.path.exists(path):
        return urls
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def download(url, out_dir):
    filename = url.rstrip("/").rsplit("/", 1)[-1]
    if not filename:
        print(f"[跳过] {url}：无法从链接推断出文件名")
        return
    dest = os.path.join(out_dir, filename)

    resp = requests.get(url, stream=True, timeout=60, allow_redirects=True)
    resp.raise_for_status()

    tmp_dest = dest + ".tmp"
    size = 0
    with open(tmp_dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                size += len(chunk)
    os.replace(tmp_dest, dest)

    print(f"[完成] {url} -> geo-data/geodata/{filename} ({size} 字节)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    urls = read_urls(LINKS_PATH)

    if not urls:
        print("links-geodata.txt 里没有找到任何链接，跳过")
        return

    for url in urls:
        try:
            download(url, OUTPUT_DIR)
        except Exception as e:
            print(f"[出错] {url} 下载失败，已跳过，原因：{e}")


if __name__ == "__main__":
    main()
