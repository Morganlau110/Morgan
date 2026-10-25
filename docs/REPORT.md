# JSON schema v1.0

顶层：schema_version、generated_at（UTC ISO 8601）、scope、devices、summary。
设备：name、transport、data、errors、findings、bgp_summary、status。

status 优先级 error > critical > warning > healthy。部分采集失败仍保留成功数据与 findings。失败的 BGP 统计为 null。合法零行表允许为空；无预期基线，因此不判断邻居缺失。

findings 含 severity、code、target。代码包括 PORT_DOWN、LAG_UNAVAILABLE、LAG_DEGRADED、BGP_NOT_ESTABLISHED。管理员关闭的端口和 LAG 不告警。

errors 只记录 stage 与异常类型，省略原始输出和异常文本。实际报告仍包含端口描述、邻居地址与 ASN，需要控制访问。

BGP received_sum_per_peer 可能包含重复前缀；active、sent 保存在邻居明细。未建立的会话允许空计数。healthy 只代表本次有限规则通过，不等于完整设备健康。
