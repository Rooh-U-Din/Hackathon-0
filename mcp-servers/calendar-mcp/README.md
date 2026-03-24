# Calendar MCP Server

## Overview

The Calendar MCP Server provides calendar management capabilities using JSON file storage. It enables Claude Code to create, read, update, and delete calendar events. The implementation is simple and extensible, with no external API dependencies.

## Features

- **Create Events**: Add new calendar events
- **Get Events**: Retrieve events with date filtering
- **Update Events**: Modify existing events
- **Delete Events**: Remove events
- **Date Filtering**: Filter events by date range
- **JSON Storage**: Simple file-based storage
- **Extensible**: Can be extended to integrate with Google Calendar API

## Installation

### Prerequisites

1. **Node.js 18+** installed

### Setup

```bash
cd mcp-servers/calendar-mcp

# Install dependencies (none required for basic version)
npm install

# Set environment variables (optional)
export CALENDAR_FILE="./calendar_events.json"

# Test the server
node index.js
```

## Configuration

### Environment Variables

```bash
# .env file
CALENDAR_FILE=./calendar_events.json
```

### Claude Code MCP Configuration

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "calendar",
      "command": "node",
      "args": ["/path/to/mcp-servers/calendar-mcp/index.js"],
      "env": {
        "CALENDAR_FILE": "./calendar_events.json"
      }
    }
  ]
}
```

## Available Tools

### 1. create_event

Create a new calendar event.

**Parameters:**
- `title` (string, required): Event title
- `start_time` (string, required): Start time in ISO 8601 format
- `end_time` (string, required): End time in ISO 8601 format
- `description` (string): Event description
- `location` (string): Event location

**Example:**
```javascript
{
  "title": "Team Meeting",
  "start_time": "2026-02-28T14:00:00Z",
  "end_time": "2026-02-28T15:00:00Z",
  "description": "Weekly team sync",
  "location": "Conference Room A"
}
```

**Response:**
```json
{
  "success": true,
  "event": {
    "id": "1709123456789",
    "title": "Team Meeting",
    "start_time": "2026-02-28T14:00:00Z",
    "end_time": "2026-02-28T15:00:00Z",
    "description": "Weekly team sync",
    "location": "Conference Room A",
    "created_at": "2026-02-28T10:00:00Z"
  }
}
```

### 2. get_events

Get calendar events with optional date filtering.

**Parameters:**
- `start_date` (string): Start date filter (ISO 8601)
- `end_date` (string): End date filter (ISO 8601)
- `limit` (number): Maximum number of events to return (default: 50)

**Example:**
```javascript
{
  "start_date": "2026-02-28",
  "end_date": "2026-03-07",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "1709123456789",
      "title": "Team Meeting",
      "start_time": "2026-02-28T14:00:00Z",
      "end_time": "2026-02-28T15:00:00Z",
      "description": "Weekly team sync",
      "location": "Conference Room A",
      "created_at": "2026-02-28T10:00:00Z"
    }
  ]
}
```

### 3. update_event

Update an existing calendar event.

**Parameters:**
- `event_id` (string, required): Event ID to update
- `title` (string): New event title
- `start_time` (string): New start time (ISO 8601)
- `end_time` (string): New end time (ISO 8601)
- `description` (string): New description
- `location` (string): New location

**Example:**
```javascript
{
  "event_id": "1709123456789",
  "title": "Team Meeting - Updated",
  "location": "Conference Room B"
}
```

**Response:**
```json
{
  "success": true,
  "event": {
    "id": "1709123456789",
    "title": "Team Meeting - Updated",
    "start_time": "2026-02-28T14:00:00Z",
    "end_time": "2026-02-28T15:00:00Z",
    "description": "Weekly team sync",
    "location": "Conference Room B",
    "created_at": "2026-02-28T10:00:00Z",
    "updated_at": "2026-02-28T11:00:00Z"
  }
}
```

### 4. delete_event

Delete a calendar event.

**Parameters:**
- `event_id` (string, required): Event ID to delete

**Example:**
```javascript
{
  "event_id": "1709123456789"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Event deleted"
}
```

## Storage Format

Events are stored in a JSON file with the following structure:

```json
[
  {
    "id": "1709123456789",
    "title": "Team Meeting",
    "start_time": "2026-02-28T14:00:00Z",
    "end_time": "2026-02-28T15:00:00Z",
    "description": "Weekly team sync",
    "location": "Conference Room A",
    "created_at": "2026-02-28T10:00:00Z"
  },
  {
    "id": "1709123456790",
    "title": "Client Call",
    "start_time": "2026-02-28T16:00:00Z",
    "end_time": "2026-02-28T17:00:00Z",
    "description": "Discuss project requirements",
    "location": "Zoom",
    "created_at": "2026-02-28T10:05:00Z"
  }
]
```

## How It Works

1. **File-Based Storage**: Events stored in JSON file
2. **Automatic ID Generation**: Uses timestamp for unique IDs
3. **Date Filtering**: Filters events by start_time
4. **Sorting**: Events sorted by start_time
5. **CRUD Operations**: Full create, read, update, delete support

## Integration with Personal AI Employee

### Cloud Agent Usage

```python
# In cloud_agent.py
# Schedule meeting based on email request

def schedule_meeting(title, start_time, end_time, description):
    result = mcp_client.call_tool('calendar', 'create_event', {
        'title': title,
        'start_time': start_time,
        'end_time': end_time,
        'description': description
    })
    return result
```

### Local Agent Usage

```python
# In local_agent.py
# Get upcoming events for briefing

def get_upcoming_events():
    result = mcp_client.call_tool('calendar', 'get_events', {
        'start_date': datetime.now().isoformat(),
        'limit': 10
    })
    return result
```

### CEO Briefing Integration

```python
# In ceo_briefing_generator.py
# Include upcoming events in briefing

events = calendar_mcp.get_events({
    'start_date': start_date,
    'end_date': end_date
})

briefing += f"\n## Upcoming Events ({len(events['events'])})\n"
for event in events['events']:
    briefing += f"- {event['title']} - {event['start_time']}\n"
```

## Security

- **File-Based**: No external API calls
- **Local Storage**: Events stored locally
- **No Authentication**: Simple file access
- **Safe for Cloud**: Can be used on cloud agent
- **Backup Recommended**: Backup calendar_events.json regularly

## Performance

- **Create Event**: ~10-50ms
- **Get Events**: ~10-50ms (depends on file size)
- **Update Event**: ~10-50ms
- **Delete Event**: ~10-50ms
- **Memory Usage**: Minimal (~10 MB)

## Troubleshooting

### Error: Cannot Write to File

**Problem**: Permission denied writing to calendar_events.json

**Solution**:
```bash
# Check file permissions
ls -la calendar_events.json

# Fix permissions
chmod 644 calendar_events.json
```

### Error: Invalid JSON

**Problem**: calendar_events.json corrupted

**Solution**:
```bash
# Backup corrupted file
mv calendar_events.json calendar_events.json.bak

# Create new empty file
echo "[]" > calendar_events.json
```

### Error: Event Not Found

**Problem**: Trying to update/delete non-existent event

**Solution**:
- Verify event_id is correct
- Check if event was already deleted
- List all events to find correct ID

## Extending to Google Calendar API

To integrate with Google Calendar API:

1. **Install Google Calendar API client**:
```bash
npm install googleapis
```

2. **Add OAuth authentication**:
```javascript
import { google } from 'googleapis';

const auth = new google.auth.OAuth2(
  CLIENT_ID,
  CLIENT_SECRET,
  REDIRECT_URI
);

const calendar = google.calendar({ version: 'v3', auth });
```

3. **Replace file operations with API calls**:
```javascript
async function createEvent(params) {
  const event = {
    summary: params.title,
    start: { dateTime: params.start_time },
    end: { dateTime: params.end_time },
    description: params.description,
    location: params.location
  };

  const response = await calendar.events.insert({
    calendarId: 'primary',
    resource: event
  });

  return { success: true, event: response.data };
}
```

## Future Enhancements

- Google Calendar API integration
- Recurring events support
- Event reminders
- Attendee management
- Calendar sharing
- Time zone support
- Conflict detection
- Event categories/tags

## Backup and Recovery

### Backup Calendar

```bash
# Manual backup
cp calendar_events.json calendar_events.backup.json

# Automated backup (cron)
0 0 * * * cp /path/to/calendar_events.json /path/to/backups/calendar_$(date +\%Y\%m\%d).json
```

### Restore Calendar

```bash
# Restore from backup
cp calendar_events.backup.json calendar_events.json
```

## Testing

### Manual Testing

```bash
# Start server
node index.js

# In another terminal, send test message
echo '{"method":"tools/call","params":{"name":"create_event","arguments":{"title":"Test Event","start_time":"2026-02-28T14:00:00Z","end_time":"2026-02-28T15:00:00Z"}}}' | node index.js
```

### Automated Testing

```javascript
// test.js
import { createEvent, getEvents } from './index.js';

// Test create event
const result = await createEvent({
  title: 'Test Event',
  start_time: '2026-02-28T14:00:00Z',
  end_time: '2026-02-28T15:00:00Z'
});

console.log('Create result:', result);

// Test get events
const events = await getEvents({ limit: 10 });
console.log('Events:', events);
```

---

**Part of Gold Tier - Personal AI Employee**
**Calendar Management via MCP**

**✅ Safe for cloud agent**
**✅ No external dependencies**
**✅ Simple and reliable**
