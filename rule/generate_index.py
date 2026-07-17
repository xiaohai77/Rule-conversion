"""
扫描 rule/singbox 和 rule/mihomo，生成 rule/index.html 作为 Cloudflare Pages 的落地页。
由 .github/workflows/deploy-pages.yml 在部署前调用，不需要手动运行。

层级：规则名 -> sing-box / mihomo (严格分开，不混) -> domain / ipcidr -> 具体文件
"""
import os
import html as html_lib
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # rule/

# (物理目录, 格式, 分类)
SOURCE_DIRS = [
    ("singbox/domain", "sing-box", "domain"),
    ("singbox/ipcidr", "sing-box", "ipcidr"),
    ("mihomo/domain", "mihomo", "domain"),
    ("mihomo/ipcidr", "mihomo", "ipcidr"),
]
FORMATS = ["sing-box", "mihomo"]
CATEGORIES = ["domain", "ipcidr"]

COPY_ICON_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="9" y="9" width="13" height="13" rx="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
)


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def collect():
    """返回 { name: { 'sing-box': {'domain': [entry], 'ipcidr': [entry]}, 'mihomo': {...} } }
    entry = (relpath, filename, size)"""
    groups = {}
    for rel_dir, fmt, category in SOURCE_DIRS:
        folder = os.path.join(BASE_DIR, rel_dir)
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.startswith('.'):
                continue
            fpath = os.path.join(folder, fname)
            if not os.path.isfile(fpath):
                continue
            name = fname.rsplit('.', 1)[0]
            size = os.path.getsize(fpath)
            relpath = f"{rel_dir}/{fname}"
            groups.setdefault(name, {"sing-box": {"domain": [], "ipcidr": []},
                                      "mihomo": {"domain": [], "ipcidr": []}})
            groups[name][fmt][category].append((relpath, fname, size))
    return groups


def file_table(entries):
    if not entries:
        return '<p class="empty">此分类下没有文件</p>'
    rows = []
    for relpath, fname, size in entries:
        ext = fname.rsplit('.', 1)[-1] if '.' in fname else ''
        esc_path = html_lib.escape(relpath)
        rows.append(f'''
          <tr>
            <td><a class="fname" href="{relpath}">{html_lib.escape(fname)}</a></td>
            <td class="ftype">.{ext}</td>
            <td class="fsize">{human_size(size)}</td>
            <td class="op"><button class="copy-btn" data-path="{esc_path}" title="复制链接" onclick="copyLink(this)">{COPY_ICON_SVG}</button></td>
          </tr>''')
    return f'''
        <table>
          <thead><tr><th>文件</th><th>类型</th><th>大小</th><th></th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>'''


def category_block(category, entries):
    count = len(entries)
    return f'''
        <details class="cat"{' open' if count else ''}>
          <summary><span class="cat-name">{category}</span><span class="count">{count}</span></summary>
          {file_table(entries)}
        </details>'''


def format_block(fmt, cats):
    total = len(cats["domain"]) + len(cats["ipcidr"])
    fmt_cls = "sb" if fmt == "sing-box" else "mh"
    return f'''
      <div class="format-group {fmt_cls}"{' data-empty="1"' if total == 0 else ''}>
        <div class="format-header">
          <span class="format-name">{fmt}</span>
          <span class="format-count">{total} 个文件</span>
        </div>
        {category_block("domain", cats["domain"])}
        {category_block("ipcidr", cats["ipcidr"])}
      </div>'''


def name_block(name, fmts):
    total = sum(len(fmts[f][c]) for f in FORMATS for c in CATEGORIES)
    return f'''
    <details class="node">
      <summary>
        <span class="node-name">{html_lib.escape(name)}</span>
        <span class="node-meta">{total} 个文件</span>
      </summary>
      <div class="node-body">
        {format_block("sing-box", fmts["sing-box"])}
        {format_block("mihomo", fmts["mihomo"])}
      </div>
    </details>'''


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = collect()
    total_files = sum(len(fmts[f][c]) for fmts in groups.values() for f in FORMATS for c in CATEGORIES)
    names = sorted(groups.keys(), key=str.lower)

    nodes_html = "".join(name_block(name, groups[name]) for name in names) or \
        '<p class="empty">还没有构建产物，先跑一次 srs.yml / mrs.yml</p>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rule Feed</title>
<style>
  @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
  :root {{
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
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 44px 18px 90px;
    font-size: 15px;
    line-height: 1.5;
  }}
  .mono {{ font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace; }}
  a {{ color: inherit; }}
  .wrap {{ max-width: 780px; margin: 0 auto; }}
  h1 {{
    font-size: 21px; margin: 0 0 20px; color: var(--text); font-weight: 700;
  }}
  .stats {{ display: flex; gap: 20px; margin-bottom: 22px; font-size: 13px; color: var(--muted); }}
  .stats b {{ color: var(--text); font-weight: 600; }}

  details.node {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; margin-bottom: 12px; overflow: hidden;
    box-shadow: var(--shadow);
  }}
  details.node > summary {{
    list-style: none; cursor: pointer; padding: 14px 18px;
    display: flex; justify-content: space-between; align-items: center;
    user-select: none; font-weight: 600; font-size: 15px;
  }}
  details.node > summary::-webkit-details-marker {{ display: none; }}
  details.node > summary::before {{ content: "›"; margin-right: 8px; color: var(--muted); font-weight: 400; transition: transform .15s; display: inline-block; }}
  details.node[open] > summary::before {{ transform: rotate(90deg); }}
  .node-meta {{ color: var(--muted); font-weight: 400; font-size: 12.5px; }}
  .node-body {{ padding: 4px 18px 16px; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 14px; margin-top: 2px; }}

  .format-group {{
    border-left: 3px solid var(--border); padding-left: 12px; margin-top: 12px;
  }}
  .format-group.sb {{ border-left-color: var(--sb); }}
  .format-group.mh {{ border-left-color: var(--mh); }}
  .format-group[data-empty="1"] {{ opacity: 0.5; }}
  .format-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }}
  .format-name {{ font-weight: 700; font-size: 13px; }}
  .format-group.sb .format-name {{ color: var(--sb); }}
  .format-group.mh .format-name {{ color: var(--mh); }}
  .format-count {{ color: var(--muted); font-size: 11.5px; }}

  details.cat {{
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; margin-top: 8px; overflow: hidden;
  }}
  details.cat summary {{
    list-style: none; cursor: pointer; padding: 8px 12px;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 12.5px; user-select: none;
  }}
  details.cat summary::-webkit-details-marker {{ display: none; }}
  details.cat summary::before {{ content: "›"; margin-right: 6px; color: var(--muted); display: inline-block; transition: transform .15s; }}
  details.cat[open] summary::before {{ transform: rotate(90deg); }}
  .cat-name {{ font-weight: 600; text-transform: capitalize; }}
  .count {{
    color: var(--muted); background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 1px 8px; font-size: 11px;
  }}

  table {{ width: 100%; border-collapse: collapse; border-top: 1px solid var(--border); }}
  thead th {{
    text-align: left; color: var(--muted); font-weight: 400; font-size: 11px;
    padding: 6px 12px;
  }}
  tbody tr {{ border-top: 1px solid var(--border); }}
  tbody tr:hover {{ background: var(--accent-soft); }}
  tbody td {{ padding: 7px 12px; font-size: 13px; }}
  a.fname {{ text-decoration: none; color: var(--text); font-weight: 500; }}
  a.fname:hover {{ color: var(--accent); text-decoration: underline; }}
  .ftype {{ color: var(--muted); }}
  .fsize {{ color: var(--muted); text-align: right; }}
  .op {{ text-align: right; width: 36px; }}
  .empty {{ color: var(--muted); font-size: 13px; padding: 10px 0; margin: 0; }}

  .copy-btn {{
    background: transparent; border: 1px solid var(--border); color: var(--muted);
    border-radius: 6px; width: 30px; height: 30px; cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    transition: color .12s, border-color .12s, background .12s;
  }}
  .copy-btn:hover {{ color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }}
  .copy-btn.copied {{ color: var(--mh); border-color: var(--mh); background: var(--mh-soft); }}

  footer {{ margin-top: 32px; color: var(--muted); font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Rule Feed</h1>
  <div class="stats">
    <span><b>{len(names)}</b> 个规则</span>
    <span><b>{total_files}</b> 个文件</span>
    <span>更新于 <b>{now}</b></span>
  </div>

  {nodes_html}

  <footer>由 rule/generate_index.py 自动生成</footer>
</div>

<script>
  var CHECK_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';

  function copyLink(btn) {{
    var text = location.origin + '/' + btn.dataset.path;
    var original = btn.innerHTML;
    navigator.clipboard.writeText(text).then(function () {{
      btn.innerHTML = CHECK_ICON;
      btn.classList.add('copied');
      setTimeout(function () {{
        btn.innerHTML = original;
        btn.classList.remove('copied');
      }}, 1200);
    }});
  }}
</script>
</body>
</html>'''

    out_path = os.path.join(BASE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"生成 {out_path}，共 {len(names)} 个规则名 / {total_files} 个文件")


if __name__ == "__main__":
    main()
