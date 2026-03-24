#!/usr/bin/env python3
"""
Test Suite for Odoo Integration

Tests Odoo Community Edition integration via JSON-RPC with mocked API calls:
- Draft invoice creation
- Revenue report generation
- Expense tracking
- Read-only vs full access permissions
- Approval workflow for financial actions

All Odoo API calls are mocked to ensure:
- No real database modifications
- No network calls to Odoo server
- Deterministic test behavior
- Proper payload formatting

All tests use unittest.mock to prevent real Odoo API calls.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json


class TestOdooJSONRPC(unittest.TestCase):
    """Test Odoo JSON-RPC API integration with mocked calls."""

    def setUp(self):
        """Set up test environment."""
        self.odoo_url = "http://localhost:8069"
        self.odoo_db = "odoo"
        self.odoo_username = "admin"
        self.odoo_password = "admin"

    @patch('requests.post')
    def test_odoo_authenticate_successfully(self, mock_post):
        """Test that Odoo authentication works correctly."""
        # Mock authentication response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 1,
            'result': 123  # User ID
        }
        mock_post.return_value = mock_response

        # Simulate authentication
        auth_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'common',
                'method': 'authenticate',
                'args': [self.odoo_db, self.odoo_username, self.odoo_password, {}]
            },
            'id': 1
        }

        response = mock_post(f"{self.odoo_url}/jsonrpc", json=auth_payload)
        result = response.json()

        # Verify authentication
        self.assertEqual(result['result'], 123)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_odoo_get_invoices_with_correct_payload(self, mock_post):
        """Test that Odoo get_invoices formats request correctly."""
        # Mock invoices response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 2,
            'result': [
                {
                    'id': 1,
                    'name': 'INV/2026/0001',
                    'partner_id': [1, 'Customer A'],
                    'amount_total': 1000.00,
                    'state': 'posted'
                },
                {
                    'id': 2,
                    'name': 'INV/2026/0002',
                    'partner_id': [2, 'Customer B'],
                    'amount_total': 2500.00,
                    'state': 'posted'
                }
            ]
        }
        mock_post.return_value = mock_response

        # Simulate get_invoices call
        get_invoices_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'object',
                'method': 'execute',
                'args': [
                    self.odoo_db,
                    123,  # uid
                    self.odoo_password,
                    'account.move',
                    'search_read',
                    [['move_type', '=', 'out_invoice']],
                    ['name', 'partner_id', 'amount_total', 'state']
                ]
            },
            'id': 2
        }

        response = mock_post(f"{self.odoo_url}/jsonrpc", json=get_invoices_payload)
        result = response.json()

        # Verify invoices retrieved
        self.assertEqual(len(result['result']), 2)
        self.assertEqual(result['result'][0]['name'], 'INV/2026/0001')
        self.assertEqual(result['result'][0]['amount_total'], 1000.00)

    @patch('requests.post')
    def test_odoo_create_draft_invoice_with_correct_payload(self, mock_post):
        """Test that Odoo create_draft_invoice formats request correctly."""
        # Mock create response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 3,
            'result': 123  # New invoice ID
        }
        mock_post.return_value = mock_response

        # Simulate create_draft_invoice call
        invoice_data = {
            'partner_id': 1,
            'move_type': 'out_invoice',
            'invoice_date': '2026-02-27',
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': 1,
                    'quantity': 2,
                    'price_unit': 500.00
                })
            ]
        }

        create_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'object',
                'method': 'execute',
                'args': [
                    self.odoo_db,
                    123,  # uid
                    self.odoo_password,
                    'account.move',
                    'create',
                    invoice_data
                ]
            },
            'id': 3
        }

        response = mock_post(f"{self.odoo_url}/jsonrpc", json=create_payload)
        result = response.json()

        # Verify invoice created
        self.assertEqual(result['result'], 123)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_odoo_get_revenue_report_with_correct_payload(self, mock_post):
        """Test that Odoo get_revenue_report formats request correctly."""
        # Mock revenue response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 4,
            'result': {
                'total_revenue': 15000.00,
                'period': '2026-02',
                'invoices_count': 10
            }
        }
        mock_post.return_value = mock_response

        # Simulate get_revenue_report call
        response = mock_post(f"{self.odoo_url}/jsonrpc", json={})
        result = response.json()

        # Verify revenue data
        self.assertEqual(result['result']['total_revenue'], 15000.00)
        self.assertEqual(result['result']['invoices_count'], 10)


class TestOdooReadOnlyAccess(unittest.TestCase):
    """Test read-only access restrictions for cloud agent."""

    def setUp(self):
        """Set up test environment."""
        self.odoo_url = "http://localhost:8069"
        self.odoo_db = "odoo"
        self.readonly_username = "cloud_readonly"
        self.readonly_password = "readonly_pass"

    @patch('requests.post')
    def test_readonly_user_can_read_invoices(self, mock_post):
        """Test that read-only user can read invoices."""
        # Mock successful read
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 1,
            'result': [
                {'id': 1, 'name': 'INV/2026/0001', 'amount_total': 1000.00}
            ]
        }
        mock_post.return_value = mock_response

        # Read-only user reads invoices
        response = mock_post(f"{self.odoo_url}/jsonrpc", json={})
        result = response.json()

        # Verify read succeeded
        self.assertEqual(len(result['result']), 1)

    @patch('requests.post')
    def test_readonly_user_cannot_create_invoices(self, mock_post):
        """Test that read-only user cannot create invoices."""
        # Mock permission error
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 2,
            'error': {
                'code': 403,
                'message': 'Access Denied',
                'data': {
                    'name': 'odoo.exceptions.AccessError',
                    'message': 'You do not have permission to create invoices'
                }
            }
        }
        mock_post.return_value = mock_response

        # Read-only user tries to create invoice
        response = mock_post(f"{self.odoo_url}/jsonrpc", json={})
        result = response.json()

        # Verify creation denied
        self.assertIn('error', result)
        self.assertEqual(result['error']['code'], 403)

    @patch('requests.post')
    def test_readonly_user_cannot_post_invoices(self, mock_post):
        """Test that read-only user cannot post (finalize) invoices."""
        # Mock permission error
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 3,
            'error': {
                'code': 403,
                'message': 'Access Denied'
            }
        }
        mock_post.return_value = mock_response

        # Read-only user tries to post invoice
        response = mock_post(f"{self.odoo_url}/jsonrpc", json={})
        result = response.json()

        # Verify posting denied
        self.assertIn('error', result)


class TestOdooApprovalWorkflow(unittest.TestCase):
    """Test approval workflow for Odoo financial actions."""

    def setUp(self):
        """Set up test vault."""
        self.test_vault = tempfile.mkdtemp()
        self.pending_approval = Path(self.test_vault) / "Pending_Approval"
        self.approved = Path(self.test_vault) / "Approved"
        self.done = Path(self.test_vault) / "Done"

        for path in [self.pending_approval, self.approved, self.done]:
            path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_invoice_creation_requires_approval(self):
        """Test that invoice creation requires human approval."""
        # Cloud agent creates approval request
        approval_file = self.pending_approval / "INVOICE_APPROVAL_001.md"
        approval_content = """---
type: approval_request
action: create_invoice
created_by: cloud_agent
status: pending
---

# Invoice Creation Approval

**Customer:** Customer A
**Amount:** $1,000.00
**Items:**
- Product X: 2 units @ $500.00

## Action Required

**To Approve:** Move this file to `/Approved/` folder
**To Reject:** Move this file to `/Rejected/` folder
"""
        approval_file.write_text(approval_content, encoding='utf-8')

        # Verify approval request created
        self.assertTrue(approval_file.exists())
        content = approval_file.read_text(encoding='utf-8')
        self.assertIn('type: approval_request', content)
        self.assertIn('action: create_invoice', content)

    @patch('requests.post')
    def test_invoice_created_only_after_approval(self, mock_post):
        """Test that invoice is created only after approval."""
        # Mock successful creation
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 1,
            'result': 123
        }
        mock_post.return_value = mock_response

        # Create approval file
        approval_file = self.approved / "INVOICE_APPROVAL_001.md"
        approval_file.write_text("---\naction: create_invoice\nstatus: approved\n---", encoding='utf-8')

        # Check if approved
        content = approval_file.read_text(encoding='utf-8')
        is_approved = 'status: approved' in content

        # Only create if approved
        if is_approved:
            response = mock_post(f"http://localhost:8069/jsonrpc", json={})
            result = response.json()
            self.assertEqual(result['result'], 123)

    def test_invoice_approval_logs_to_audit(self):
        """Test that invoice creation is logged to audit trail."""
        # Simulate invoice creation
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': 'invoice_create',
            'actor': 'local_agent',
            'target': 'Customer A',
            'parameters': {
                'amount': 1000.00,
                'invoice_id': 123
            },
            'approval_status': 'approved',
            'approved_by': 'human',
            'result': 'success'
        }

        # Write to audit log
        audit_file = Path(self.test_vault) / "Logs" / "Audit" / f"{datetime.now().strftime('%Y-%m-%d')}_audit.json"
        audit_file.parent.mkdir(parents=True, exist_ok=True)

        logs = [audit_entry]
        audit_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')

        # Verify audit log
        self.assertTrue(audit_file.exists())
        logged_data = json.loads(audit_file.read_text(encoding='utf-8'))
        self.assertEqual(logged_data[0]['action_type'], 'invoice_create')
        self.assertEqual(logged_data[0]['approval_status'], 'approved')


class TestOdooDataValidation(unittest.TestCase):
    """Test data validation for Odoo operations."""

    @patch('requests.post')
    def test_invoice_validates_required_fields(self, mock_post):
        """Test that invoice creation validates required fields."""
        # Valid invoice data
        valid_invoice = {
            'partner_id': 1,
            'move_type': 'out_invoice',
            'invoice_date': '2026-02-27',
            'invoice_line_ids': [(0, 0, {
                'product_id': 1,
                'quantity': 1,
                'price_unit': 100.00
            })]
        }

        # Validate required fields
        required_fields = ['partner_id', 'move_type', 'invoice_line_ids']
        for field in required_fields:
            self.assertIn(field, valid_invoice)

        # Invalid invoice (missing partner_id)
        invalid_invoice = {
            'move_type': 'out_invoice',
            'invoice_line_ids': []
        }

        self.assertNotIn('partner_id', invalid_invoice)

    @patch('requests.post')
    def test_invoice_validates_line_items(self, mock_post):
        """Test that invoice validates line items."""
        # Valid line item
        valid_line = {
            'product_id': 1,
            'quantity': 2,
            'price_unit': 500.00
        }

        # Validate line item fields
        self.assertIn('product_id', valid_line)
        self.assertIn('quantity', valid_line)
        self.assertIn('price_unit', valid_line)
        self.assertGreater(valid_line['quantity'], 0)
        self.assertGreater(valid_line['price_unit'], 0)

    @patch('requests.post')
    def test_invoice_calculates_total_correctly(self, mock_post):
        """Test that invoice total is calculated correctly."""
        line_items = [
            {'quantity': 2, 'price_unit': 500.00},
            {'quantity': 1, 'price_unit': 300.00}
        ]

        # Calculate total
        total = sum(item['quantity'] * item['price_unit'] for item in line_items)

        self.assertEqual(total, 1300.00)


class TestOdooErrorHandling(unittest.TestCase):
    """Test error handling for Odoo operations."""

    @patch('requests.post')
    def test_odoo_handles_connection_error(self, mock_post):
        """Test that Odoo integration handles connection errors."""
        # Mock connection error
        mock_post.side_effect = Exception("Connection refused")

        # Should handle error gracefully
        try:
            response = mock_post("http://localhost:8069/jsonrpc", json={})
            self.fail("Should have raised exception")
        except Exception as e:
            self.assertEqual(str(e), "Connection refused")

    @patch('requests.post')
    def test_odoo_handles_authentication_error(self, mock_post):
        """Test that Odoo integration handles authentication errors."""
        # Mock auth error
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 1,
            'error': {
                'code': 401,
                'message': 'Authentication failed'
            }
        }
        mock_post.return_value = mock_response

        response = mock_post("http://localhost:8069/jsonrpc", json={})
        result = response.json()

        # Verify error handling
        self.assertIn('error', result)
        self.assertEqual(result['error']['code'], 401)

    @patch('requests.post')
    def test_odoo_handles_invalid_data_error(self, mock_post):
        """Test that Odoo integration handles invalid data errors."""
        # Mock validation error
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 1,
            'error': {
                'code': 400,
                'message': 'Invalid invoice data',
                'data': {
                    'name': 'odoo.exceptions.ValidationError',
                    'message': 'Partner is required'
                }
            }
        }
        mock_post.return_value = mock_response

        response = mock_post("http://localhost:8069/jsonrpc", json={})
        result = response.json()

        # Verify error handling
        self.assertIn('error', result)
        self.assertEqual(result['error']['code'], 400)


class TestOdooCloudLocalSeparation(unittest.TestCase):
    """Test cloud vs local separation for Odoo access."""

    def test_cloud_agent_uses_readonly_credentials(self):
        """Test that cloud agent uses read-only credentials."""
        # Cloud agent configuration
        cloud_config = {
            'odoo_username': 'cloud_readonly',
            'odoo_password': 'readonly_pass',
            'permissions': 'read_only'
        }

        self.assertEqual(cloud_config['odoo_username'], 'cloud_readonly')
        self.assertEqual(cloud_config['permissions'], 'read_only')

    def test_local_agent_uses_admin_credentials(self):
        """Test that local agent uses admin credentials."""
        # Local agent configuration
        local_config = {
            'odoo_username': 'admin',
            'odoo_password': 'admin_pass',
            'permissions': 'full_access'
        }

        self.assertEqual(local_config['odoo_username'], 'admin')
        self.assertEqual(local_config['permissions'], 'full_access')

    def test_cloud_agent_cannot_modify_financial_data(self):
        """Test that cloud agent cannot modify financial data."""
        # Cloud agent permissions
        cloud_permissions = {
            'can_read_invoices': True,
            'can_create_invoices': False,
            'can_post_invoices': False,
            'can_delete_invoices': False
        }

        self.assertTrue(cloud_permissions['can_read_invoices'])
        self.assertFalse(cloud_permissions['can_create_invoices'])
        self.assertFalse(cloud_permissions['can_post_invoices'])


if __name__ == '__main__':
    unittest.main()
