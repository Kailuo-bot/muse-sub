# muse — Clash Meta 订阅配置

Clash Meta (mihomo) 配置文件，由 Muse 每日自动维护：抓取公开免费节点源 → 去重 → 连通性筛选 → 生成配置，死节点不进配置；配置内的健康检查与自动选择组会在手机端持续剔除失效节点。

## 订阅地址（固定不变，二选一）

- jsDelivr 镜像（国内优先试这个）：https://cdn.jsdelivr.net/gh/Kailuo-bot/muse-sub@main/muse.yaml
- GitHub 原始地址：https://raw.githubusercontent.com/Kailuo-bot/muse-sub/main/muse.yaml

## 导入方法（Clash Meta for Android）

配置 → 新建配置 → 从 URL 导入 → 粘贴上面任一地址 → 名称填 muse → 保存并启用。
之后在配置页点该配置的更新按钮，即可拉取最新版；也可以给该配置开启自动更新。

## 说明

- 节点全部来自公开免费聚合源，质量波动大，仅供普通浏览；请勿用于银行、支付等敏感账号。
- 配置每 6 小时通过 proxy-providers 自行拉新源数据，本仓库文件每日由 Muse 复检更新。
