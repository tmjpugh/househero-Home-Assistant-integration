"""Constants for the House Hero integration."""

DOMAIN = "househero"

DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)

CONF_API_URL = "api_url"

# API paths
API_HOMES = "/api/homes"
API_TICKETS = "/api/tickets"
API_INVENTORY = "/api/inventory"

# Ticket status values (must match the strings stored in the House Hero database)
TICKET_STATUS_OPEN = "open"
TICKET_STATUS_IN_PROGRESS = "in-progress"
TICKET_STATUS_WAITING = "waiting"
TICKET_STATUS_CLOSED = "closed"

# Ticket priority values
TICKET_PRIORITY_HIGH = "high"
TICKET_PRIORITY_MEDIUM = "medium"
TICKET_PRIORITY_LOW = "low"

# Service names
SERVICE_CREATE_TICKET = "create_ticket"
