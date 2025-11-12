# n8n Integration Setup Guide for LOOP Logistics

This guide will help you set up n8n workflow automation for LOOP Logistics system.

## What is n8n?

n8n is a workflow automation tool that allows you to connect different services and automate processes. In LOOP Logistics, it's used for:

- AI decision logging and tracking
- Automated notifications based on events
- Analytics data collection
- Custom business logic automation

## Installation Options

### Option 1: Docker (Recommended)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### Option 2: npm

```bash
npm install n8n -g
n8n start
```

### Option 3: Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3"

services:
  n8n:
    image: n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_password
    volumes:
      - ~/.n8n:/home/node/.n8n
```

Then run:
```bash
docker-compose up -d
```

## Accessing n8n

Once running, access n8n at: `http://localhost:5678`

## Setting Up Workflows

### 1. Courier Assignment Workflow

This workflow tracks AI courier assignments and sends notifications.

**Steps:**

1. Create new workflow in n8n
2. Add "Webhook" node (trigger):
   - HTTP Method: POST
   - Path: `/courier-assigned`
   - Copy the webhook URL (e.g., `http://localhost:5678/webhook/courier-assigned`)
3. Add "Set" node to process data:
   ```
   - order_id: {{$json["order_id"]}}
   - courier_id: {{$json["courier_id"]}}
   - assignment_score: {{$json["assignment_score"]}}
   - timestamp: {{$json["timestamp"]}}
   ```
4. Add "HTTP Request" node to send notification:
   - Method: POST
   - URL: `http://localhost:8001/api/notifications/push`
   - Authentication: Bearer Token
   - Body: JSON with notification details
5. Activate workflow

**Update LOOP Backend:**
Add the webhook URL to `/app/backend/.env`:
```
N8N_WEBHOOK_URL=http://localhost:5678/webhook/courier-assigned
```

### 2. Order Status Change Workflow

Monitor order status changes and trigger actions.

**Workflow Structure:**

```
Webhook Trigger (Order Status Change)
  ↓
Check Status
  ↓
Switch Node (based on status):
  ├─ Delivered → Send customer thank you email
  ├─ Cancelled → Alert admin
  └─ In Transit → Send ETA update
```

**n8n Nodes:**
1. Webhook node: `/order-status-changed`
2. Switch node with conditions
3. Multiple HTTP Request nodes for different actions
4. SendGrid/Twilio nodes for notifications

### 3. Daily Analytics Workflow

Automated daily reports.

**Workflow:**

```
Cron Trigger (Daily at 9 AM)
  ↓
HTTP Request to /api/analytics/dashboard
  ↓
HTTP Request to /api/analytics/revenue
  ↓
Format Data
  ↓
Send Email Report (SendGrid)
```

### 4. Weather Alert Workflow

Alert system when bad weather is detected.

**Workflow:**

```
Cron Trigger (Every hour)
  ↓
HTTP Request to /api/weather/current
  ↓
Check Weather Conditions
  ↓
If bad weather → Send alerts to active couriers
```

## Complete Webhook Endpoints in LOOP

LOOP provides these webhook endpoints for n8n:

1. `/api/webhooks/order-created` - New order created
2. `/api/webhooks/courier-assigned` - Courier assigned to order
3. `/api/webhooks/delivery-completed` - Delivery completed
4. `/api/webhooks/analytics-event` - Generic analytics events

## Example n8n Workflow JSON

### Courier Assignment Notification Workflow

```json
{
  "name": "Courier Assignment Notification",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "courier-assigned",
        "responseMode": "onReceived",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "message",
              "value": "=New order {{$json[\"order_id\"]}} assigned to courier {{$json[\"courier_id\"]}} with score {{$json[\"assignment_score\"]}}"
            }
          ]
        },
        "options": {}
      },
      "name": "Format Message",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8001/api/notifications/push",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "={\"device_tokens\": [\"test_token\"], \"title\": \"New Assignment\", \"body\": \"{{$json[\\\"message\\\"]}}\", \"data\": {{$json}}}"
      },
      "name": "Send Notification",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [650, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Format Message", "type": "main", "index": 0}]]
    },
    "Format Message": {
      "main": [[{"node": "Send Notification", "type": "main", "index": 0}]]
    }
  }
}
```

**To Import:**
1. Copy the JSON above
2. In n8n, click "Import from JSON"
3. Paste and activate

## Advanced Workflows

### Machine Learning Model Integration

For courier assignment optimization:

```
Webhook: New Order
  ↓
Gather Historical Data (MongoDB)
  ↓
Call ML API (Python/TensorFlow)
  ↓
Get Best Courier Prediction
  ↓
Assign Courier via LOOP API
  ↓
Log Decision for Training
```

### Multi-Channel Notification System

```
Order Status Change Webhook
  ↓
Check User Preferences
  ↓
Split (Parallel):
  ├─ Send Push (FCM)
  ├─ Send Email (SendGrid)
  └─ Send SMS (Twilio)
  ↓
Log Notification Status
```

## Testing Webhooks

### From Terminal

```bash
# Test courier assignment webhook
curl -X POST http://localhost:5678/webhook/courier-assigned \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "test-order-123",
    "courier_id": "courier-456",
    "assignment_score": 95.5,
    "timestamp": "2025-01-12T10:00:00Z"
  }'
```

### From LOOP Backend

The backend automatically calls n8n webhooks when:
- A courier is assigned (via AI assignment service)
- Orders are created/updated
- Deliveries are completed

Check `/app/backend/services/ai_assignment_service.py` for webhook implementation.

## Monitoring & Debugging

### Check n8n Executions

1. Go to n8n UI: `http://localhost:5678`
2. Click "Executions" in left sidebar
3. View execution history, errors, and data flow

### Common Issues

**Issue: Webhook not receiving data**
- Check n8n is running: `docker ps` or check port 5678
- Verify webhook URL in LOOP `.env` file
- Check n8n execution logs

**Issue: Authentication errors**
- Ensure Bearer token is correctly passed
- Check if n8n has API credentials configured

**Issue: Workflow not triggering**
- Verify workflow is activated (toggle in top right)
- Check webhook path matches LOOP configuration
- Test webhook manually with curl

## Production Best Practices

1. **Security:**
   - Use n8n basic auth or OAuth
   - Run n8n behind reverse proxy (nginx)
   - Use HTTPS for webhooks

2. **Scalability:**
   - Use n8n with PostgreSQL for persistence
   - Set up queue mode for high traffic
   - Monitor execution times

3. **Reliability:**
   - Set up error notifications
   - Implement retry logic
   - Log all webhook calls

4. **Monitoring:**
   - Track webhook success/failure rates
   - Monitor execution times
   - Set up alerts for failed workflows

## Environment Variables for Production

```bash
# n8n Configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure_password
N8N_HOST=n8n.yourdomain.com
N8N_PORT=5678
N8N_PROTOCOL=https
N8N_WEBHOOK_URL=https://n8n.yourdomain.com/

# Database (PostgreSQL for production)
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=secure_db_password
```

## Resources

- n8n Documentation: https://docs.n8n.io/
- n8n Community: https://community.n8n.io/
- n8n Workflows Library: https://n8n.io/workflows/

## Support

For LOOP-specific n8n integration issues:
1. Check the workflow execution logs in n8n UI
2. Verify webhook URLs in `/app/backend/.env`
3. Test webhooks manually using curl
4. Check LOOP backend logs: `tail -f /var/log/supervisor/backend.*.log`

---

**Happy Automating! 🚀**
