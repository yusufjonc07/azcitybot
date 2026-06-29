from bson.objectid import ObjectId as BsonObjectId
from motor.motor_tornado import MotorClient, MotorCollection
from pydantic import BaseModel
import certifi

from data.config import MONGO_NAME, MONGO_URL

client = MotorClient(
    MONGO_URL, 
    ## Uncomment when using on your local machine
    # tlsCAFile=certifi.where()
)
db = client[MONGO_NAME]


class ObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, BsonObjectId):
            raise TypeError("ObjectId required")
        return str(v)


class Base(BaseModel):
    _collection: MotorCollection = None

    @classmethod
    async def count(cls):
        num = await cls._collection.count_documents({})
        return num

    @classmethod
    async def get_by(cls, **kwargs):
        obj = await cls._collection.find_one(kwargs)
        return cls(**obj) if obj else None
    
    @classmethod
    async def get(cls, id: int):
        obj = await cls._collection.find_one({"_id": id})
        return cls(**obj) if obj else None

    @classmethod
    async def get_all(cls):
        objs = cls._collection.find()
        result = []
        async for u in objs:
            try:
                result.append(cls(**u))
            except Exception as e:
                # Skip (don't crash the whole export/broadcast on) one bad doc
                print(f"Skipping invalid {cls.__name__} doc {u.get('_id')}: {e}")
        return result

    @classmethod
    async def update(cls, id: int, **kwargs):
        await cls._collection.find_one_and_update({"_id": id}, {"$set": kwargs})
        return await cls.get(id)

    @classmethod
    async def create(cls, **kwargs):
        # Use a counter collection for unique auto-increment IDs
        if "_id" not in kwargs:
            from database.base import db
            counter = await db["counters"].find_one_and_update(
                {"_id": cls._collection.name + "_id"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            kwargs["_id"] = counter["seq"]
        obj = cls(**kwargs)
        
        await cls._collection.insert_one(obj.model_dump(by_alias=True))
        return await cls.get(kwargs["_id"])

    @classmethod
    async def delete(cls, id: int):
        await cls._collection.find_one_and_delete({"_id": id})
        return True

    @classmethod
    def set_collection(cls, collection: str):
        cls._collection = db[collection]
