# 6. API Documentation

When running in server mode, the API documentation is available at:

- OpenAPI UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

## 6.1 API Endpoints

- `POST /api/query`: Submit a query to the agent
- `POST /api/search`: Search for CPT codes
- `POST /api/validate`: Validate a CPT code
- `POST /api/analyze`: Analyze a procedure description
- `GET /api/conversations`: List all conversations
- `GET /api/conversations/{session_id}`: Get a specific conversation
- `DELETE /api/conversations/{session_id}`: Delete a specific conversation
