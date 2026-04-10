from fastapi import APIRouter, HTTPException

from app.core.wazuh_client import WazuhManagerClient

router = APIRouter(prefix="/wazuh", tags=["Wazuh"])


@router.get("/agents")
async def list_agents():
    """Proxy to Wazuh Manager API — returns connected agent list."""
    try:
        client = WazuhManagerClient()
        agents = await client.get_agents()
        await client.close()
        return {"agents": agents, "total": len(agents)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh Manager unavailable: {e}")


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    try:
        client = WazuhManagerClient()
        agent = await client.get_agent(agent_id)
        await client.close()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Wazuh Manager unavailable: {e}")
