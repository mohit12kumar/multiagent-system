import os
import requests
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from src.monitoring.logger import logger

app = FastAPI(
    title="Label Studio Webhook Feedback Ingest Server",
    description="Listens to Label Studio annotation webhooks and synchronizes edits/approvals back to the pipeline database."
)

# API Endpoint of our primary Multi-Agent NER application
API_URL = os.getenv("PRIMARY_API_URL", "http://localhost:8000/api/v1")


@app.post("/webhook/label-studio")
async def label_studio_webhook(request: Request):
    """
    Receives events from Label Studio on annotation exports/webhooks.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("action", "")
    logger.info(f"Received Label Studio webhook event: {event}")

    # We look for annotation creation or updates
    if event in ("annotation_created", "annotation_updated"):
        annotation = payload.get("annotation", {})
        task = payload.get("task", {})

        # In Label Studio, when importing tasks we pass our internal entity_mention_id in task metadata
        task_data = task.get("data", {})
        entity_mention_id = task_data.get("entity_mention_id")

        if not entity_mention_id:
            logger.warning(
                "Received Label Studio annotation task without 'entity_mention_id'. Cannot link feedback.")
            return {"status": "ignored", "reason": "missing_entity_mention_id"}

        results = annotation.get("result", [])
        if not results:
            # If reviewer removed all labels, treat it as rejected
            logger.info(
                f"Reviewer removed annotations for entity mention {entity_mention_id}. Rejecting.")
            feedback_payload = {
                "entity_mention_id": entity_mention_id,
                "reviewer": annotation.get("completed_by", {}).get("email", "label_studio"),
                "action": "REJECTED"
            }
        else:
            # Extract corrected details
            # Typically label-studio results have a value with text and labels
            val = results[0].get("value", {})
            new_text = val.get("text")
            labels = val.get("labels", [])
            new_type = labels[0] if labels else None

            # Form feedback request
            # Check if text or label matches the original structure
            original_text = task_data.get("text")
            original_type = task_data.get("type")

            action = "APPROVED"
            if new_text != original_text or new_type != original_type:
                action = "MODIFIED"

            feedback_payload = {
                "entity_mention_id": entity_mention_id,
                "reviewer": str(annotation.get("completed_by", {}).get("email", "label_studio")),
                "action": action,
                "new_text": new_text,
                "new_type": new_type
            }

        # Submit feedback payload to our primary API server
        try:
            logger.info(
                f"Submitting feedback payload to NER API: {feedback_payload}")
            response = requests.post(
                f"{API_URL}/review/feedback", json=feedback_payload, timeout=5)
            response.raise_for_status()
            logger.info("Feedback successfully ingested")
            return {"status": "processed", "result": response.json()}
        except Exception as err:
            logger.error(f"Failed to push feedback to primary API: {err}")
            raise HTTPException(
                status_code=502, detail=f"Feedback sync failed: {err}")

    return {"status": "ignored", "reason": "unhandled_event_type"}

if __name__ == "__main__":
    # Start on port 8081
    uvicorn.run("feedback_ingest:app", host="0.0.0.0",
                port=8081, log_level="info")
