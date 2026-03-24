#!/usr/bin/env node
/**
 * WhatsApp MCP Server
 * Provides WhatsApp messaging capabilities via browser automation
 * Note: Requires manual login on first run
 */

import { chromium } from 'playwright';

const SESSION_PATH = process.env.WHATSAPP_SESSION_PATH || './whatsapp_session';

let browser = null;
let page = null;

/**
 * Initialize WhatsApp Web session
 */
async function initializeWhatsApp() {
  if (browser) return;

  browser = await chromium.launchPersistentContext(SESSION_PATH, {
    headless: false, // WhatsApp Web requires visible browser
    args: ['--disable-blink-features=AutomationControlled']
  });

  page = browser.pages()[0] || await browser.newPage();
  await page.goto('https://web.whatsapp.com');

  // Wait for WhatsApp to load
  await page.waitForSelector('[data-testid="chat-list"]', { timeout: 60000 });
}

/**
 * Send WhatsApp message
 */
async function sendMessage(params) {
  const { contact, message } = params;

  try {
    await initializeWhatsApp();

    // Search for contact
    const searchBox = await page.waitForSelector('[data-testid="chat-list-search"]');
    await searchBox.click();
    await searchBox.fill(contact);
    await page.waitForTimeout(1000);

    // Click on first result
    const firstChat = await page.waitForSelector('[data-testid="cell-frame-container"]');
    await firstChat.click();
    await page.waitForTimeout(500);

    // Type and send message
    const messageBox = await page.waitForSelector('[data-testid="conversation-compose-box-input"]');
    await messageBox.fill(message);
    await page.waitForTimeout(500);

    const sendButton = await page.waitForSelector('[data-testid="send"]');
    await sendButton.click();

    return {
      success: true,
      message: 'Message sent successfully'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Get unread messages
 */
async function getUnreadMessages(params) {
  const { limit = 10 } = params;

  try {
    await initializeWhatsApp();

    const unreadChats = await page.$$('[data-testid="cell-frame-container"]:has([aria-label*="unread"])');
    const messages = [];

    for (let i = 0; i < Math.min(unreadChats.length, limit); i++) {
      const chat = unreadChats[i];
      const text = await chat.innerText();
      messages.push({ text });
    }

    return {
      success: true,
      messages: messages
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
class WhatsAppMCPServer {
  constructor() {
    this.tools = [
      {
        name: 'send_message',
        description: 'Send a WhatsApp message to a contact',
        inputSchema: {
          type: 'object',
          properties: {
            contact: { type: 'string', description: 'Contact name or phone number', required: true },
            message: { type: 'string', description: 'Message text', required: true }
          },
          required: ['contact', 'message']
        }
      },
      {
        name: 'get_unread_messages',
        description: 'Get unread WhatsApp messages',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Maximum number of messages to return' }
          }
        }
      }
    ];
  }

  async handleToolCall(toolName, params) {
    switch (toolName) {
      case 'send_message':
        return await sendMessage(params);
      case 'get_unread_messages':
        return await getUnreadMessages(params);
      default:
        return { success: false, error: 'Unknown tool' };
    }
  }

  async start() {
    console.log('WhatsApp MCP Server starting...');
    console.log('Session path:', SESSION_PATH);
    console.log('Note: First run requires manual WhatsApp Web login');

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

    // Cleanup on exit
    process.on('SIGINT', async () => {
      if (browser) await browser.close();
      process.exit(0);
    });
  }
}

// Start the server
const server = new WhatsAppMCPServer();
server.start();
