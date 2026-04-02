"""CLI: agent commands — list, chat."""

from __future__ import annotations

import json
from pathlib import Path

import click

from kweaver.cli._helpers import handle_errors, make_client, pp


@click.group("agent")
def agent_group() -> None:
    """Manage Decision Agents."""


@agent_group.command("list")
@click.option("--keyword", default=None, help="Filter by keyword.")
@click.option("--offset", default=0, type=int, help="Pagination offset (default: 0).")
@click.option("--limit", default=50, type=int, help="Max items to return (default: 50).")
@click.option("--category-id", default=None, help="Filter by category ID.")
@click.option("--status", default=None, help="Filter by status (e.g. published, draft).")
@click.option("--verbose", "-v", is_flag=True, help="Show full JSON response.")
@handle_errors
def list_agents(
    keyword: str | None,
    offset: int,
    limit: int,
    category_id: str | None,
    status: str | None,
    verbose: bool,
) -> None:
    """List published agents."""
    client = make_client()
    agents = client.agents.list(keyword=keyword, status=status, offset=offset, limit=limit)
    if category_id:
        agents = [a for a in agents if category_id in getattr(a, "category_ids", [])]
    if verbose:
        pp([a.model_dump() for a in agents])
    else:
        simplified = [
            {"name": a.name, "id": a.id, "description": a.description or ""}
            for a in agents
        ]
        pp(simplified)


@agent_group.command("get")
@click.argument("agent_id")
@click.option("--verbose", "-v", is_flag=True, help="Show full JSON response.")
@click.option("--save-config", help="保存配置到文件（自动添加时间戳）")
@handle_errors
def get_agent(agent_id: str, verbose: bool, save_config: str | None) -> None:
    """Get agent details."""
    from kweaver.cli._helpers import _generate_timestamped_path

    client = make_client()
    agent = client.agents.get(agent_id)

    if save_config and agent.config:
        timestamped_path = _generate_timestamped_path(save_config)
        Path(timestamped_path).parent.mkdir(parents=True, exist_ok=True)
        Path(timestamped_path).write_text(json.dumps(agent.config, indent=2), encoding="utf-8")
        click.echo(timestamped_path)
        return

    if verbose:
        pp(agent.model_dump())
    else:
        simplified = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description or "",
            "status": agent.status,
            "kn_ids": agent.kn_ids,
        }
        pp(simplified)


@agent_group.command("chat")
@click.argument("agent_id")
@click.option("-m", "--message", required=True, help="Message to send.")
@click.option("--conversation-id", default=None, help="Continue a conversation.")
@handle_errors
def chat(agent_id: str, message: str, conversation_id: str | None) -> None:
    """Chat with a Decision Agent."""
    client = make_client()

    msg = client.conversations.send_message(
        agent_id=agent_id,
        conversation_id=conversation_id or "",
        content=message,
    )

    click.echo(f"\n{msg.content}")

    if msg.references:
        click.echo("\nReferences:")
        for ref in msg.references:
            click.echo(f"  - [{ref.score:.2f}] {ref.source}: {ref.content[:100]}")

    if msg.conversation_id:
        click.echo("", err=True)
        click.echo(
            "To continue this conversation, rerun the command with --conversation-id:",
            err=True,
        )
        click.echo(
            f'kweaver agent chat {agent_id} -m "{{你的下一轮问题}}" --conversation-id {msg.conversation_id}',
            err=True,
        )


@agent_group.command("sessions")
@click.argument("agent_id")
@handle_errors
def sessions(agent_id: str) -> None:
    """List all conversations for an agent."""
    client = make_client()
    convs = client.conversations.list(agent_id=agent_id)
    pp([c.model_dump() for c in convs])


@agent_group.command("history")
@click.argument("conversation_id")
@click.option("--limit", default=None, type=int, help="Max messages to return.")
@handle_errors
def history(conversation_id: str, limit: int | None) -> None:
    """Show message history for a conversation."""
    client = make_client()
    messages = client.conversations.list_messages(conversation_id, limit=limit)
    pp([m.model_dump() for m in messages])


@agent_group.command("trace")
@click.argument("conversation_id")
@click.option("--compact", is_flag=True, help="Compact JSON output.")
@handle_errors
def trace(conversation_id: str, compact: bool) -> None:
    """Get trace data for a conversation."""
    client = make_client()
    data = client.conversations.get_traces_by_conversation(conversation_id)
    pp(data, compact=compact)


@agent_group.command("personal-list")
@click.option("--keyword", help="过滤名称")
@click.option("--size", default=48, type=int, help="返回数量")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def list_personal_agents(
    keyword: str | None,
    size: int,
    verbose: bool,
) -> None:
    """列出私人空间的 Agent。"""
    client = make_client()
    agents = client.agents.list_personal(keyword=keyword, size=size)
    if verbose:
        pp([a.model_dump() for a in agents])
    else:
        simplified = [{"name": a.name, "id": a.id, "description": a.description or ""} for a in agents]
        pp(simplified)


@agent_group.command("category-list")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def list_categories(verbose: bool) -> None:
    """列出 Agent 分类。"""
    client = make_client()
    categories = client.agents.list_categories()
    if verbose:
        pp([c.model_dump() for c in categories])
    else:
        simplified = [{"name": c.name, "id": c.id} for c in categories]
        pp(simplified)


@agent_group.command("template-list")
@click.option("--category-id", help="分类ID")
@click.option("--keyword", help="过滤名称")
@click.option("--size", default=48, type=int, help="返回数量")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def list_templates(
    category_id: str | None,
    keyword: str | None,
    size: int,
    verbose: bool,
) -> None:
    """列出已发布的 Agent 模板。"""
    client = make_client()
    templates = client.agents.list_templates(
        keyword=keyword,
        category_id=category_id,
        size=size,
    )
    if verbose:
        pp([t.model_dump() for t in templates])
    else:
        simplified = [{"name": t.name, "id": t.id, "description": t.description or ""} for t in templates]
        pp(simplified)


@agent_group.command("template-get")
@click.argument("template_id")
@click.option("--save-config", help="保存配置到文件（自动添加时间戳）")
@click.option("--verbose", "-v", is_flag=True, help="显示完整JSON响应")
@handle_errors
def get_template(template_id: str, save_config: str | None, verbose: bool) -> None:
    """获取已发布的 Agent 模板详情。"""
    from kweaver.cli._helpers import _generate_timestamped_path

    client = make_client()
    template = client.agents.get_template(template_id)

    if save_config and template.config:
        timestamped_path = _generate_timestamped_path(save_config)
        Path(timestamped_path).parent.mkdir(parents=True, exist_ok=True)
        Path(timestamped_path).write_text(json.dumps(template.config, indent=2), encoding="utf-8")
        click.echo(timestamped_path)
        return

    if verbose:
        pp(template.model_dump())
    else:
        simplified = {
            "id": template.id,
            "name": template.name,
            "description": template.description or "",
            "config": template.config,
        }
        pp(simplified)


@agent_group.command("update")
@click.argument("agent_id")
@click.option("--name", help="Agent名称")
@click.option("--profile", help="Agent描述")
@click.option("--system-prompt", help="系统提示词")
@click.option("--knowledge-network-id", help="业务知识网络ID")
@click.option("--config-path", help="配置文件路径")
@handle_errors
def update_agent(
    agent_id: str,
    name: str | None,
    profile: str | None,
    system_prompt: str | None,
    knowledge_network_id: str | None,
    config_path: str | None,
) -> None:
    """更新一个 Agent。"""
    from kweaver.cli._helpers import _generate_timestamped_path

    client = make_client()

    # 获取当前 Agent 配置
    current = client.agents.get(agent_id)
    current_dict = current.model_dump()

    # 如果指定了 config-path，从文件读取配置
    if config_path:
        with open(config_path) as f:
            config = json.load(f)
        current_dict["config"] = config

    # 更新字段
    if name:
        current_dict["name"] = name
    if profile:
        current_dict["profile"] = profile
    if system_prompt is not None:
        current_dict.setdefault("config", {})["system_prompt"] = system_prompt

    # 更新知识网络配置
    if knowledge_network_id:
        current_dict.setdefault("config", {}).setdefault("data_source", {})["knowledge_network"] = [
            {"knowledge_network_id": knowledge_network_id, "knowledge_network_name": ""}
        ]

    # 调用 update API
    client.agents.update(agent_id, current_dict)
    click.echo(f"Agent {agent_id} updated.")
