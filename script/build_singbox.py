import os
import concurrent.futures
import tempfile
from collections import defaultdict

import common

# 手动维护的规则源（links-domain / links-ipcidr / links-mixed）
# 输出到 rules/singbox
RULES_LINKS_FILES = [
    "../links/links-domain.txt",
    "../links/links-ipcidr.txt",
    "../links/links-mixed.txt",
]
RULES_OUTPUT_ROOT = "../rules/singbox"

# 自动从 MetaCubeX/meta-rules-dat 拉取的全量 geosite+geoip（links-meta.txt）
# 输出到 geo-data/singbox，与手动维护的规则分开存放
GEO_LINKS_FILES = [
    "../links/links-meta.txt",
]
GEO_OUTPUT_ROOT = "../geo-data/singbox"


def write_domain(filtered, name, out_dir):
    if not filtered:
        return False
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{name}.json")
    srs_path = os.path.join(out_dir, f"{name}.srs")
    common.unified_to_singbox_json(filtered, json_path)
    common.run(["sing-box", "rule-set", "compile", "--output", srs_path, json_path])
    return True


def write_ip(filtered, name, out_dir):
    if not filtered:
        return False
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{name}.json")
    srs_path = os.path.join(out_dir, f"{name}.srs")
    common.unified_to_singbox_json(filtered, json_path)
    common.run(["sing-box", "rule-set", "compile", "--output", srs_path, json_path])
    return True


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
            print(f"[跳过] {link}：mihomo 官方未提供 mrs 反解工具，srs 无法处理此输入")
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
    if write_domain(domain_part, name, domain_dir):
        wrote.append("Domain")
    if write_ip(ipcidr_part, name, ipcidr_dir):
        wrote.append("IP")

    if wrote:
        print(f"[完成] {name} -> {output_root}/{{domain,ipcidr}}/ ({','.join(wrote)})，共 {len(links)} 个源")
    else:
        print(f"[跳过] {name}：识别不出域名或IP规则")


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
