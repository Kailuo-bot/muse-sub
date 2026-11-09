# muse — Clash Meta 订阅配置（只保留美国节点）

Clash Meta (mihomo) 配置，由 Muse 每日自动维护：
抓取公开免费节点源 → 去重 → 连通性筛选 → **只保留美国（US）的节点** → 生成配置推送到本仓库。
地区按服务器 IP 归属判定；CDN 前置节点按节点名标注的国家判定；无法判定地区的不收。
（2026-11-09 起按用户指定改为只收美国，此前为北美/日本/欧洲。）

## 订阅地址（固定不变，二选一）

- jsDelivr 镜像（国内优先试这个）：https://cdn.jsdelivr.net/gh/Kailuo-bot/muse-sub@main/muse.yaml
- GitHub 原始地址：https://raw.githubusercontent.com/Kailuo-bot/muse-sub/main/muse.yaml

## 导入方法（Clash Meta for Android）

配置 → 新建配置 → 从 URL 导入 → 粘贴上面任一地址 → 名称填 muse → 保存并启用。
之后在配置页更新该配置即可拿到最新版；也可以给它开启自动更新（建议间隔 1440 分钟）。

## 说明

- 节点全部来自公开免费聚合源，质量波动大，仅供普通浏览；请勿用于银行、支付等敏感账号。
- 手机端健康检查与「♻️ 自动选择」组会持续剔除失效节点。
