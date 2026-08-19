import asyncio

import pytest

from horde.tools.base import ReconTool, ToolContext


class FixedTool(ReconTool):
    name = "fixed"

    async def execute(self, target, options, context):
        return None


@pytest.mark.asyncio
async def test_subprocess_helper_does_not_use_shell():
    result = await FixedTool.run_executable("/bin/printf", ["%s", "ok"], ToolContext())
    assert result.stdout == "ok"


def test_nul_arguments_rejected():
    with pytest.raises(ValueError):
        asyncio.run(FixedTool.run_executable("/bin/printf", ["bad\x00"], ToolContext()))
