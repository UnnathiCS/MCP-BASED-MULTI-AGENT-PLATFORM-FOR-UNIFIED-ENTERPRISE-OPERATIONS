from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from app.services.review_service import review_document
import logging
import io

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# LEGACY ENDPOINT (backward compatible)
# ============================================================================

@router.post("/review")
async def review(file: UploadFile):
    """
    Legacy document review endpoint.
    Accepts file upload and returns analysis.
    """
    result = await review_document(file)
    return result

# ============================================================================
# MCP COMPLIANT ENDPOINT
# ============================================================================

@router.post("/invoke")
async def invoke_mcp(payload: dict):
    """
    Standard MCP invocation endpoint for Document Review Agent.
    
    Request format:
    {
        "request_id": "uuid",
        "trace_id": "trace-xyz",
        "mcp_meta": {"policies": [...]},
        "payload": {
            "action": "document.review.file",
            "document": {
                "content": "base64-encoded PDF or text",
                "filename": "document.pdf",
                "mime_type": "application/pdf"
            },
            "options": {
                "include_suggestions": true,
                "check_policies": true
            }
        },
        "timeout_ms": 60000
    }
    
    Response format:
    {
        "request_id": "uuid",
        "agent_id": "document-review-agent",
        "status": "ok",
        "result": {
            "document_type": "NDA",
            "risk_level": "high",
            "compliance_score": 75.5,
            "clauses": [...],
            "suggestions": [...],
            "support_ticket": {...}
        },
        "suggested_actions": []
    }
    """
    try:
        request_id = payload.get("request_id", "unknown")
        trace_id = payload.get("trace_id", "unknown")
        mcp_payload = payload.get("payload", {})
        action = mcp_payload.get("action", "document.review.file")
        
        logger.info(f"[{trace_id}] Received MCP invocation: action={action}")
        
        if action != "document.review.file":
            return JSONResponse(
                status_code=400,
                content={
                    "request_id": request_id,
                    "agent_id": "document-review-agent",
                    "status": "error",
                    "error": f"Unknown action: {action}",
                    "suggested_actions": []
                }
            )
        
        # Extract document from payload
        document_data = mcp_payload.get("document", {})
        if not document_data or "content" not in document_data:
            return JSONResponse(
                status_code=400,
                content={
                    "request_id": request_id,
                    "agent_id": "document-review-agent",
                    "status": "error",
                    "error": "Missing required field: document.content",
                    "suggested_actions": []
                }
            )
        
        # Create a mock UploadFile-like object from the base64 content
        import base64
        from fastapi import UploadFile
        
        filename = document_data.get("filename", "document.pdf")
        content = document_data.get("content", "")
        
        # Decode base64 content
        try:
            file_bytes = base64.b64decode(content)
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "request_id": request_id,
                    "agent_id": "document-review-agent",
                    "status": "error",
                    "error": f"Invalid base64 content: {str(e)}",
                    "suggested_actions": []
                }
            )
        
        # Create a file-like object
        file_obj = io.BytesIO(file_bytes)
        
        # Create UploadFile-like object
        class MockUploadFile:
            def __init__(self, content, filename):
                self.file = io.BytesIO(content)
                self.filename = filename
                self.content_type = "application/pdf"
            
            async def read(self):
                return self.file.read()
            
            async def seek(self, offset):
                self.file.seek(offset)
        
        upload_file = MockUploadFile(file_bytes, filename)
        
        # Process document using existing service
        result = await review_document(upload_file)
        
        logger.info(f"[{trace_id}] Successfully analyzed document: {result.get('document_type')}")
        
        # Return standard MCP response
        return {
            "request_id": request_id,
            "agent_id": "document-review-agent",
            "status": "ok",
            "result": result,
            "suggested_actions": [
                {
                    "action": "review.request_support",
                    "condition": f"risk_level >= high",
                    "description": "Request support agent review for high-risk documents"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in invoke: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "request_id": payload.get("request_id", "unknown"),
                "agent_id": "document-review-agent",
                "status": "error",
                "error": str(e),
                "suggested_actions": []
            }
        )
