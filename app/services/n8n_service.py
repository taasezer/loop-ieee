"""
N8N Automation Service Stub
This service is meant to trigger external N8N webhooks.
For now, it simply logs the event.
"""

class N8NService:
    def __init__(self):
        self.enabled = False # Şimdilik kapalı tutuluyor

    async def trigger_order_status_update(self, order_id: int, new_status: str, supplier_id: int | None = None):
        """
        Gelecekte N8N webhook'larına istek atacak asıl metod.
        Örneğin:
        async with httpx.AsyncClient() as client:
            await client.post("https://n8n.loop.com/webhook/order-update", json={...})
        """
        if self.enabled:
            print(f"[N8N HOOK] Order #{order_id} status updated to '{new_status}'. (Supplier: {supplier_id})")

n8n_service = N8NService()
