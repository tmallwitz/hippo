---
name: multi-tenant-config
description: Pattern for resolving per-instance config from prefixed env vars with a shared unprefixed fallback, using pydantic-settings.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-06-phase7-multi-bot-deployment
---

# Multi-Tenant Config via Prefixed Env Vars

When one process host runs multiple named instances (e.g. multiple bots), resolve config with two pydantic-settings source layers:

1. **Per-instance prefix** — `{INSTANCE_NAME}_FIELD_NAME` (e.g. `ALICE_TELEGRAM_BOT_TOKEN`)
2. **Shared fallback** — unprefixed `FIELD_NAME` (e.g. `TELEGRAM_BOT_TOKEN`)

```python
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource

class HippoConfig(BaseSettings):
    telegram_bot_token: str
    vault_path: str
    ...

def get_config(bot_name: str) -> HippoConfig:
    prefix = bot_name.upper() + "_"

    class _BotConfig(HippoConfig):
        @classmethod
        def settings_customise_sources(
            cls, settings_cls, **kwargs
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return (
                EnvSettingsSource(settings_cls, env_prefix=prefix),
                EnvSettingsSource(settings_cls, env_prefix=""),
            )

    return _BotConfig(hippo_bot_name=bot_name)
```

**Rules:**
- Per-bot override wins; shared setting is the fallback.
- Never parse env vars manually — rely on pydantic's type coercion.
- Validate the instance name early (regex allowlist) before constructing config, to produce a clear error for typos.
- Single-instance users need only add the prefix to their existing `.env`; unprefixed vars continue to work as the fallback.
