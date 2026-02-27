"""Tests for WISDOM Plugin System."""

import pytest

from wisdom.plugins import WisdomPlugin, PluginManager, hook


class SamplePlugin(WisdomPlugin):
    """Test plugin for unit tests."""
    name = "sample"
    version = "1.0.0"
    description = "A test plugin"

    @hook("pre_process", priority=50)
    def prefix_message(self, value: str, **kwargs) -> str:
        return f"[PROCESSED] {value}"

    @hook("post_process", priority=50)
    def suffix_response(self, value: str, **kwargs) -> str:
        return f"{value} [END]"

    @hook("context_provider")
    def provide_context(self, **kwargs) -> str:
        return "Sample context from plugin"


class AnotherPlugin(WisdomPlugin):
    name = "another"
    version = "0.1.0"

    @hook("pre_process", priority=200)
    def late_process(self, value: str, **kwargs) -> str:
        return value.upper()


class TestPluginManager:
    def setup_method(self):
        self.pm = PluginManager()

    def test_register_plugin(self):
        plugin = SamplePlugin()
        self.pm.register(plugin)
        assert "sample" in [p["name"] for p in self.pm.list_plugins()]

    def test_list_plugins(self):
        self.pm.register(SamplePlugin())
        plugins = self.pm.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "sample"
        assert plugins[0]["version"] == "1.0.0"

    def test_get_plugin(self):
        self.pm.register(SamplePlugin())
        plugin = self.pm.get_plugin("sample")
        assert plugin is not None
        assert plugin.name == "sample"

    def test_unregister_plugin(self):
        self.pm.register(SamplePlugin())
        self.pm.unregister("sample")
        assert self.pm.get_plugin("sample") is None

    def test_duplicate_register_skips(self):
        self.pm.register(SamplePlugin())
        self.pm.register(SamplePlugin())  # Should skip
        assert len(self.pm.list_plugins()) == 1

    def test_enable_disable(self):
        self.pm.register(SamplePlugin())
        assert self.pm.disable("sample")
        plugin = self.pm.get_plugin("sample")
        assert not plugin.enabled
        assert self.pm.enable("sample")
        assert plugin.enabled

    def test_enable_nonexistent(self):
        assert not self.pm.enable("nonexistent")
        assert not self.pm.disable("nonexistent")


class TestPluginHooks:
    def setup_method(self):
        self.pm = PluginManager()
        self.pm.register(SamplePlugin())

    def test_pre_process_hook(self):
        result = self.pm.run_hook("pre_process", "hello")
        assert result == "[PROCESSED] hello"

    def test_post_process_hook(self):
        result = self.pm.run_hook("post_process", "response")
        assert result == "response [END]"

    def test_context_provider_hook(self):
        contexts = self.pm.run_hook("context_provider")
        assert len(contexts) == 1
        assert "Sample context" in contexts[0]

    def test_hook_priority_ordering(self):
        self.pm.register(AnotherPlugin())
        # SamplePlugin has priority 50, AnotherPlugin has priority 200
        # SamplePlugin runs first, then AnotherPlugin
        result = self.pm.run_hook("pre_process", "hello")
        assert result == "[PROCESSED] HELLO"

    def test_disabled_plugin_hooks_skipped(self):
        self.pm.disable("sample")
        result = self.pm.run_hook("pre_process", "hello")
        assert result == "hello"  # Unchanged

    def test_invalid_hook_point(self):
        result = self.pm.run_hook("invalid_hook", "test")
        assert result == "test"

    def test_ui_component_hook(self):
        # ui_component hooks don't return values
        result = self.pm.run_hook("ui_component")
        assert result is None


class TestWisdomPlugin:
    def test_plugin_info(self):
        plugin = SamplePlugin()
        info = plugin.get_info()
        assert info["name"] == "sample"
        assert info["version"] == "1.0.0"
        assert info["enabled"] is True

    def test_on_load_on_unload(self):
        plugin = SamplePlugin()
        plugin.on_load()  # Should not error
        plugin.on_unload()  # Should not error


class TestPluginDiscovery:
    def test_discover_plugins(self):
        pm = PluginManager()
        count = pm.discover_plugins()
        # Should find the example_plugin.py
        assert count >= 1
        assert any(p["name"] == "learning_tips" for p in pm.list_plugins())
