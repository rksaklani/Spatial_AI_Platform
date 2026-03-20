"""
Multi-tenant data access layer.

Task 2.4: Multi-tenant data isolation
Provides a base repository class that enforces organization_id filtering
on all database operations to ensure data isolation between tenants.
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
import structlog

from utils.database import get_db

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class TenantRepository(Generic[T]):
    """
    Base repository class that enforces multi-tenant data isolation.
    
    All queries are automatically filtered by organization_id to ensure
    users can only access data belonging to their organization.
    
    Usage:
        class SceneRepository(TenantRepository):
            collection_name = "scenes"
        
        repo = SceneRepository(organization_id="org-123")
        scenes = await repo.find_many({"status": "completed"})
        # Automatically adds organization_id filter
    """
    
    collection_name: str = ""  # Override in subclass
    
    def __init__(self, organization_id: str):
        """
        Initialize repository with organization context.
        
        Args:
            organization_id: The organization ID to scope all queries to
        """
        if not organization_id:
            raise ValueError("organization_id is required for tenant repository")
        
        # SECURITY: Store org_id as private immutable attribute
        self._organization_id = organization_id
        self._db: Optional[AsyncIOMotorDatabase] = None
    
    @property
    def organization_id(self) -> str:
        """Get the organization ID (read-only)."""
        return self._organization_id
    
    @organization_id.setter
    def organization_id(self, value):
        """Prevent modification of organization_id after creation."""
        raise AttributeError("organization_id is immutable and cannot be changed")
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the MongoDB collection for this repository."""
        if not self.collection_name:
            raise NotImplementedError("collection_name must be set in subclass")
        
        if self._db is None:
            self._db = await get_db()
        
        return self._db[self.collection_name]
    
    def _inject_org_filter(self, filter_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Inject organization_id into filter to enforce tenant isolation.
        
        Args:
            filter_dict: Optional existing filter dictionary
            
        Returns:
            Filter dictionary with organization_id added
        """
        base_filter = {"organization_id": self.organization_id}
        
        if filter_dict:
            # Merge with existing filter
            base_filter.update(filter_dict)
        
        return base_filter
    
    def _inject_org_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject organization_id into document for insert operations.
        
        Args:
            document: Document to insert
            
        Returns:
            Document with organization_id added
        """
        doc_copy = document.copy()
        doc_copy["organization_id"] = self.organization_id
        return doc_copy
    
    async def find_one(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document with organization isolation.
        
        Args:
            filter_dict: Query filter
            **kwargs: Additional arguments for find_one
            
        Returns:
            Document if found, None otherwise
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        logger.debug(
            "tenant_find_one",
            collection=self.collection_name,
            organization_id=self.organization_id,
            filter=tenant_filter
        )
        
        return await collection.find_one(tenant_filter, **kwargs)
    
    async def find_by_id(self, document_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Find a document by ID with organization isolation.
        
        Args:
            document_id: The document's _id
            **kwargs: Additional arguments for find_one
            
        Returns:
            Document if found and belongs to organization, None otherwise
        """
        return await self.find_one({"_id": document_id}, **kwargs)
    
    async def find_many(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents with organization isolation.
        
        Args:
            filter_dict: Query filter
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: Sort specification
            **kwargs: Additional arguments for find
            
        Returns:
            List of documents
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        logger.debug(
            "tenant_find_many",
            collection=self.collection_name,
            organization_id=self.organization_id,
            filter=tenant_filter,
            skip=skip,
            limit=limit
        )
        
        cursor = collection.find(tenant_filter, **kwargs)
        
        if sort:
            cursor = cursor.sort(sort)
        
        cursor = cursor.skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents with organization isolation.
        
        Args:
            filter_dict: Query filter
            
        Returns:
            Count of matching documents
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        return await collection.count_documents(tenant_filter)
    
    async def insert_one(self, document: Dict[str, Any]) -> str:
        """
        Insert a document with organization_id automatically set.
        
        Args:
            document: Document to insert
            
        Returns:
            Inserted document's _id
        """
        collection = await self._get_collection()
        
        # Generate ID if not provided
        if "_id" not in document:
            document["_id"] = str(ObjectId())
        
        # Set timestamps
        now = datetime.utcnow()
        if "created_at" not in document:
            document["created_at"] = now
        if "updated_at" not in document:
            document["updated_at"] = now
        
        # Inject organization_id
        tenant_doc = self._inject_org_document(document)
        
        logger.debug(
            "tenant_insert_one",
            collection=self.collection_name,
            organization_id=self.organization_id,
            document_id=tenant_doc["_id"]
        )
        
        await collection.insert_one(tenant_doc)
        return tenant_doc["_id"]
    
    async def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents with organization_id automatically set.
        
        Args:
            documents: List of documents to insert
            
        Returns:
            List of inserted document IDs
        """
        collection = await self._get_collection()
        
        now = datetime.utcnow()
        tenant_docs = []
        
        for doc in documents:
            if "_id" not in doc:
                doc["_id"] = str(ObjectId())
            if "created_at" not in doc:
                doc["created_at"] = now
            if "updated_at" not in doc:
                doc["updated_at"] = now
            
            tenant_docs.append(self._inject_org_document(doc))
        
        logger.debug(
            "tenant_insert_many",
            collection=self.collection_name,
            organization_id=self.organization_id,
            count=len(tenant_docs)
        )
        
        await collection.insert_many(tenant_docs)
        return [doc["_id"] for doc in tenant_docs]
    
    async def update_one(
        self,
        filter_dict: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        Update a single document with organization isolation.
        
        Args:
            filter_dict: Query filter
            update: Update operations
            upsert: Whether to insert if not found
            
        Returns:
            Number of documents modified
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        # Add updated_at timestamp
        if "$set" in update:
            update["$set"]["updated_at"] = datetime.utcnow()
        else:
            update["$set"] = {"updated_at": datetime.utcnow()}
        
        # If upserting, ensure organization_id is set
        if upsert:
            if "$setOnInsert" not in update:
                update["$setOnInsert"] = {}
            update["$setOnInsert"]["organization_id"] = self.organization_id
            update["$setOnInsert"]["created_at"] = datetime.utcnow()
        
        logger.debug(
            "tenant_update_one",
            collection=self.collection_name,
            organization_id=self.organization_id,
            filter=tenant_filter
        )
        
        result = await collection.update_one(tenant_filter, update, upsert=upsert)
        return result.modified_count
    
    async def update_many(
        self,
        filter_dict: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents with organization isolation.
        
        Args:
            filter_dict: Query filter
            update: Update operations
            
        Returns:
            Number of documents modified
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        # Add updated_at timestamp
        if "$set" in update:
            update["$set"]["updated_at"] = datetime.utcnow()
        else:
            update["$set"] = {"updated_at": datetime.utcnow()}
        
        logger.debug(
            "tenant_update_many",
            collection=self.collection_name,
            organization_id=self.organization_id,
            filter=tenant_filter
        )
        
        result = await collection.update_many(tenant_filter, update)
        return result.modified_count
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete a single document with organization isolation.
        
        Args:
            filter_dict: Query filter
            
        Returns:
            Number of documents deleted
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        logger.debug(
            "tenant_delete_one",
            collection=self.collection_name,
            organization_id=self.organization_id,
            filter=tenant_filter
        )
        
        result = await collection.delete_one(tenant_filter)
        return result.deleted_count
    
    async def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete multiple documents with organization isolation.
        
        Args:
            filter_dict: Query filter
            
        Returns:
            Number of documents deleted
        """
        collection = await self._get_collection()
        tenant_filter = self._inject_org_filter(filter_dict)
        
        logger.debug(
            "tenant_delete_many",
            collection=self.collection_name,
            organization_id=self.organization_id,
            filter=tenant_filter
        )
        
        result = await collection.delete_many(tenant_filter)
        return result.deleted_count
    
    async def aggregate(
        self,
        pipeline: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Run aggregation pipeline with organization isolation.
        
        Automatically prepends a $match stage for organization_id.
        
        Args:
            pipeline: Aggregation pipeline
            **kwargs: Additional arguments for aggregate
            
        Returns:
            List of aggregation results
        """
        collection = await self._get_collection()
        
        # Prepend organization filter as first stage
        tenant_pipeline = [
            {"$match": {"organization_id": self.organization_id}}
        ] + pipeline
        
        logger.debug(
            "tenant_aggregate",
            collection=self.collection_name,
            organization_id=self.organization_id,
            pipeline_stages=len(pipeline)
        )
        
        cursor = collection.aggregate(tenant_pipeline, **kwargs)
        return await cursor.to_list(length=None)


# ============================================================================
# Concrete Repository Classes for Platform Entities
# ============================================================================

class SceneRepository(TenantRepository):
    """Repository for scene documents with tenant isolation."""
    collection_name = "scenes"


class ProcessingJobRepository(TenantRepository):
    """Repository for processing job documents with tenant isolation."""
    collection_name = "processing_jobs"


class SceneTileRepository(TenantRepository):
    """Repository for scene tile documents with tenant isolation."""
    collection_name = "scene_tiles"


class AnnotationRepository(TenantRepository):
    """Repository for annotation documents with tenant isolation."""
    collection_name = "annotations"


class GuidedTourRepository(TenantRepository):
    """Repository for guided tour documents with tenant isolation."""
    collection_name = "guided_tours"


class ShareTokenRepository(TenantRepository):
    """Repository for share token documents with tenant isolation."""
    collection_name = "share_tokens"


class SceneObjectRepository(TenantRepository):
    """Repository for scene object documents with tenant isolation."""
    collection_name = "scene_objects"


# ============================================================================
# Repository Factory
# ============================================================================

def get_repository(
    collection_name: str,
    organization_id: str
) -> TenantRepository:
    """
    Factory function to get a tenant repository for a collection.
    
    Args:
        collection_name: Name of the MongoDB collection
        organization_id: Organization ID for tenant isolation
        
    Returns:
        TenantRepository instance for the collection
    """
    repositories = {
        "scenes": SceneRepository,
        "processing_jobs": ProcessingJobRepository,
        "scene_tiles": SceneTileRepository,
        "annotations": AnnotationRepository,
        "guided_tours": GuidedTourRepository,
        "share_tokens": ShareTokenRepository,
        "scene_objects": SceneObjectRepository,
    }
    
    repo_class = repositories.get(collection_name)
    
    if repo_class:
        return repo_class(organization_id)
    
    # Generic repository for other collections
    class GenericRepository(TenantRepository):
        pass
    
    GenericRepository.collection_name = collection_name
    return GenericRepository(organization_id)
