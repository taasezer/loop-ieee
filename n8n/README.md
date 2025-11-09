# LOOP Logistics - n8n Integration

## Overview

This directory contains n8n workflow templates for automating LOOP logistics operations. The workflows integrate with the LOOP API to provide intelligent automation for courier assignments, notifications, and decision-making.

## Workflows

### 1. Auto-Assignment Workflow
Automatically assigns the best courier when a new order is created.

**Trigger:** New order created (webhook or database trigger)
**Process:**
1. Receive new order notification
2. Call AI recommendation API: `POST /api/ai/recommend`
3. If score > 0.7, auto-assign: `POST /api/ai/assign`
4. Send notifications to courier and customer
5. Update order status

**Webhook URL:** `YOUR_N8N_URL/webhook/new-order`

### 2. Order Status Update Workflow
Sends notifications when order status changes.

**Trigger:** Order status update (webhook)
**Process:**
1. Receive status update
2. Fetch order details: `GET /api/orders/{order_id}`
3. Send SMS/email notification to customer
4. If delivered, update courier stats
5. Log to analytics

**Webhook URL:** `YOUR_N8N_URL/webhook/order-status`

### 3. Weather Alert Workflow
Monitors weather and alerts couriers about dangerous conditions.

**Trigger:** Schedule (every 30 minutes)
**Process:**
1. Get all active courier locations: `GET /api/tracking/active`
2. For each location, check weather: `POST /api/weather/impact`
3. If impact_score < 0.5, send alert to courier
4. Suggest reassignment if needed

### 4. Courier Performance Analytics
Generates daily performance reports.

**Trigger:** Schedule (daily at 23:00)
**Process:**
1. Fetch all couriers: `GET /api/couriers/`
2. For each courier, get stats: `GET /api/couriers/{id}/stats`
3. Generate performance report
4. Send to management dashboard
5. Identify top performers and those needing support

### 5. Smart Routing Optimization
Optimizes routes for couriers with multiple deliveries.

**Trigger:** Schedule (every 15 minutes) or manual trigger
**Process:**
1. Get busy couriers: `GET /api/couriers/?status=busy`
2. For each courier: `POST /api/ai/optimize-route`
3. Send optimized route to courier app
4. Update ETAs in system

## Setup Instructions

### 1. Install n8n

```bash
npm install -g n8n

# Or use Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### 2. Configure Environment Variables

Add these to your n8n environment:

```
LOOP_API_URL=http://your-api-url:8000
LOOP_API_KEY=your_api_key_if_needed
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Import Workflows

1. Open n8n interface (http://localhost:5678)
2. Click "Import from File"
3. Select workflow JSON files from `/n8n/workflows/`
4. Configure webhook URLs
5. Activate workflows

## API Integration

### Authentication

If your API requires authentication, add these headers to all HTTP requests:

```json
{
  "Authorization": "Bearer YOUR_API_KEY",
  "Content-Type": "application/json"
}
```

### Webhook Configuration

Configure webhooks in your application to trigger n8n workflows:

1. **New Order Created**
   - Endpoint: `POST /api/orders/`
   - Webhook: Send to n8n when order created
   - Payload: Full order object

2. **Order Status Changed**
   - Endpoint: `PATCH /api/orders/{order_id}`
   - Webhook: Send to n8n on status change
   - Payload: Order ID + new status

3. **Courier Location Updated**
   - Endpoint: `POST /api/tracking/update`
   - Webhook: Send to n8n on location update
   - Payload: Courier ID + location data

## Example Workflows

### Auto-Assignment Flow

```
[Webhook] New Order
    ↓
[HTTP Request] GET /api/ai/recommend
    ↓
[IF] Score > 0.7?
    ↓ YES
[HTTP Request] POST /api/ai/assign
    ↓
[Function] Prepare notification
    ↓
[Send Email/SMS] Notify courier & customer
    ↓
[HTTP Request] Update order status
```

### Weather Alert Flow

```
[Schedule] Every 30 min
    ↓
[HTTP Request] GET /api/tracking/active
    ↓
[Loop] For each courier
    ↓
[HTTP Request] POST /api/weather/impact
    ↓
[IF] Impact < 0.5?
    ↓ YES
[Send Alert] SMS to courier
    ↓
[HTTP Request] Log alert
```

## Best Practices

1. **Error Handling**
   - Always add error handling nodes
   - Log failures to monitoring system
   - Set up retry logic for API calls

2. **Rate Limiting**
   - Add delays between API calls
   - Use batch processing when possible
   - Monitor API usage

3. **Testing**
   - Test workflows with sample data
   - Validate all API endpoints
   - Check notification delivery

4. **Monitoring**
   - Enable workflow execution logging
   - Set up alerts for failures
   - Track performance metrics

## Troubleshooting

### Workflow Not Triggering
- Check webhook URL is correct
- Verify API is sending webhooks
- Check n8n logs for errors

### API Calls Failing
- Verify API endpoint URLs
- Check authentication credentials
- Test endpoints with Postman first

### Notifications Not Sending
- Verify email/SMS credentials
- Check notification service status
- Review error logs

## Support

For issues or questions:
- Check API documentation
- Review n8n logs
- Contact development team
