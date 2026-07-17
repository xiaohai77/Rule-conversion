"""
扫描 rule/singbox 和 rule/mihomo，为每一级目录各生成一个 index.html，
浏览体验跟 GitHub 网页版目录一致：

  rule/index.html                 -> 显示 singbox/ mihomo/ 两个文件夹
  rule/singbox/index.html         -> 显示 domain/ ipcidr/ 两个文件夹
  rule/singbox/domain/index.html  -> 显示该目录下的具体文件
  rule/singbox/ipcidr/index.html  -> 同上
  rule/mihomo/index.html          -> 显示 domain/ ipcidr/
  rule/mihomo/domain/index.html   -> 显示该目录下的具体文件
  rule/mihomo/ipcidr/index.html   -> 同上

由 .github/workflows/deploy-pages.yml 在部署前调用，不需要手动运行。
"""
import os
import html as html_lib
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # rule/

TREE = {
    "singbox": ["domain", "ipcidr"],
    "mihomo": ["domain", "ipcidr"],
}

COPY_ICON_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="9" y="9" width="13" height="13" rx="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
)
FOLDER_ICON_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"></path></svg>'
)

STYLE = '''
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
  :root {
    --bg: #f7f8fa;
    --card: #ffffff;
    --border: #e6e8ee;
    --text: #1e222b;
    --muted: #7a8194;
    --accent: #3562e0;
    --accent-soft: #eef2fd;
    --sb: #3562e0;
    --sb-soft: #eef2fd;
    --mh: #0f9d78;
    --mh-soft: #e6f7f1;
    --shadow: 0 1px 2px rgba(20, 24, 33, 0.04), 0 1px 8px rgba(20, 24, 33, 0.03);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 44px 18px 90px;
    font-size: 15px;
    line-height: 1.5;
  }
  a { color: inherit; }
  .wrap { max-width: 780px; margin: 0 auto; }
  .crumb { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
  .crumb a { color: var(--accent); text-decoration: none; }
  .crumb a:hover { text-decoration: underline; }
  .crumb .sep { margin: 0 6px; color: var(--border); }
  h1 { font-size: 21px; margin: 0 0 20px; font-weight: 700; }
  .stats { display: flex; gap: 20px; margin-bottom: 22px; font-size: 13px; color: var(--muted); }
  .stats b { color: var(--text); font-weight: 600; }

  .folder-grid { display: flex; flex-direction: column; gap: 10px; }
  .folder-card {
    display: flex; align-items: center; gap: 14px; text-decoration: none;
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px 18px; box-shadow: var(--shadow); color: var(--text);
    transition: border-color .12s, transform .12s;
  }
  .folder-card:hover { border-color: var(--accent); transform: translateY(-1px); }
  .folder-card .icon { color: var(--accent); flex-shrink: 0; }
  .folder-card.mh .icon { color: var(--mh); }
  .folder-card .name { font-weight: 600; font-size: 15px; flex: 1; }
  .folder-card .meta { color: var(--muted); font-size: 12.5px; }

  .table-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    box-shadow: var(--shadow); overflow: hidden;
  }
  .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  table { width: 100%; border-collapse: collapse; min-width: 100%; }
  thead th {
    text-align: left; color: var(--muted); font-weight: 400; font-size: 11px;
    padding: 10px 14px; border-bottom: 1px solid var(--border);
  }
  tbody tr { border-top: 1px solid var(--border); }
  tbody tr:first-child { border-top: none; }
  tbody tr:hover { background: var(--accent-soft); }
  tbody td { padding: 9px 14px; font-size: 13px; white-space: nowrap; }
  td.fname-cell { max-width: 0; width: 100%; overflow: hidden; text-overflow: ellipsis; }
  a.fname {
    text-decoration: none; color: var(--text); font-weight: 500;
    font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  }
  a.fname:hover { color: var(--accent); text-decoration: underline; }
  .ftype { color: var(--muted); }
  .fsize { color: var(--muted); text-align: right; }
  .op { text-align: right; width: 44px; padding-right: 14px !important; }
  .empty { color: var(--muted); font-size: 13px; padding: 18px; margin: 0; text-align: center; }

  .copy-btn {
    background: transparent; border: 1px solid var(--border); color: var(--muted);
    border-radius: 6px; width: 30px; height: 30px; cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    transition: color .12s, border-color .12s, background .12s;
    flex-shrink: 0;
  }
  .copy-btn:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }
  .copy-btn.copied { color: var(--mh); border-color: var(--mh); background: var(--mh-soft); }

  footer { margin-top: 32px; color: var(--muted); font-size: 12px; text-align: center; }
'''

SCRIPT = '''
  var CHECK_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  function copyLink(btn) {
    var text = location.origin + '/' + btn.dataset.path;
    var original = btn.innerHTML;
    navigator.clipboard.writeText(text).then(function () {
      btn.innerHTML = CHECK_ICON;
      btn.classList.add('copied');
      setTimeout(function () {
        btn.innerHTML = original;
        btn.classList.remove('copied');
      }, 1200);
    });
  }
'''


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def collect_files(folder):
    if not os.path.isdir(folder):
        return []
    items = []
    for fname in sorted(os.listdir(folder)):
        if fname.startswith('.'):
            continue
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            items.append((fname, os.path.getsize(fpath)))
    return items


def breadcrumb_html(parts):
    """parts: [(label, href_or_None)]，最后一个是当前页不加链接"""
    segs = []
    for i, (label, href) in enumerate(parts):
        if href:
            segs.append(f'<a href="{href}">{label}</a>')
        else:
            segs.append(f'<span>{label}</span>')
    sep = '<span class="sep">/</span>'
    return f'<div class="crumb">{sep.join(segs)}</div>'


def page_shell(title, crumb, body):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  {crumb}
  <h1>{title}</h1>
  {body}
  <footer>由 rule/generate_index.py 自动生成</footer>
</div>
<script>{SCRIPT}</script>
</body>
</html>'''


def render_folder_page(title, crumb, folders):
    """folders: [(name, href, count, cls)]"""
    cards = []
    for name, href, count, cls in folders:
        cards.append(f'''
      <a class="folder-card {cls}" href="{href}">
        <span class="icon">{FOLDER_ICON_SVG}</span>
        <span class="name">{name}/</span>
        <span class="meta">{count} 个文件</span>
      </a>''')
    body = f'<div class="folder-grid">{"".join(cards)}</div>'
    return page_shell(title, crumb, body)


def render_file_page(title, crumb, rel_dir, entries):
    if not entries:
        table_html = '<p class="empty">-- 这里还没有文件，先跑一次对应的 build workflow --</p>'
    else:
        rows = []
        for fname, size in entries:
            ext = fname.rsplit('.', 1)[-1] if '.' in fname else ''
            relpath = f"{rel_dir}/{fname}"
            esc_path = html_lib.escape(relpath)
            rows.append(f'''
              <tr>
                <td class="fname-cell"><a class="fname" href="{fname}">{html_lib.escape(fname)}</a></td>
                <td class="ftype">.{ext}</td>
                <td class="fsize">{human_size(size)}</td>
                <td class="op"><button class="copy-btn" data-path="{esc_path}" title="复制链接" onclick="copyLink(this)">{COPY_ICON_SVG}</button></td>
              </tr>''')
        table_html = f'''
        <div class="table-card">
          <div class="table-scroll">
            <table>
              <thead><tr><th>文件</th><th>类型</th><th>大小</th><th></th></tr></thead>
              <tbody>{''.join(rows)}</tbody>
            </table>
          </div>
        </div>'''
    stats = f'<div class="stats"><span><b>{len(entries)}</b> 个文件</span></div>'
    return page_shell(title, crumb, stats + table_html)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_files = 0

    # 根页面: rule/index.html -> singbox/ mihomo/
    root_folders = []
    for top, subs in TREE.items():
        cls = "sb" if top == "singbox" else "mh"
        count = sum(len(collect_files(os.path.join(BASE_DIR, top, sub))) for sub in subs)
        root_folders.append((top, f"{top}/", count, cls))
    root_crumb = breadcrumb_html([("Rule Feed", None)])
    write(os.path.join(BASE_DIR, "index.html"),
          render_folder_page("Rule Feed", root_crumb, root_folders))

    # 二级页面: rule/singbox/index.html, rule/mihomo/index.html -> domain/ ipcidr/
    for top, subs in TREE.items():
        cls = "sb" if top == "singbox" else "mh"
        sub_folders = []
        for sub in subs:
            count = len(collect_files(os.path.join(BASE_DIR, top, sub)))
            sub_folders.append((sub, f"{sub}/", count, cls))
        crumb = breadcrumb_html([("Rule Feed", "/"), (top, None)])
        write(os.path.join(BASE_DIR, top, "index.html"),
              render_folder_page(top, crumb, sub_folders))

        # 三级页面: rule/singbox/domain/index.html 等 -> 具体文件
        for sub in subs:
            folder = os.path.join(BASE_DIR, top, sub)
            entries = collect_files(folder)
            total_files += len(entries)
            crumb = breadcrumb_html([("Rule Feed", "/"), (top, f"/{top}/"), (sub, None)])
            write(os.path.join(folder, "index.html"),
                  render_file_page(f"{top}/{sub}", crumb, f"{top}/{sub}", entries))

    print(f"生成完毕，共 {total_files} 个文件，构建时间 {now}")


if __name__ == '__main__':
    main()
