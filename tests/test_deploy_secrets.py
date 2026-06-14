from pathlib import Path

import pytest
from unittest.mock import AsyncMock, patch

from tinyagentos.deployer import deploy_agent, DeployRequest, _secret_env_name


def _req(**overrides) -> DeployRequest:
    defaults = dict(
        name="test",
        framework="smolagents",
        model=None,
        data_dir=Path("/tmp/taos-test-data"),
    )
    defaults.update(overrides)
    return DeployRequest(**defaults)


class FakeSecretsStore:
    """Minimal stand-in for SecretsStore.get_agent_secrets."""

    def __init__(self, secrets):
        self._secrets = secrets
        self.calls = []

    async def get_agent_secrets(self, agent_name):
        self.calls.append(agent_name)
        return list(self._secrets)


async def _run_deploy(req, tmp_path):
    async def mock_exec(name, cmd, **kwargs):
        if "hostname -I" in " ".join(cmd):
            return (0, "10.0.0.5")
        return (0, "ok")

    with patch("tinyagentos.deployer.create_container", new_callable=AsyncMock) as mock_create, \
         patch("tinyagentos.deployer.exec_in_container", side_effect=mock_exec), \
         patch("tinyagentos.deployer.push_file", new_callable=AsyncMock, return_value=(0, "")), \
         patch("tinyagentos.deployer.add_proxy_device", new_callable=AsyncMock, return_value={"success": True, "output": ""}):
        mock_create.return_value = {"success": True, "name": "taos-agent-test"}
        result = await deploy_agent(req)
        assert result["success"] is True
        return mock_create.call_args.kwargs["env"]


class TestSecretEnvName:
    def test_exact_passthrough(self):
        assert _secret_env_name("OPENROUTER_API_KEY") == "OPENROUTER_API_KEY"

    def test_lowercase_and_spaces(self):
        assert _secret_env_name("my secret 2") == "MY_SECRET_2"

    def test_special_chars(self):
        assert _secret_env_name("api-key.v1") == "API_KEY_V1"

    def test_leading_digit_prefixed(self):
        assert _secret_env_name("1password") == "_1PASSWORD"


class TestDeploySecretsInjection:
    @pytest.mark.asyncio
    async def test_injects_granted_secrets(self, tmp_path):
        store = FakeSecretsStore([
            {"name": "OPENROUTER_API_KEY", "value": "sk-xxx"},
            {"name": "my secret 2", "value": "v2"},
        ])
        req = _req(data_dir=tmp_path, secrets_store=store)
        env = await _run_deploy(req, tmp_path)

        assert env["OPENROUTER_API_KEY"] == "sk-xxx"
        assert env["MY_SECRET_2"] == "v2"
        assert store.calls == ["test"]

    @pytest.mark.asyncio
    async def test_collision_does_not_clobber_platform_var(self, tmp_path):
        # LITELLM_API_KEY is a platform var the deployer always sets (default "").
        store = FakeSecretsStore([
            {"name": "LITELLM_API_KEY", "value": "evil-override"},
        ])
        req = _req(data_dir=tmp_path, secrets_store=store)
        env = await _run_deploy(req, tmp_path)

        assert env["LITELLM_API_KEY"] != "evil-override"

    @pytest.mark.asyncio
    async def test_no_secrets_store_behaves_as_before(self, tmp_path):
        req = _req(data_dir=tmp_path)  # secrets_store defaults to None
        env = await _run_deploy(req, tmp_path)

        # No injected secret; platform vars still present.
        assert env["TAOS_AGENT_NAME"] == "test"
        assert "OPENROUTER_API_KEY" not in env
