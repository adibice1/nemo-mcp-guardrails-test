import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

github_pat = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
if not github_pat:
    raise RuntimeError('Missing GITHUB_PERSONAL_ACCESS_TOKEN')

client = MultiServerMCPClient({
    'github': {
        'command': 'docker',
        'args': [
            'run', '-i', '--rm',
            '-e', 'GITHUB_PERSONAL_ACCESS_TOKEN',
            '-e', 'GITHUB_READ_ONLY=1',
            '-e', 'GITHUB_TOOLSETS=repos,issues,pull_requests',
            'ghcr.io/github/github-mcp-server',
        ],
        'transport': 'stdio',
        'env': {
            'GITHUB_PERSONAL_ACCESS_TOKEN': github_pat,
            'GITHUB_READ_ONLY': '1',
            'GITHUB_TOOLSETS': 'repos,issues,pull_requests',
        },
    }
})

tools = asyncio.run(client.get_tools())
print('got tools count=', len(tools))
for t in tools:
    print('-', t.name)
