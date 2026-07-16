# sing-box-geosite

在 `links.txt` 添加规则集，生成 **sing-box (srs/json)** 和 **mihomo (mrs/yaml)** 两套规则集——两者是**两个独立的 workflow**，各自单独触发、各自只写自己的目录，互不依赖。

仓库 Settings ----> Actions ----> General ----> Workflow permissions ----> Read and write permissions 勾选上

## 目录 / 脚本 / workflow 对应关系

```
.github/workflows/
  srs.yml   -> 只装 sing-box，跑 rule/build_singbox.py，只写 rule/singbox/
  mrs.yml   -> 装 sing-box + mihomo，跑 rule/build_mihomo.py，只写 rule/mihomo/

rule/
  common.py         # 两边共用的解析库，不直接运行
  build_singbox.py  # srs.yml 调用
  build_mihomo.py   # mrs.yml 调用
  singbox/
    <name>.json   <name>.srs
  mihomo/
    <name>.yaml   <name>.mrs
    <name>-ip.yaml <name>-ip.mrs   # 规则集里含 ip_cidr 时才会有
```

两个 workflow 都能在 Actions 页面手动点 `Run workflow` 单独触发，也都各自有每日 `schedule`；只推送 `links.txt` 或对应脚本改动时才会自动触发（改 `rule/build_singbox.py` 不会触发 `mrs.yml`，反之亦然）。

> `mrs.yml` 里也装了 sing-box——因为 `links.txt` 里的 `srs:`/`adguard:` 类型输入要先靠 `sing-box decompile`/`convert` 才能拿到中间数据，这一步不产出任何 `singbox/` 下的文件，纯粹是内部转换需要。

## links.txt 支持的写法

`links.txt` 只有一份，两个 workflow 共用，每行一个规则源，支持自动识别扩展名，也支持前缀强制指定：

| 写法 | 说明 |
|---|---|
| `https://xxx.yaml` / `.list` / `.txt` | clash yaml / surge / quantumultx 等文本规则，走原有解析逻辑 |
| `https://xxx.json` 或 `json:<url>` | sing-box source json，直接读取 |
| `https://xxx.srs` 或 `srs:<url>` | sing-box 二进制规则集，先 `decompile` 还原再重新生成 |
| `adguard:<url>` | AdGuard filter 格式，走 `sing-box rule-set convert --type adguard` |

同一份 `links.txt`，`srs.yml` 跑起来只出 srs/json，`mrs.yml` 跑起来只出 mrs/yaml，两边互不影响。

### 关于 mrs 的两个限制（上游工具本身的限制）

1. **不支持导入 `.mrs` 作为规则源**：mihomo 官方目前只提供 `convert-ruleset` 单向生成 mrs 的命令，没有反解（decompile）工具，`links.txt` 里放 `.mrs` 链接会被两边脚本自动跳过并打印警告。
2. **mrs 只能装 domain / domain_suffix / ip_cidr**：`mihomo convert-ruleset` 本身只支持 `domain` 和 `ipcidr` 两种 behavior。规则集里如果还有 `domain_keyword`、`domain_regex`、`port` 等类型，这部分内容只会出现在 `singbox/` 下，`mihomo/` 侧会跳过并在日志里提示。

## 规则集源文件写法 eg（供其他 sing-box 配置引用）

```json
{
  "tag": "geosite-wechat",
  "type": "remote",
  "format": "source",
  "url": "https://raw.githubusercontent.com/Toperlock/sing-box-geosite/main/wechat.json",
  "download_detour": "auto"
}
```

mihomo 侧引用示例：

```yaml
rule-providers:
  wechat:
    type: http
    behavior: domain
    format: mrs
    url: "https://raw.githubusercontent.com/<你的用户名>/sing-box-geosite/main/rule/mihomo/WeChat.mrs"
    path: ./ruleset/wechat.mrs
    interval: 86400
```

# 致谢（排名不分先后）

[@izumiChan16](https://github.com/izumiChan16)

[@ifaintad](https://github.com/ifaintad)

[@NobyDa](https://github.com/NobyDa)

[@blackmatrix7](https://github.com/blackmatrix7)

[@DivineEngine](https://github.com/DivineEngine)
