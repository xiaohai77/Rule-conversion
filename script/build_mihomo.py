import os
import concurrent.futures
import tempfile
from collections import defaultdict

import common

# 手动维护的规则源（links-domain / links-ipcidr / links-mixed）
# 输出到 rules/mihomo
RULES_LINKS_FILES = [
    "../links/links-domain.txt",
    "../links/links-ipcidr.txt",
    "../links/links-mixed.txt",
]
RULES_OUTPUT_ROOT = "../rules/mihomo"

# 自动从 MetaCubeX/meta-rules-dat 拉取的全量 geosite+geoip（links-meta.txt）
# 输出到 geo-data/mihomo，与手动维护的规则分开存放
GEO_LINKS_FILES = [
    "../links/links-meta.txt",
]
GEO_OUTPUT_ROOT = "../geo-data/mihomo"


def build_domain_files(filtered, name, out_dir):
    domain_lines = sorted(filtered.get('domain', set()))
    domain_lines += sorted('+.' + d.lstrip('.') for d in filtered.get('domain_suffix', set()))
    if not domain_lines:
        return False
    os.makedirs(out_dir, exist_ok=True)
    yaml_path = os.path.join(out_dir, f"{name}_Domain.yaml")
    mrs_path = os.path.join(out_dir, f"{name}_Domain.mrs")
    common.yaml.safe_dump({'payload': domain_lines}, open(yaml_path, 'w', encoding='utf-8'), allow_unicode=True)
    common.run(["mihomo", "convert-ruleset", "domain", "yaml", yaml_path, mrs_path])
    return True


def build_ip_files(filtered, name, out_dir):
    ip_lines = sorted(filtered.get('ip_cidr', set()))
    if not ip_lines:
        return False
    os.makedirs(out_dir, exist_ok=True)
    yaml_path = os.path.join(out_dir, f"{name}_IP.yaml")
    mrs_path = os.path.join(out_dir, f"{name}_IP.mrs")
    common.yaml.safe_dump({'payload': ip_lines}, open(yaml_path, 'w', encoding='utf-8'), allow_unicode=True)
    common.run(["mihomo", "convert-ruleset", "ipcidr", "yaml", yaml_path, mrs_path])
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
            print(f"[跳过] {link}：mihomo 官方未提供 mrs 反解工具，无法作为规则源导入")
            continue
        if not unified:
            print(f"[跳过] {link}：未解析出任何规则")
            continue
        if name in ('google', 'twitter'):
            print(f"[调试] {name} <- {link} 解析出字段: { {k: len(v) for k, v in unified.items()} }")
        unified_list.append(unified)

    if not unified_list:
        return

    unified = merge_unified(unified_list)
    domain_part, ipcidr_part, leftover = common.split_mixed_unified(unified)
    if leftover:
        print(f"[提示] {name}: 以下字段既不算域名也不算IP，已跳过: {leftover}")

    mrs_unsupported = set(domain_part.keys()) - common.MIHOMO_MRS_SUPPORTED
    if mrs_unsupported:
        print(f"[提示] {name}: 以下字段 mihomo mrs 不支持，已跳过: {sorted(mrs_unsupported)}")

    out_dir = os.path.join(output_root, name)
    wrote = []
    if build_domain_files(domain_part, name, out_dir):
        wrote.append("Domain")
    if build_ip_files(ipcidr_part, name, out_dir):
        wrote.append("IP")
    if common.write_qx_list(domain_part, ipcidr_part, os.path.join(out_dir, f"{name}.list")):
        wrote.append("List")

    if wrote:
        print(f"[完成] {name} -> {output_root}/{name}/ ({','.join(wrote)})，共 {len(links)} 个源")
    else:
        print(f"[跳过] {name}：过滤后没有可生成 mrs 的规则")


def run_group(links_files, output_root, work_dir):
    os.makedirs(output_root, exist_ok=True)
    groups = group_links(links_files)

    multi = {name: len(links) for name, links in groups.items() if len(links) > 1}
    print(f"[分组统计] {output_root}: 共 {len(groups)} 个 name，其中 {len(multi)} 个有多个来源")
    if 'google' in groups:
        print(f"[分组统计] google 的来源: {groups['google']}")
    if 'twitter' in groups:
        print(f"[分组统计] twitter 的来源: {groups['twitter']}")

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
