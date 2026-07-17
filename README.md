# Rule Feed

一个用于抓取、转换、托管 mihomo（Clash Meta）与 sing-box 规则集的自动化项目。规则源每天自动更新，编译产物通过 Cloudflare Pages 发布，可直接在自己的代理客户端里订阅使用。

CDN 地址：https://xiaohai-rule.445568.xyz

## 目录结构

```
.
├── .github/workflows/     GitHub Actions 工作流
│   ├── mihomo.yml         编译 mihomo 规则（.yaml/.mrs）
│   ├── singbox.yml        编译 sing-box 规则（.json/.srs）
│   └── deploy-pages.yml   生成浏览页并推送到 Cloudflare Pages
├── script/                构建脚本
│   ├── common.py          规则拉取/解析/统一格式的公共逻辑
│   ├── build_mihomo.py    生成 mihomo 规则
│   ├── build_singbox.py   生成 sing-box 规则
│   └── generate_index.py  生成可浏览的静态首页
├── links/                 规则源列表（改这里就能加规则）
│   ├── links-domain.txt   只含域名规则的源
│   ├── links-ipcidr.txt   只含 IP/CIDR 规则的源
│   └── links-mixed.txt    域名和IP混在一起的源，脚本会自动拆分
├── rule/
│   ├── mihomo/<名字>/     每个规则一个文件夹，装 <名字>_Domain.yaml/.mrs、<名字>_IP.yaml/.mrs
│   └── singbox/<名字>/    每个规则一个文件夹，装 <名字>_Domain.json/.srs、<名字>_IP.json/.srs
├── icon/                  图标/图片素材，推送后可直接在浏览页复制 CDN 直链
└── _headers               Cloudflare Pages 缓存策略配置
```

## 怎么加一条新规则

打开 `links/` 里对应的 txt 文件，每行一条，格式：

```
自定义名字 规则源链接
```

不写名字也行，脚本会用链接里的文件名当名字。支持的规则源类型：

| 前缀 | 说明 |
|---|---|
| （无前缀） | 纯文本规则（Clash txt/list、Meta yaml 等），自动解析 |
| `srs:` | sing-box 编译好的 `.srs` 文件，会反解成统一格式 |
| `json:` | sing-box 规则的 `.json` 源文件 |
| `mrs:` | mihomo 的 `.mrs` 文件（官方暂无反解工具，会被跳过） |
| `adguard:` | AdGuard 格式规则列表 |

三个文件里放的链接，不管写在哪个文件，脚本都会按内容自动识别是域名规则还是 IP 规则，分别写进对应文件里，不用自己纠结该放哪个文件。

## 自动构建 & 部署节奏

- `mihomo.yml`：每天定时构建 mihomo 规则，也可以手动触发（Actions 页面点 `Run workflow`）
- `singbox.yml`：每天定时构建 sing-box 规则，同样支持手动触发
- `deploy-pages.yml`：每 12 小时自动把最新内容推送到 Cloudflare Pages，也可以手动触发

**注意**：规则构建和网站部署是分开的两个流程，互不自动触发。如果你手动改了规则源想立刻看到效果，顺序是：先手动跑一遍 `mihomo.yml`/`singbox.yml`（等两个都跑完），再手动跑一次 `deploy-pages.yml`。

## 怎么用生成的规则

打开 https://445568.xyz ，像逛文件夹一样点进去，例如 `rule/mihomo/google/`，能看到：

- 点文件名：直接打开/预览这个文件（`.md` 文件会渲染成 GitHub 那种排版）
- 点复制按钮：拿到这个文件的 CDN 直链，粘贴到 Clash / mihomo / sing-box 的 `rule-providers` 或 `rule_set` 配置里就能订阅

## 需要配置的 GitHub Secrets

| 名称 | 说明 |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账号 ID |
| `CLOUDFLARE_PAGES` | Cloudflare Pages 项目名 |
