"""
扫描 rule/singbox 和 rule/mihomo，生成 rule/index.html 作为 Cloudflare Pages 的落地页。
由 .github/workflows/deploy-pages.yml 在部署前调用，不需要手动运行。

按“规则名”分组，而不是按 singbox/mihomo 分组：
  china/
    domain/   china.json  china.srs  china.yaml  china.mrs  (只列实际存在的)
    ipcidr/   ...
点开规则名 -> 再点开 domain 或 ipcidr -> 才看到具体文件，格式(sing-box/mihomo)用小标签区分。
"""
import os
import html as html_lib
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # rule/

# (物理目录, 分类 domain/ipcidr, 来源标签)
SOURCE_DIRS = [
    ("singbox/domain", "domain", "sing-box"),
    ("singbox/ipcidr", "ipcidr", "sing-box"),
    ("mihomo/domain", "domain", "mihomo"),
    ("mihomo/ipcidr", "ipcidr", "mihomo"),
]


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def collect():
    """返回 { name: { 'domain': [entry,...], 'ipcidr': [entry,...] } }
    entry = (relpath, filename, size, source_label)"""
    groups = {}
    for rel_dir, category, source_label in SOURCE_DIRS:
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
            groups.setdefault(name, {'domain': [], 'ipcidr': []})
            groups[name][category].append((relpath, fname, size, source_label))
    return groups


def copy_btn(relpath):
    esc = html_lib.escape(relpath)
    return (f'<button class="copy-btn" data-path="{esc}" title="复制完整链接" '
            f'onclick="copyLink(this)">⧉</button>')


def file_table(entries):
    if not entries:
        return '<div class="empty">-- empty --</div>'
    rows = []
    for relpath, fname, size, source_label in entries:
        ext = fname.rsplit('.', 1)[-1] if '.' in fname else ''
        badge_cls = "sb" if source_label == "sing-box" else "mh"
        rows.append(f'''
          <tr>
            <td><a class="fname" href="{relpath}">{html_lib.escape(fname)}</a></td>
            <td><span class="badge {badge_cls}">{source_label}</span></td>
            <td class="ftype">.{ext}</td>
            <td class="fsize">{human_size(size)}</td>
            <td class="op">{copy_btn(relpath)}</td>
          </tr>''')
    return f'''
        <table>
          <thead><tr><th>file</th><th>format</th><th>type</th><th>size</th><th></th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>'''


def category_block(label, entries):
    count = len(entries)
    empty_cls = " is-empty" if count == 0 else ""
    return f'''
      <details class="cat{empty_cls}">
        <summary><span class="cat-name">{label}/</span><span class="count">{count}</span></summary>
        {file_table(entries)}
      </details>'''


def name_block(name, cats):
    total = len(cats['domain']) + len(cats['ipcidr'])
    return f'''
    <details class="node">
      <summary>
        <span class="node-name">{html_lib.escape(name)}</span>
        <span class="node-meta">domain × {len(cats['domain'])} &nbsp; ipcidr × {len(cats['ipcidr'])}</span>
      </summary>
      <div class="node-body">
        {category_block('domain', cats['domain'])}
        {category_block('ipcidr', cats['ipcidr'])}
      </div>
    </details>'''


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = collect()
    total_files = sum(len(v['domain']) + len(v['ipcidr']) for v in groups.values())
    names = sorted(groups.keys(), key=str.lower)

    nodes_html = "".join(name_block(name, groups[name]) for name in names) or \
        '<p class="empty">-- 还没有构建产物，先跑一次 srs.yml / mrs.yml --</p>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>rule-feed // index</title>
<style>
  @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
  :root {{
    --bg: #f5f7fa;
    --panel: #ffffff;
    --line: #dde3ec;
    --text: #1b2433;
    --muted: #707c8f;
    --accent: #2f5fa8;
    --accent-soft: #eaf1fb;
    --sb: #2f5fa8;
    --sb-soft: #eaf1fb;
    --mh: #9a5b21;
    --mh-soft: #fbf0e3;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background:
      linear-gradient(var(--line) 1px, transparent 1px) 0 0/100% 28px,
      var(--bg);
    color: var(--text);
    font-family: "SFMono-Regular", "JetBrains Mono", Consolas, Menlo, monospace;
    padding: 48px 20px 90px;
    font-size: 14px;
  }}
  a {{ color: inherit; }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  .prompt {{ color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
  h1 {{
    font-size: 22px; margin: 0 0 4px; color: var(--text);
    letter-spacing: 0.01em; font-weight: 700;
  }}
  .sub {{ color: var(--muted); font-size: 13px; margin: 0 0 18px; }}
  .origin-row {{
    display: flex; align-items: center; gap: 8px; margin-bottom: 26px;
    background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
    padding: 10px 12px; font-size: 12.5px;
  }}
  .origin-row .label {{ color: var(--muted); }}
  .origin-row .origin-url {{ color: var(--accent); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .stats {{ display: flex; gap: 20px; margin-bottom: 22px; font-size: 12px; color: var(--muted); }}
  .stats b {{ color: var(--accent); font-weight: 700; }}

  details.node {{
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 10px; margin-bottom: 10px; overflow: hidden;
  }}
  details.node > summary {{
    list-style: none; cursor: pointer; padding: 12px 16px;
    display: flex; justify-content: space-between; align-items: center;
    user-select: none;
  }}
  details.node > summary::-webkit-details-marker {{ display: none; }}
  details.node > summary::before {{ content: "▸ "; color: var(--accent); margin-right: 2px; }}
  details.node[open] > summary::before {{ content: "▾ "; }}
  .node-name {{ font-size: 14.5px; font-weight: 700; }}
  .node-meta {{ color: var(--muted); font-size: 11.5px; }}
  .node-body {{ padding: 4px 16px 14px; border-top: 1px solid var(--line); }}

  details.cat {{
    background: var(--bg); border: 1px solid var(--line);
    border-radius: 6px; margin-top: 10px; overflow: hidden;
  }}
  details.cat.is-empty {{ opacity: 0.55; }}
  details.cat summary {{
    list-style: none; cursor: pointer; padding: 8px 12px;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 12.5px; user-select: none;
  }}
  details.cat summary::-webkit-details-marker {{ display: none; }}
  details.cat summary::before {{ content: "▸ "; color: var(--muted); }}
  details.cat[open] summary::before {{ content: "▾ "; }}
  .cat-name {{ color: var(--accent); font-weight: 600; }}
  .count {{
    color: var(--muted); background: var(--panel); border: 1px solid var(--line);
    border-radius: 10px; padding: 1px 8px; font-size: 11px;
  }}

  table {{ width: 100%; border-collapse: collapse; border-top: 1px solid var(--line); }}
  thead th {{
    text-align: left; color: var(--muted); font-weight: 400; font-size: 10.5px;
    padding: 6px 12px; text-transform: lowercase; letter-spacing: 0.04em;
  }}
  tbody tr {{ border-top: 1px solid var(--line); }}
  tbody tr:hover {{ background: var(--accent-soft); }}
  tbody td {{ padding: 6px 12px; font-size: 12.5px; }}
  a.fname {{ text-decoration: none; color: var(--text); }}
  a.fname:hover {{ color: var(--accent); text-decoration: underline; }}
  .badge {{
    font-size: 10px; padding: 2px 7px; border-radius: 8px; font-weight: 600;
  }}
  .badge.sb {{ color: var(--sb); background: var(--sb-soft); }}
  .badge.mh {{ color: var(--mh); background: var(--mh-soft); }}
  .ftype {{ color: var(--muted); }}
  .fsize {{ color: var(--muted); text-align: right; }}
  .op {{ text-align: right; width: 30px; }}
  .empty {{ color: var(--muted); font-style: italic; padding: 10px 0; font-size: 12.5px; }}

  .copy-btn {{
    background: var(--panel); border: 1px solid var(--line); color: var(--muted);
    border-radius: 5px; width: 24px; height: 24px; cursor: pointer;
    font-size: 12px; line-height: 1; transition: color .12s, border-color .12s;
  }}
  .copy-btn:hover {{ color: var(--accent); border-color: var(--accent); }}
  .copy-btn.copied {{ color: #2f9e5a; border-color: #2f9e5a; }}

  footer {{ margin-top: 36px; color: var(--muted); font-size: 11px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="prompt">$ tree rule/ --group-by=name</div>
  <h1>rule-feed index</h1>
  <p class="sub">sing-box / mihomo 规则集自动构建产物 · 按规则名分组，展开查看 domain / ipcidr</p>

  <div class="origin-row">
    <span class="label">当前站点：</span>
    <span class="origin-url" id="originUrl">...</span>
    <button class="copy-btn" title="复制站点地址" onclick="copyLink(this, true)">⧉</button>
  </div>

  <div class="stats">
    <span><b>{len(names)}</b> 个规则</span>
    <span><b>{total_files}</b> 个文件</span>
    <span>built <b>{now}</b></span>
  </div>

  {nodes_html}

  <footer>generated by rule/generate_index.py · deployed via Cloudflare Pages</footer>
</div>

<script>
  document.getElementById('originUrl').textContent = location.origin + '/';

  function copyLink(btn, isOrigin) {{
    var text = isOrigin ? (location.origin + '/') : (location.origin + '/' + btn.dataset.path);
    navigator.clipboard.writeText(text).then(function () {{
      var original = btn.textContent;
      btn.textContent = '✓';
      btn.classList.add('copied');
      setTimeout(function () {{
        btn.textContent = original;
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
