import os
import concurrent.futures
import tempfile
from collections import defaultdict

import common

# 手动维护的规则源（links-domain / links-ipcidr / links-mixed）
# 输出到 rules/quantumultx，与 rules/mihomo、rules/singbox 平级
RULES_LINKS_FILES = [
    "../links/links-domain.txt",
    "../links/links-ipcidr.txt",
    "../links/links-mixed.txt",
]
RULES_OUTPUT_ROOT = "../rules/quantumultx"

# 自动从 MetaCubeX/meta-rules-dat 拉取的全量 geosite+geoip（links-meta.txt）
# 输出到 geo-data/quantumultx，与 geo-data/mihomo、geo-data/singbox 平级
GEO_LINKS_FILES = [
    "../links/links-meta.txt",
]
GEO_OUTPUT_ROOT = "../geo-data/quantumultx"


def merge_unified(unified_list):
    merged = {}
    for unified in unified_list:
        for key, values in unified.items():
            merged.setdefault(key, set()).update(values)
    return merged


def group_links(links_files):
    """按 name 分组，同一个 name 的多个来源（例如 geosite+geoip）会被合并到一起，
    避免多个线程同时写同一个输出目录。"""
    groups = defaultdict(list)
    for links_path in links_files:
        for custom_name, link in common.read_links(links_path):
            kind, url = common.detect_source(link)
            name = custom_name or common.base_name(url)
            groups[name].append(link)
    return groups


def build_group(name, links, work_dir, output_root):
    unified_list = []
    for link in links:
        try:
            _, unified = common.link_to_unified(link, work_dir, name)
        except Exception as e:
            print(f"[出错] {link} 处理失败，已跳过，原因：{e}")
            continue

        if unified == 'UNSUPPORTED':
            print(f"[跳过] {link}：无法从 mrs 反解，QuantumultX 规则无法导入")
            continue
        if not unified:
            print(f"[跳过] {link}：未解析出任何规则")
            continue
        unified_list.append(unified)

    if not unified_list:
        return

    unified = merge_unified(unified_list)
    domain_part, ipcidr_part, leftover = common.split_mixed_unified(unified)
    if leftover:
        print(f"[提示] {name}: 以下字段既不算域名也不算IP，已跳过: {leftover}")

    domain_dir = os.path.join(output_root, "domain")
    ipcidr_dir = os.path.join(output_root, "ipcidr")
    wrote = []
    if common.write_qx_list(domain_part, {}, os.path.join(domain_dir, f"{name}.list")):
        wrote.append("Domain")
    if common.write_qx_list({}, ipcidr_part, os.path.join(ipcidr_dir, f"{name}.list")):
        wrote.append("IP")

    if wrote:
        print(f"[完成] {name} -> {output_root}/{{domain,ipcidr}}/{name}.list，共 {len(links)} 个源")
    else:
        print(f"[跳过] {name}：过滤后没有可写入的规则")


def run_group(links_files, output_root, work_dir):
    os.makedirs(output_root, exist_ok=True)
    groups = group_links(links_files)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(
            lambda item: build_group(item[0], item[1], work_dir, output_root),
            groups.items(),
        ))


def main():
    with tempfile.TemporaryDirectory() as work_dir:
        run_group(RULES_LINKS_FILES, RULES_OUTPUT_ROOT, work_dir)
        run_group(GEO_LINKS_FILES, GEO_OUTPUT_ROOT, work_dir)


if __name__ == '__main__':
    main()
