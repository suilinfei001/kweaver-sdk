# exec - Execution Factory Commands

Operator、Toolbox、MCP Server 的管理与导入导出。

## 子命令

| 子命令 | 说明 |
|--------|------|
| `operator` | 算子管理 |
| `toolbox` | 工具箱管理 |
| `mcp` | MCP Server 管理 |
| `impex` | 导入导出 |

## operator

```bash
kweaver exec operator list [options]     # 列出算子（默认 published）
kweaver exec operator get <id> [options]
kweaver exec operator register [options]
kweaver exec operator edit <id> <version> [options]
kweaver exec operator delete [options]
kweaver exec operator status [options]
kweaver exec operator debug [options]
kweaver exec operator history <id> [options]
kweaver exec operator market [options]
kweaver exec operator market-get <id>
kweaver exec operator categories
kweaver exec operator internal-register [options]
```

**Options:** `-bd, --biz-domain`, `--pretty`, `--compact`

**List 默认:** `page=1`, `page_size=10`, `status=published`

## toolbox

```bash
kweaver exec toolbox list [options]        # 列出工具箱（默认 published）
kweaver exec toolbox get <box_id> [options]
kweaver exec toolbox create [options]
kweaver exec toolbox update <box_id> [options]
kweaver exec toolbox delete <box_id>
kweaver exec toolbox status <box_id> [options]
kweaver exec toolbox tool-list <box_id> [options]
kweaver exec toolbox tool-get <box_id> <tool_id>
kweaver exec toolbox tool-create <box_id> [options]
kweaver exec toolbox tool-update <box_id> <tool_id> [options]
kweaver exec toolbox tool-status <box_id> [options]
kweaver exec toolbox tool-delete <box_id> <tool_id>
kweaver exec toolbox tool-batch-delete <box_id> [options]
kweaver exec toolbox convert [options]
kweaver exec toolbox market [options]
kweaver exec toolbox market-get <box_id>
kweaver exec toolbox categories
kweaver exec toolbox proxy <box_id> <tool_id> [options]
kweaver exec toolbox debug <box_id> <tool_id> [options]
kweaver exec toolbox function-execute [options]
kweaver exec toolbox function-ai-generate [options]
kweaver exec toolbox prompt-templates
kweaver exec toolbox dependencies-install [options]
kweaver exec toolbox dependencies-versions <package>
```

**Options:** `-bd, --biz-domain`, `--pretty`, `--compact`

**List 默认:** `page=1`, `page_size=10`, `status=published`

## mcp

```bash
kweaver exec mcp list [options]          # 列出 MCP Server（默认 published）
kweaver exec mcp get <mcp_id> [options]
kweaver exec mcp create [options]
kweaver exec mcp update <mcp_id> [options]
kweaver exec mcp delete <mcp_id>
kweaver exec mcp status <mcp_id> [options]
kweaver exec mcp parse-sse [options]
kweaver exec mcp debug <mcp_id> <tool_name> [options]
kweaver exec mcp market [options]
kweaver exec mcp market-get <mcp_id>
kweaver exec mcp categories
kweaver exec mcp proxy-call <mcp_id> [options]
kweaver exec mcp proxy-list <mcp_id>
```

**Options:** `-bd, --biz-domain`, `--pretty`, `--compact`

**List 默认:** `page=1`, `page_size=10`, `status=published`

## impex

```bash
kweaver exec impex export <type> <id> [options]   # 导出单个组件
kweaver exec impex import <type> [options]          # 导入组件
```

**Arguments:**
- `type`: `operator` | `toolbox` | `mcp`
- `id`: 组件 ID（export 需要）

**Options:** `-bd, --biz-domain`, `--pretty`, `--compact`

## 分页参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--page` | 1 | 页码 |
| `--page-size` | 10 | 每页数量 |

## 状态过滤

List 接口默认 `status=published`，可指定其他状态：
- `--status enabled`
- `--status disabled`
- `--status published`