# 版本说明 v1：Agent 底层核心技术官方版图

- 日期：2026-07-13
- 输出目标：客观、全面、详细解释主流 Agent 底层支撑技术，不按借鉴价值或热度排名。
- 权威性规则：主体只使用官方规范、官方仓库、官方 SDK 与官方发布材料；社区内容单独标注。
- 深度冷存：OpenAI Agents SDK、MCP、A2A。
- 冷存提交：OpenAI `8221e424db96c0dd3152f36e6848f9b8c6f10646`；MCP `2807f9d6d8ae2012e09377908f47cff16a2b9489`；A2A `2183794bfb9b67af4aee1be0a0ef726050642873`。
- 边界：A2A 首次冷存时 bundle 生成失败；修复冷存脚本并重试后，源码清单、关键文档、哈希与 `repository.bundle` 均已完整生成。LangGraph、Microsoft Agent Framework、Google ADK、OpenTelemetry 本轮未完整冷存。
- 主要内容：技术分层、MCP、A2A、OpenAI Agents SDK、其他官方运行时、OpenTelemetry、社区观察与生产组合。
