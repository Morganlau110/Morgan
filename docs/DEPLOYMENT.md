# 部署

## 本地与容器

使用 Python 3.10+ 在项目根目录按 README 运行；Windows 可用 `py -m sros_audit`。

```bash
docker build -t sros-audit:0.1 .
docker run --rm sros-audit:0.1
```

容器以非 root UID 10001 运行；示例返回码 1。需保留报告时：

```bash
mkdir -p reports
# Linux：让容器用户可以写入专用目录
sudo chown 10001:10001 reports
docker run --rm -v "$PWD/reports:/app/reports" sros-audit:0.1
```

构建需镜像和包源网络。本次未交付预构建镜像。

## SSH 实验室接入

先为实际版本开发 parser adapter；当前模拟格式不适配原生 SR OS。LAG total/minimum 必须从详细状态获得，不应凭摘要推断。使用设备端只读 RBAC 账号；在设备账号会话配置中处理分页，程序不发送会话修改命令。

```bash
python -m pip install '.[ssh]'
```

凭据使用 SSH agent 或受保护的 ~/.ssh 密钥，不放入清单。通过可信渠道核对公钥指纹后配置 ~/.ssh/known_hosts；不要盲目信任 ssh-keyscan。未知或改变的主机密钥会被拒绝。

本地建立 inventory.local.json（已忽略）：

```json
{"devices":[{"name":"LAB-REAL","transport":"ssh","host":"192.0.2.10","username":"audit","port":22}]}
```

```bash
python -m sros_audit --inventory inventory.local.json --allow-ssh --output reports/lab.json
```

示例使用文档地址。三个固定查询为 show port、show lag、show router bgp summary。禁止任意命令输入，无配置接口。连接超时 10 秒，命令通道超时 20 秒，每命令输出上限 2 MB。当前串行、无重试；输出包含设备信息，应保存在访问受控目录。

生产接入前需验证实际输出、分页、LAG 规则、BGP 地址族口径、RBAC、主机密钥拒绝与失败隔离。应用命令白名单不能替代设备权限控制。后续可按版本注册解析器、增加 NETCONF state reader、期望状态和受限并发；配置执行需要独立设计。
