import os
import requests

LINKS_PATH = os.path.join(os.path.dirname(__file__), "..", "links", "links-geodata.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "georules", "geodata")


def read_entries(path):
    """每行格式: [自定义名] 链接
    自定义名可省略，省略时用链接本身的文件名（含扩展名）。
    写了自定义名时，保留链接原本的扩展名，只替换文件名主体。"""
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) == 1:
                entries.append((None, parts[0]))
            else:
                entries.append((parts[0], parts[1]))
    return entries


def download(custom_name, url, out_dir):
    orig_filename = url.rstrip("/").rsplit("/", 1)[-1]
    if not orig_filename:
        print(f"[跳过] {url}：无法从链接推断出文件名")
        return

    if custom_name:
        ext = ("." + orig_filename.rsplit(".", 1)[-1]) if "." in orig_filename else ""
        filename = f"{custom_name}{ext}"
    else:
        filename = orig_filename

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

    print(f"[完成] {url} -> georules/geodata/{filename} ({size} 字节)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    entries = read_entries(LINKS_PATH)

    if not entries:
        print("links-geodata.txt 里没有找到任何链接，跳过")
        return

    for custom_name, url in entries:
        try:
            download(custom_name, url, OUTPUT_DIR)
        except Exception as e:
            print(f"[出错] {url} 下载失败，已跳过，原因：{e}")


if __name__ == "__main__":
    main()
