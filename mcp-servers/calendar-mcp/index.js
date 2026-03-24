#!/usr/bin/env node
/**
 * Calendar MCP Server
 * Provides calendar management capabilities
 * Stores events in JSON file (can be extended to integrate with Google Calendar, etc.)
 */

import fs from 'fs/promises';
import path from 'path';

const CALENDAR_FILE = process.env.CALENDAR_FILE || './calendar_events.json';

/**
 * Load calendar events
 */
async function loadEvents() {
  try {
    const data = await fs.readFile(CALENDAR_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return [];
  }
}

/**
 * Save calendar events
 */
async function saveEvents(events) {
  await fs.writeFile(CALENDAR_FILE, JSON.stringify(events, null, 2));
}

/**
 * Create calendar event
 */
async function createEvent(params) {
  const { title, start_time, end_time, description, location } = params;

  try {
    const events = await loadEvents();

    const newEvent = {
      id: Date.now().toString(),
      title,
      start_time,
      end_time,
      description: description || '',
      location: location || '',
      created_at: new Date().toISOString()
    };

    events.push(newEvent);
    await saveEvents(events);

    return {
      success: true,
      event: newEvent
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Get calendar events
 */
async function getEvents(params) {
  const { start_date, end_date, limit = 50 } = params;

  try {
    let events = await loadEvents();

    // Filter by date range if provided
    if (start_date) {
      events = events.filter(e => e.start_time >= start_date);
    }
    if (end_date) {
      events = events.filter(e => e.start_time <= end_date);
    }

    // Sort by start time
    events.sort((a, b) => a.start_time.localeCompare(b.start_time));

    // Limit results
    events = events.slice(0, limit);

    return {
      success: true,
      events: events
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Update calendar event
 */
async function updateEvent(params) {
  const { event_id, title, start_time, end_time, description, location } = params;

  try {
    const events = await loadEvents();
    const index = events.findIndex(e => e.id === event_id);

    if (index === -1) {
      return {
        success: false,
        error: 'Event not found'
      };
    }

    // Update fields
    if (title) events[index].title = title;
    if (start_time) events[index].start_time = start_time;
    if (end_time) events[index].end_time = end_time;
    if (description !== undefined) events[index].description = description;
    if (location !== undefined) events[index].location = location;

    events[index].updated_at = new Date().toISOString();

    await saveEvents(events);

    return {
      success: true,
      event: events[index]
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Delete calendar event
 */
async function deleteEvent(params) {
  const { event_id } = params;

  try {
    let events = await loadEvents();
    const initialLength = events.length;

    events = events.filter(e => e.id !== event_id);

    if (events.length === initialLength) {
      return {
        success: false,
        error: 'Event not found'
      };
    }

    await saveEvents(events);

    return {
      success: true,
      message: 'Event deleted'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * MCP Server Implementation
 */
class CalendarMCPServer {
  constructor() {
    this.tools = [
      {
        name: 'create_event',
        description: 'Create a calendar event',
        inputSchema: {
          type: 'object',
          properties: {
            title: { type: 'string', description: 'Event title', required: true },
            start_time: { type: 'string', description: 'Start time (ISO 8601)', required: true },
            end_time: { type: 'string', description: 'End time (ISO 8601)', required: true },
            description: { type: 'string', description: 'Event description' },
            location: { type: 'string', description: 'Event location' }
          },
          required: ['title', 'start_time', 'end_time']
        }
      },
      {
        name: 'get_events',
        description: 'Get calendar events',
        inputSchema: {
          type: 'object',
          properties: {
            start_date: { type: 'string', description: 'Start date filter (ISO 8601)' },
            end_date: { type: 'string', description: 'End date filter (ISO 8601)' },
            limit: { type: 'number', description: 'Maximum number of events to return' }
          }
        }
      },
      {
        name: 'update_event',
        description: 'Update a calendar event',
        inputSchema: {
          type: 'object',
          properties: {
            event_id: { type: 'string', description: 'Event ID', required: true },
            title: { type: 'string', description: 'Event title' },
            start_time: { type: 'string', description: 'Start time (ISO 8601)' },
            end_time: { type: 'string', description: 'End time (ISO 8601)' },
            description: { type: 'string', description: 'Event description' },
            location: { type: 'string', description: 'Event location' }
          },
          required: ['event_id']
        }
      },
      {
        name: 'delete_event',
        description: 'Delete a calendar event',
        inputSchema: {
          type: 'object',
          properties: {
            event_id: { type: 'string', description: 'Event ID', required: true }
          },
          required: ['event_id']
        }
      }
    ];
  }

  async handleToolCall(toolName, params) {
    switch (toolName) {
      case 'create_event':
        return await createEvent(params);
      case 'get_events':
        return await getEvents(params);
      case 'update_event':
        return await updateEvent(params);
      case 'delete_event':
        return await deleteEvent(params);
      default:
        return { success: false, error: 'Unknown tool' };
    }
  }

  async start() {
    console.log('Calendar MCP Server starting...');
    console.log('Calendar file:', CALENDAR_FILE);

    // Listen for MCP protocol messages on stdin
    process.stdin.on('data', async (data) => {
      try {
        const message = JSON.parse(data.toString());

        if (message.method === 'tools/list') {
          process.stdout.write(JSON.stringify({
            tools: this.tools
          }) + '\n');
        } else if (message.method === 'tools/call') {
          const result = await this.handleToolCall(message.params.name, message.params.arguments);
          process.stdout.write(JSON.stringify({
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
          }) + '\n');
        }
      } catch (error) {
        console.error('Error processing message:', error);
      }
    });
  }
}

// Start the server
const server = new CalendarMCPServer();
server.start();
