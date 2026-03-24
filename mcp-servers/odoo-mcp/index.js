#!/usr/bin/env node
/**
 * Odoo MCP Server
 * Provides accounting integration with Odoo Community Edition via JSON-RPC API
 * Supports draft-only mode with human approval for posting
 */

import xmlrpc from 'xmlrpc';

// Configuration from environment variables
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'odoo';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'admin';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'admin';

let uid = null;

/**
 * Authenticate with Odoo
 */
async function authenticate() {
  return new Promise((resolve, reject) => {
    const client = xmlrpc.createClient({
      url: `${ODOO_URL}/xmlrpc/2/common`,
      headers: { 'Content-Type': 'text/xml' }
    });

    client.methodCall('authenticate', [ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {}], (error, value) => {
      if (error) {
        reject(error);
      } else {
        uid = value;
        resolve(value);
      }
    });
  });
}

/**
 * Execute Odoo method
 */
async function execute(model, method, args, kwargs = {}) {
  if (!uid) {
    await authenticate();
  }

  return new Promise((resolve, reject) => {
    const client = xmlrpc.createClient({
      url: `${ODOO_URL}/xmlrpc/2/object`,
      headers: { 'Content-Type': 'text/xml' }
    });

    client.methodCall('execute_kw', [
      ODOO_DB,
      uid,
      ODOO_PASSWORD,
      model,
      method,
      args,
      kwargs
    ], (error, value) => {
      if (error) {
        reject(error);
      } else {
        resolve(value);
      }
    });
  });
}

/**
 * MCP Tool: Get Invoices
 */
async function getInvoices(params) {
  const { limit = 10, state = 'draft' } = params;

  try {
    const domain = state ? [['state', '=', state]] : [];
    const invoices = await execute(
      'account.move',
      'search_read',
      [domain],
      {
        fields: ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'],
        limit: limit
      }
    );

    return {
      success: true,
      invoices: invoices
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * MCP Tool: Create Draft Invoice
 */
async function createDraftInvoice(params) {
  const { partner_id, invoice_lines, invoice_date } = params;

  try {
    const invoiceData = {
      partner_id: partner_id,
      move_type: 'out_invoice',
      invoice_date: invoice_date || new Date().toISOString().split('T')[0],
      invoice_line_ids: invoice_lines.map(line => [0, 0, {
        product_id: line.product_id,
        quantity: line.quantity,
        price_unit: line.price_unit,
        name: line.description || 'Product/Service'
      }])
    };

    const invoiceId = await execute(
      'account.move',
      'create',
      [invoiceData]
    );

    return {
      success: true,
      invoice_id: invoiceId,
      message: 'Draft invoice created. Requires human approval to post.',
      approval_required: true
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * MCP Tool: Get Revenue Report
 */
async function getRevenueReport(params) {
  const { start_date, end_date } = params;

  try {
    const domain = [
      ['move_type', '=', 'out_invoice'],
      ['state', '=', 'posted'],
      ['invoice_date', '>=', start_date],
      ['invoice_date', '<=', end_date]
    ];

    const invoices = await execute(
      'account.move',
      'search_read',
      [domain],
      {
        fields: ['name', 'partner_id', 'amount_total', 'invoice_date']
      }
    );

    const totalRevenue = invoices.reduce((sum, inv) => sum + inv.amount_total, 0);

    return {
      success: true,
      period: { start_date, end_date },
      total_revenue: totalRevenue,
      invoice_count: invoices.length,
      invoices: invoices
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * MCP Tool: Get Expenses
 */
async function getExpenses(params) {
  const { start_date, end_date, limit = 50 } = params;

  try {
    const domain = [
      ['move_type', '=', 'in_invoice'],
      ['state', '=', 'posted'],
      ['invoice_date', '>=', start_date],
      ['invoice_date', '<=', end_date]
    ];

    const expenses = await execute(
      'account.move',
      'search_read',
      [domain],
      {
        fields: ['name', 'partner_id', 'amount_total', 'invoice_date'],
        limit: limit
      }
    );

    const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount_total, 0);

    return {
      success: true,
      period: { start_date, end_date },
      total_expenses: totalExpenses,
      expense_count: expenses.length,
      expenses: expenses
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
class OdooMCPServer {
  constructor() {
    this.tools = [
      {
        name: 'get_invoices',
        description: 'Get invoices from Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Maximum number of invoices to return' },
            state: { type: 'string', description: 'Invoice state (draft, posted, cancel)' }
          }
        }
      },
      {
        name: 'create_draft_invoice',
        description: 'Create a draft invoice (requires human approval to post)',
        inputSchema: {
          type: 'object',
          properties: {
            partner_id: { type: 'number', description: 'Customer ID', required: true },
            invoice_lines: {
              type: 'array',
              description: 'Invoice line items',
              items: {
                type: 'object',
                properties: {
                  product_id: { type: 'number' },
                  quantity: { type: 'number' },
                  price_unit: { type: 'number' },
                  description: { type: 'string' }
                }
              }
            },
            invoice_date: { type: 'string', description: 'Invoice date (YYYY-MM-DD)' }
          },
          required: ['partner_id', 'invoice_lines']
        }
      },
      {
        name: 'get_revenue_report',
        description: 'Get revenue report for a date range',
        inputSchema: {
          type: 'object',
          properties: {
            start_date: { type: 'string', description: 'Start date (YYYY-MM-DD)', required: true },
            end_date: { type: 'string', description: 'End date (YYYY-MM-DD)', required: true }
          },
          required: ['start_date', 'end_date']
        }
      },
      {
        name: 'get_expenses',
        description: 'Get expenses for a date range',
        inputSchema: {
          type: 'object',
          properties: {
            start_date: { type: 'string', description: 'Start date (YYYY-MM-DD)', required: true },
            end_date: { type: 'string', description: 'End date (YYYY-MM-DD)', required: true },
            limit: { type: 'number', description: 'Maximum number of expenses to return' }
          },
          required: ['start_date', 'end_date']
        }
      }
    ];
  }

  async handleToolCall(toolName, params) {
    switch (toolName) {
      case 'get_invoices':
        return await getInvoices(params);
      case 'create_draft_invoice':
        return await createDraftInvoice(params);
      case 'get_revenue_report':
        return await getRevenueReport(params);
      case 'get_expenses':
        return await getExpenses(params);
      default:
        return { success: false, error: 'Unknown tool' };
    }
  }

  async start() {
    console.log('Odoo MCP Server starting...');
    console.log(`Odoo URL: ${ODOO_URL}`);
    console.log(`Database: ${ODOO_DB}`);

    try {
      await authenticate();
      console.log('Authenticated with Odoo successfully');
      console.log('MCP Server ready');

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
    } catch (error) {
      console.error('Failed to authenticate with Odoo:', error.message);
      process.exit(1);
    }
  }
}

// Start the server
const server = new OdooMCPServer();
server.start();
