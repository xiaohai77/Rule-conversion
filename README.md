# Rule Feed

自动抓取、转换并发布代理规则集。

支持生成：

- Mihomo / Clash Meta
  - YAML
  - MRS(rule-set)

- sing-box
  - JSON
  - SRS(rule-set)

项目通过 GitHub Actions 自动执行规则抓取、转换和发布，可用于 Mihomo、Clash Meta、sing-box 等客户端。

## 功能特点

- 自动拉取远程规则源
- 支持域名规则和 IP-CIDR 规则
- 自动转换不同客户端格式
- 支持自定义规则源
- GitHub Actions 自动构建
- 支持 Cloudflare Pages 自动部署

## 使用方式

Fork 本仓库后，根据需求修改规则源文件：

```
links-domain.txt
links-ipcidr.txt
links-mixed.txt
```

添加需要转换的规则集链接，提交后去触发 GitHub Actions 会自动生成对应规则文件。

### 规则文件说明

|文件|说明|
|-|-|
|links-domain.txt|用于添加域名类规则集|
|links-ipcidr.txt|用于添加 IP-CIDR 类规则集|
|links-mixed.txt|用于添加同时包含域名和 IP-CIDR 的混合规则集|

## GitHub Actions 权限设置

Fork 仓库后，需要开启 Actions 写入权限：

```
Settings → Actions → General → Workflow permissions
```

选择：

```
Read and write permissions
```

并保存。

否则 GitHub Actions 无法自动提交或发布生成的规则文件。

## Cloudflare Pages 部署

如果需要自动发布到 Cloudflare Pages，需要在 GitHub 仓库：

```
Settings → Secrets and variables → Actions
```

添加以下变量：

```
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_PROJECT_NAME
```

变量说明：

|变量|作用|
|-|-|
|CLOUDFLARE_API_TOKEN|Cloudflare API Token，用于授权部署|
|CLOUDFLARE_ACCOUNT_ID|Cloudflare 账户 ID|
|CLOUDFLARE_PROJECT_NAME|Cloudflare Pages 项目名称|

完成配置后，GitHub Actions 会自动将生成的规则文件部署到 Cloudflare Pages。

## 注意事项

- Mihomo MRS 格式不支持反解。

## 支持客户端

- Mihomo
- Clash Meta
- sing-box

生成后的规则文件可直接用于：

- rule-providers
- rule-set

## License

MIT
