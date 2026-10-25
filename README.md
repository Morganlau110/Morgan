# Nokia 7750 SR OS 只读巡检 v0.1

Python 3.10+ 模块化原型。默认使用虚构设备，无需凭据、网络或第三方依赖。

## 运行

在项目根目录执行：

```bash
python3 -m sros_audit --inventory examples/inventory.json --output reports/audit.json
python3 -m unittest discover -s tests -v
```

示例包含健康和故障设备。巡检返回 **1 是预期结果**，故障设备存在端口 down、LAG 成员减少、BGP Idle。退出码：0=本次检查无异常，1=warning/critical，2=输入输出或采集错误。生成 JSON 报告默认仅文件所有者可读写。

可选安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
sros-audit --inventory examples/inventory.json
```

## 已实现

设备清单校验、模拟/SSH 采集、端口状态、LAG 成员及最小成员数检查、BGP 邻居状态及接收/活跃/发送路由统计、远端 ASN 清单、基础健康规则、错误隔离和 JSON 报告。NETCONF、配置审核、MOP 仅预留接口，无配置下发。

**兼容边界：examples/mock 是简化模拟格式，不是 Nokia 原生 CLI 输出。** 当前解析器只支持这个明确的 fixture profile，未知格式或截断输出将返回 error。SSH 连接模块已实现，但尚未验证真实设备端到端流程。接入 SR OS 前必须根据实际版本及 Classic/MD-CLI 的脱敏输出增加解析适配器与回归测试，不能直接用于生产。

范围仅 base router，暂不覆盖 VPRN、多地址族明细、日志分析、Web UI、调度与高并发。received_sum_per_peer 是每邻居接收数量之和，可能重复，**不是唯一前缀数**。没有本机 ASN，remote_asns 不等同于外部 AS。无预期邻居基线，合法空表不会告警。

| 模块 | 职责 |
| --- | --- |
| inventory.py | JSON 清单、去重、路径与参数校验 |
| transport.py | Transport 接口、命令白名单、mock、SSH |
| parsers.py | 严格表格解析与截断检测 |
| health.py | 健康规则 |
| runner.py | 批量编排、错误隔离、统计 |
| cli.py | CLI、原子报告写入、退出码 |
| extensions.py | NETCONF/配置审核/MOP 接口 |

参见 [部署说明](docs/DEPLOYMENT.md)、[报告说明](docs/REPORT.md)。

## 导入 GitHub

空仓库中使用解压后的源码，而不是提交 ZIP：

```bash
git init -b main
git add .
git diff --cached --stat
git commit -m "Initialize read-only SR OS audit prototype"
git remote add origin https://github.com/Morganlau110/Morgan.git
git push -u origin main
```

已有代码时先 clone 再复制并审查差异，不要 force push。公开仓库只存虚构数据；真实清单、输出、报告和密钥不应提交。GitHub Actions 提供 Python 3.10/3.12/3.13 测试矩阵，其执行结果以 Actions 页面为准。
