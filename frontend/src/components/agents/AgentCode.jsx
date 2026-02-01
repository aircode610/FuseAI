/**
 * AgentCode Component
 * Code tab: shows generated main.py from API when available, else placeholder.
 */

import { useState, useEffect, useMemo } from 'react';
import { Download, Copy, ChevronDown, ChevronRight, FileCode, FileJson, FileText } from 'lucide-react';
import { Card, CardHeader, CardBody, Button } from '../common';
import agentService from '../../services/agentService';
import './AgentCode.css';

export function AgentCode({ agent }) {
  const [activeFile, setActiveFile] = useState('main.py');
  const [expandedFolders, setExpandedFolders] = useState({ root: true });
  const [fetchedCode, setFetchedCode] = useState(null);
  const [fetchedFiles, setFetchedFiles] = useState(null);

  useEffect(() => {
    if (!agent?.id) return;
    agentService.getAgentCode(agent.id)
      .then((res) => {
        setFetchedCode(res?.code ?? null);
        setFetchedFiles(res?.files ?? null);
      })
      .catch(() => {
        setFetchedCode(null);
        setFetchedFiles(null);
      });
  }, [agent?.id]);

  const placeholderMain = `from fastapi import FastAPI, HTTPException, Header
from typing import Optional
import os

app = FastAPI(title="${agent?.name || 'FuseAI Agent'}")

# Configuration
API_KEY = os.getenv("API_KEY")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/execute")
async def execute(
    payload: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    ${agent?.description || 'On-demand API endpoint'}
    """
    try:
        # Extract data from payload
        card_name = payload.get("card_name", "Unknown")
        board_id = payload.get("board_id")
        
        # Process with Zapier
        result = await process_zapier_action(payload)
        
        # Log success
        logger.info(f"Processed: {card_name}")
        
        return {
            "success": True,
            "message": f"Processed {card_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Enhanced error handling with web search
        solutions = await search_error_solutions(e)
        logger.error(f"Error: {str(e)}", extra={"solutions": solutions})
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "possible_solutions": solutions
            }
        )

async def process_zapier_action(data: dict) -> dict:
    """Execute Zapier action"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            os.getenv("ZAPIER_WEBHOOK", ""),
            json=data,
            timeout=30.0
        )
        return response.json()
`;

  const files = useMemo(() => {
    const mainContent = fetchedCode ?? (fetchedFiles?.['main.py']) ?? placeholderMain;
    const configContent = fetchedFiles?.['config.json'] ?? JSON.stringify({
      agent_id: agent?.id || 'agent_001',
      name: agent?.name || 'FuseAI Agent',
      trigger_type: 'on_demand',
      zapier: { services: agent?.services || [], tool_names: [] },
      monitoring: { log_level: 'INFO', enable_metrics: true }
    }, null, 2);
    const requirementsContent = fetchedFiles?.['requirements.txt'] ?? `fastapi>=0.109.0
uvicorn>=0.27.0
httpx>=0.26.0
python-dotenv>=1.0.0
pydantic>=2.5.0
`;
    const readmeContent = fetchedFiles?.['README.md'] ?? `# ${agent?.name ?? 'FuseAI Agent'}

${agent?.description || 'Auto-generated agent by FuseAI'}

## Setup

1. Install dependencies: \`pip install -r requirements.txt\`
2. Set environment variables (ANTHROPIC_API_KEY, ZAPIER_MCP_*).
3. Run: \`uvicorn main:app --host 0.0.0.0 --port 8000\`
`;
    return {
      'main.py': { icon: FileCode, content: mainContent },
      'config.json': { icon: FileJson, content: configContent },
      'requirements.txt': { icon: FileText, content: requirementsContent },
      'README.md': { icon: FileText, content: readmeContent },
    };
  }, [fetchedCode, fetchedFiles, agent]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="agent-code">
      <Card padding="none">
        <CardHeader actions={
          <Button variant="outline" icon={Download}>
            Download ZIP
          </Button>
        }>
          <h3>Generated Agent Code</h3>
        </CardHeader>
        <div className="agent-code__container">
          {/* File Tree */}
          <div className="agent-code__sidebar">
            <div className="file-tree">
              <div 
                className="file-tree__folder"
                onClick={() => setExpandedFolders(prev => ({ ...prev, root: !prev.root }))}
              >
                {expandedFolders.root ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span>{agent?.id || 'agent_001'}</span>
              </div>
              {expandedFolders.root && (
                <div className="file-tree__files">
                  {Object.entries(files).map(([filename, file]) => (
                    <div
                      key={filename}
                      className={`file-tree__file ${activeFile === filename ? 'file-tree__file--active' : ''}`}
                      onClick={() => setActiveFile(filename)}
                    >
                      <file.icon size={14} />
                      <span>{filename}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Code Viewer */}
          <div className="agent-code__viewer">
            <div className="agent-code__header">
              <span className="agent-code__filename">{activeFile}</span>
              <Button 
                variant="ghost" 
                size="sm" 
                icon={Copy}
                onClick={() => copyToClipboard(files[activeFile].content)}
              >
                Copy
              </Button>
            </div>
            <pre className="agent-code__content">
              <code>{files[activeFile].content}</code>
            </pre>
          </div>
        </div>
      </Card>

      <div className="agent-code__warning">
        <span className="agent-code__warning-icon">⚠️</span>
        <p>This code was automatically generated. You can download and deploy it anywhere.</p>
      </div>
    </div>
  );
}

export default AgentCode;
