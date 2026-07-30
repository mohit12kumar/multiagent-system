from typing import Dict, Any, List, Optional
from backend.database.mysql_store import MySQLStore
from src.monitoring.logger import logger


class HumanReviewAgent:
    def __init__(self, mysql_store: Optional[MySQLStore] = None):
        self.mysql_store = mysql_store

    def get_pending_queue(self) -> List[Dict[str, Any]]:
        logger.info("Human Review Agent fetching pending review items")
        return self.mysql_store.get_pending_review_queue()

    def approve_item(self, review_id: str, reviewer: str) -> bool:
        logger.info(f"Human Review Agent approving review item {review_id} by doctor {reviewer}")
        return self.mysql_store.resolve_review_item(review_id, "APPROVED", reviewer)

    def reject_item(self, review_id: str, reviewer: str) -> bool:
        logger.info(f"Human Review Agent rejecting review item {review_id} by doctor {reviewer}")
        return self.mysql_store.resolve_review_item(review_id, "REJECTED", reviewer)

    def modify_item(self, review_id: str, reviewer: str, new_value: str) -> bool:
        logger.info(f"Human Review Agent modifying review item {review_id} by doctor {reviewer} to '{new_value}'")
        return self.mysql_store.resolve_review_item(review_id, "MODIFIED", reviewer, new_value=new_value)

    def approve_all(self, reviewer: str) -> int:
        logger.info(f"Human Review Agent executing batch Approve All by doctor {reviewer}")
        return self.mysql_store.approve_all_pending_reviews(reviewer)
