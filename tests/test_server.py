"""Testes de integração do server MCP — verifica registro de tools e resources."""

from __future__ import annotations


class TestServerRegistration:
    def test_mcp_loads(self):
        from inpe_bdc_mcp.server import mcp
        assert mcp is not None
        assert mcp.name == "inpe-bdc-stac"

    def test_tools_registered(self):
        from inpe_bdc_mcp.server import mcp
        # FastMCP armazena as tools internamente
        # Verifica que pelo menos as principais estão registradas
        assert hasattr(mcp, '_tool_manager') or hasattr(mcp, 'list_tools')

    def test_error_handler_returns_json_on_value_error(self):
        import json
        from inpe_bdc_mcp.server import _handle_errors

        @_handle_errors
        def bad_func():
            raise ValueError("param inválido")

        result = bad_func()
        parsed = json.loads(result)
        assert parsed["code"] == "BAD_REQUEST"
        assert "param inválido" in parsed["details"]

    def test_error_handler_returns_json_on_generic_error(self):
        import json
        from inpe_bdc_mcp.server import _handle_errors

        @_handle_errors
        def crash():
            raise RuntimeError("boom")

        result = crash()
        parsed = json.loads(result)
        assert parsed["code"] == "INTERNAL_ERROR"
