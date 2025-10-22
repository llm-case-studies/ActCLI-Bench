# ActCLI-Bench API Documentation

## Overview

This directory contains API specifications for ActCLI-Bench's integration with external systems, particularly the **Round Table** public AI debate platform.

## Files

### `round-table-openapi.yaml`
OpenAPI 3.0 specification for the Round Table integration API.

**Source:** Copied from `/home/alex/Projects/ActCLI-Round-Table/openapi.yaml`

**Status:** 🚧 **Reference spec** - ActCLI-Bench does not yet implement this API

**Purpose:**
- Documents the REST API that ActCLI-Bench must expose
- Defines session management endpoints
- Specifies transcript streaming format
- Used by scheduler and frontend developers

**Key Endpoints:**
- `POST /api/sessions` - Create a debate session
- `GET /api/sessions/{id}` - Get session status
- `GET /api/sessions/{id}/stream` - Stream live transcript
- `GET /api/sessions/active` - List running sessions

**View:**
- Raw YAML: [round-table-openapi.yaml](./round-table-openapi.yaml)
- Rendered docs: Use [Swagger Editor](https://editor.swagger.io/) or [Redoc](https://github.com/Redocly/redoc)

## Implementation Status

**Current:** ActCLI-Bench is a TUI application with no HTTP API.

**Planned:** See [round-table-integration.md](../round-table-integration.md) for integration roadmap.

## Development Workflow

1. **API Design** - Update `round-table-openapi.yaml` when adding endpoints
2. **Mock Backend** - Test frontend against mock (see Round Table repo)
3. **Implementation** - Build actual API in ActCLI-Bench
4. **Integration** - Connect scheduler and frontend to real backend

## Testing

**Mock Backend:**
Located in `/home/alex/Projects/ActCLI-Round-Table/mock_backend/`

```bash
# Start mock server
cd /home/alex/Projects/ActCLI-Round-Table/mock_backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/api/
curl http://localhost:8000/api/topics
```

## References

- [Round Table Integration Spec](../round-table-integration.md) - Overall integration plan
- [Round Table README](/home/alex/Projects/ActCLI-Round-Table/README.md) - Vision and roadmap
- [Frontend Spec](/home/alex/Projects/ActCLI-Round-Table/frontend_spec.md) - UI requirements
