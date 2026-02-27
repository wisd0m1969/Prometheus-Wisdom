"""WISDOM Plugin System — extensible plugin architecture.

Plugins can hook into the WISDOM pipeline at defined extension points:
- pre_process: Before message enters the pipeline
- post_process: After response is generated
- context_provider: Adds context to RAG retrieval
- ui_component: Adds UI elements to Streamlit

Example plugin:
    from wisdom.plugins import WisdomPlugin, hook

    class MyPlugin(WisdomPlugin):
        name = "my_plugin"
        version = "1.0.0"

        @hook("post_process")
        def add_footer(self, response: str, **kwargs) -> str:
            return response + "\\n\\n---\\nPowered by MyPlugin"
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

__all__ = ["WisdomPlugin", "PluginManager", "hook"]

logger = logging.getLogger(__name__)


@dataclass
class HookRegistration:
    """Metadata for a registered hook function."""
    hook_point: str
    priority: int = 100
    func: Callable | None = None


def hook(hook_point: str, priority: int = 100) -> Callable:
    """Decorator to register a method as a plugin hook.

    Args:
        hook_point: One of 'pre_process', 'post_process', 'context_provider', 'ui_component'.
        priority: Lower numbers run first. Default 100.
    """
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_wisdom_hooks"):
            func._wisdom_hooks = []
        func._wisdom_hooks.append(HookRegistration(hook_point=hook_point, priority=priority))
        return func
    return decorator


class WisdomPlugin(ABC):
    """Base class for all WISDOM plugins.

    Subclass this and use the @hook decorator to register handlers.
    """

    name: str = "unnamed_plugin"
    version: str = "0.0.0"
    description: str = ""
    enabled: bool = True

    def on_load(self) -> None:
        """Called when the plugin is loaded. Override for setup."""
        pass

    def on_unload(self) -> None:
        """Called when the plugin is unloaded. Override for cleanup."""
        pass

    def get_info(self) -> dict:
        """Return plugin metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
        }


class PluginManager:
    """Discovers, loads, and manages WISDOM plugins.

    Plugins are loaded from the plugins/ directory or registered manually.
    """

    VALID_HOOKS = {"pre_process", "post_process", "context_provider", "ui_component"}

    def __init__(self) -> None:
        self._plugins: dict[str, WisdomPlugin] = {}
        self._hooks: dict[str, list[tuple[int, Callable, WisdomPlugin]]] = {
            h: [] for h in self.VALID_HOOKS
        }

    def register(self, plugin: WisdomPlugin) -> None:
        """Register a plugin instance."""
        if plugin.name in self._plugins:
            logger.warning("Plugin '%s' already registered, skipping", plugin.name)
            return

        self._plugins[plugin.name] = plugin

        # Discover @hook decorated methods
        for attr_name in dir(plugin):
            attr = getattr(plugin, attr_name, None)
            if callable(attr) and hasattr(attr, "_wisdom_hooks"):
                for reg in attr._wisdom_hooks:
                    if reg.hook_point in self.VALID_HOOKS:
                        self._hooks[reg.hook_point].append((reg.priority, attr, plugin))
                        self._hooks[reg.hook_point].sort(key=lambda x: x[0])

        plugin.on_load()
        logger.info("Plugin loaded: %s v%s", plugin.name, plugin.version)

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name."""
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.on_unload()
            # Remove hooks
            for hook_list in self._hooks.values():
                hook_list[:] = [(p, f, pl) for p, f, pl in hook_list if pl.name != name]
            logger.info("Plugin unloaded: %s", name)

    def discover_plugins(self, plugins_dir: str | Path | None = None) -> int:
        """Discover and load plugins from a directory.

        Each .py file in the directory is checked for WisdomPlugin subclasses.

        Returns:
            Number of plugins loaded.
        """
        if plugins_dir is None:
            plugins_dir = Path(__file__).parent
        else:
            plugins_dir = Path(plugins_dir)

        count = 0
        for py_file in plugins_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                module_name = f"wisdom.plugins.{py_file.stem}"
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, WisdomPlugin)
                        and attr is not WisdomPlugin
                    ):
                        instance = attr()
                        self.register(instance)
                        count += 1
            except Exception as e:
                logger.warning("Failed to load plugin from %s: %s", py_file, e)

        return count

    def run_hook(self, hook_point: str, value: Any = None, **kwargs) -> Any:
        """Run all registered handlers for a hook point.

        For pre_process/post_process: chains the value through handlers.
        For context_provider: collects all returned strings.
        For ui_component: calls each handler (no return value).
        """
        if hook_point not in self.VALID_HOOKS:
            return value

        handlers = self._hooks.get(hook_point, [])

        if hook_point in ("pre_process", "post_process"):
            for _, handler, plugin in handlers:
                if plugin.enabled:
                    try:
                        result = handler(value, **kwargs)
                        if result is not None:
                            value = result
                    except Exception as e:
                        logger.warning("Plugin hook error (%s.%s): %s", plugin.name, hook_point, e)
            return value

        if hook_point == "context_provider":
            contexts = []
            for _, handler, plugin in handlers:
                if plugin.enabled:
                    try:
                        ctx = handler(**kwargs)
                        if ctx:
                            contexts.append(ctx)
                    except Exception:
                        pass
            return contexts

        if hook_point == "ui_component":
            for _, handler, plugin in handlers:
                if plugin.enabled:
                    try:
                        handler(**kwargs)
                    except Exception:
                        pass

        return value

    def list_plugins(self) -> list[dict]:
        """List all registered plugins."""
        return [p.get_info() for p in self._plugins.values()]

    def get_plugin(self, name: str) -> WisdomPlugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def enable(self, name: str) -> bool:
        """Enable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin.enabled = False
            return True
        return False
