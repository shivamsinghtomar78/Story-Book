"""Story model for MongoDB."""
from datetime import datetime
from typing import List, Dict, Optional
from pymongo.collection import Collection
from bson import ObjectId
from app.utils.logging_config import get_logger

logger = get_logger('story_model')


class Story:
    """Story model for database operations."""
    
    def __init__(self, collection: Collection):
        """Initialize with MongoDB collection.
        
        Args:
            collection: MongoDB collection for stories
        """
        self.collection = collection
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create database indexes for performance."""
        try:
            # Index for user queries
            self.collection.create_index([("user_id", 1), ("created_at", -1)])
            
            # Index for search
            self.collection.create_index([("title", "text"), ("prompt", "text")])
            
            # Index for favorites
            self.collection.create_index([("user_id", 1), ("is_favorite", 1)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation skipped: {e}")
    
    def create(self, user_id: str, story_data: Dict) -> str:
        """Create a new story in the database.
        
        Args:
            user_id: User ID from JWT token
            story_data: Story information
        
        Returns:
            Inserted story ID as string
        """
        document = {
            "user_id": user_id,
            "story_id": story_data.get("story_id"),
            "title": story_data.get("title", "Untitled Story"),
            "prompt": story_data.get("prompt", ""),
            "story_length": story_data.get("story_length", "normal"),
            "story_mode": story_data.get("story_mode", "standard"),
            "story_data": story_data.get("story", {}),
            "image_files": story_data.get("image_files", []),
            "audio_files": story_data.get("audio_files", []),
            "pdf_file": story_data.get("pdf_file"),
            "is_favorite": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "view_count": 0,
            "tags": []
        }
        
        result = self.collection.insert_one(document)
        logger.info(f"Story created: {result.inserted_id}", extra={
            "user_id": user_id,
            "story_id": story_data.get("story_id")
        })
        
        return str(result.inserted_id)
    
    def find_by_user(self, user_id: str, skip: int = 0, limit: int = 20,
                     sort_by: str = "created_at", sort_order: int = -1,
                     favorites_only: bool = False) -> tuple:
        """Find stories by user ID with pagination.
        
        Args:
            user_id: User ID
            skip: Number of documents to skip
            limit: Maximum documents to return
            sort_by: Field to sort by
            sort_order: 1 for ascending, -1 for descending
            favorites_only: Only return favorited stories
        
        Returns:
            Tuple of (stories list, total count)
        """
        query = {"user_id": user_id}
        
        if favorites_only:
            query["is_favorite"] = True
        
        total = self.collection.count_documents(query)
        
        cursor = self.collection.find(query)\
            .sort(sort_by, sort_order)\
            .skip(skip)\
            .limit(limit)
        
        stories = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        for story in stories:
            story["_id"] = str(story["_id"])
            if "created_at" in story:
                story["created_at"] = story["created_at"].isoformat()
            if "updated_at" in story:
                story["updated_at"] = story["updated_at"].isoformat()
        
        logger.info(f"Retrieved {len(stories)} stories for user", extra={
            "user_id": user_id,
            "total": total
        })
        
        return stories, total
    
    def find_by_id(self, story_id: str, user_id: str) -> Optional[Dict]:
        """Find a story by ID.
        
        Args:
            story_id: MongoDB document ID
            user_id: User ID for authorization
        
        Returns:
            Story document or None
        """
        try:
            query = {
                "_id": ObjectId(story_id),
                "user_id": user_id
            }
            
            story = self.collection.find_one(query)
            
            if story:
                # Increment view count
                self.collection.update_one(
                    {"_id": ObjectId(story_id)},
                    {"$inc": {"view_count": 1}}
                )
                
                # Convert ObjectId to string
                story["_id"] = str(story["_id"])
                if "created_at" in story:
                    story["created_at"] = story["created_at"].isoformat()
                if "updated_at" in story:
                    story["updated_at"] = story["updated_at"].isoformat()
                
                logger.info(f"Story retrieved: {story_id}")
            
            return story
        
        except Exception as e:
            logger.error(f"Error finding story: {e}")
            return None
    
    def update(self, story_id: str, user_id: str, updates: Dict) -> bool:
        """Update a story.
        
        Args:
            story_id: MongoDB document ID
            user_id: User ID for authorization
            updates: Fields to update
        
        Returns:
            True if updated, False otherwise
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(story_id), "user_id": user_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Story updated: {story_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error updating story: {e}")
            return False
    
    def delete(self, story_id: str, user_id: str) -> bool:
        """Delete a story.
        
        Args:
            story_id: MongoDB document ID
            user_id: User ID for authorization
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({
                "_id": ObjectId(story_id),
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Story deleted: {story_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error deleting story: {e}")
            return False
    
    def toggle_favorite(self, story_id: str, user_id: str) -> Optional[bool]:
        """Toggle favorite status.
        
        Args:
            story_id: MongoDB document ID
            user_id: User ID for authorization
        
        Returns:
            New favorite status or None
        """
        try:
            # Get current status
            story = self.collection.find_one({
                "_id": ObjectId(story_id),
                "user_id": user_id
            })
            
            if not story:
                return None
            
            new_status = not story.get("is_favorite", False)
            
            self.collection.update_one(
                {"_id": ObjectId(story_id)},
                {"$set": {"is_favorite": new_status, "updated_at": datetime.utcnow()}}
            )
            
            logger.info(f"Story favorite toggled: {story_id} -> {new_status}")
            
            return new_status
        
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return None
    
    def search(self, user_id: str, query: str, skip: int = 0, limit: int = 20) -> tuple:
        """Search stories by text.
        
        Args:
            user_id: User ID
            query: Search query
            skip: Number of documents to skip
            limit: Maximum documents to return
        
        Returns:
            Tuple of (stories list, total count)
        """
        search_filter = {
            "user_id": user_id,
            "$text": {"$search": query}
        }
        
        total = self.collection.count_documents(search_filter)
        
        cursor = self.collection.find(search_filter)\
            .skip(skip)\
            .limit(limit)
        
        stories = list(cursor)
        
        # Convert ObjectId to string
        for story in stories:
            story["_id"] = str(story["_id"])
            if "created_at" in story:
                story["created_at"] = story["created_at"].isoformat()
            if "updated_at" in story:
                story["updated_at"] = story["updated_at"].isoformat()
        
        logger.info(f"Search completed: '{query}' found {len(stories)} results")
        
        return stories, total
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for a user's stories.
        
        Args:
            user_id: User ID
        
        Returns:
            Statistics dictionary
        """
        total = self.collection.count_documents({"user_id": user_id})
        favorites = self.collection.count_documents({
            "user_id": user_id,
            "is_favorite": True
        })
        
        # Get most recent story
        recent = self.collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        
        stats = {
            "total_stories": total,
            "total_favorites": favorites,
            "last_created": recent["created_at"].isoformat() if recent else None
        }
        
        return stats


# Singleton instance
_story_model = None


def get_story_model(collection: Collection = None) -> Story:
    """Get or create Story model singleton.
    
    Args:
        collection: MongoDB collection (required on first call)
    
    Returns:
        Story model instance
    """
    global _story_model
    if _story_model is None:
        if collection is None:
            raise ValueError("Collection required for first initialization")
        _story_model = Story(collection)
    return _story_model
