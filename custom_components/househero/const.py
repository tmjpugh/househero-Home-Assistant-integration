"""Constants for the House Hero integration."""

DOMAIN = "househero"

DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)

CONF_API_URL = "api_url"

# API paths
API_HOMES = "/api/homes"
API_TICKETS = "/api/tickets"
API_INVENTORY = "/api/inventory"

# Ticket status values
TICKET_STATUS_OPEN = "open"
TICKET_STATUS_IN_PROGRESS = "in_progress"
TICKET_STATUS_CLOSED = "closed"

# Ticket priority values
TICKET_PRIORITY_HIGH = "high"
TICKET_PRIORITY_MEDIUM = "medium"
TICKET_PRIORITY_LOW = "low"
