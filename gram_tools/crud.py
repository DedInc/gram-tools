from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type, TypeVar, Generic, Optional, List, Union, Sequence, Any

ModelType = TypeVar('ModelType')

class CRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def add(self, session: AsyncSession, instances: Union[ModelType, Sequence[ModelType], None] = None, **kwargs) -> ModelType:
        try:
            if instances is None and kwargs:
                instances = self.model(**kwargs)
            
            if isinstance(instances, Sequence) and not isinstance(instances, (str, bytes)):
                session.add_all(instances)
            else:
                session.add(instances)
            await session.commit()
            
            if isinstance(instances, Sequence) and not isinstance(instances, (str, bytes)):
                for instance in instances:
                    await session.refresh(instance)
            else:
                await session.refresh(instances)
                
            return instances
        except Exception as e:
            await session.rollback()
            raise e

    async def delete(self, session: AsyncSession, instances: Union[ModelType, Sequence[ModelType]]) -> None:
        try:
            if isinstance(instances, Sequence) and not isinstance(instances, (str, bytes)):
                for instance in instances:
                    await session.delete(instance)
            else:
                await session.delete(instances)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    async def update(self, session: AsyncSession, instances: Union[ModelType, Sequence[ModelType]], **kwargs) -> None:
        try:
            if isinstance(instances, Sequence) and not isinstance(instances, (str, bytes)):
                for instance in instances:
                    for attr, value in kwargs.items():
                        setattr(instance, attr, value)
            else:
                for attr, value in kwargs.items():
                    setattr(instances, attr, value)
            await session.commit()
            if isinstance(instances, Sequence) and not isinstance(instances, (str, bytes)):
                for instance in instances:
                    await session.refresh(instance)
            else:
                await session.refresh(instances)
        except Exception as e:
            await session.rollback()
            raise e

    async def get(self, session: AsyncSession, *expressions: Any, **kwargs) -> Optional[ModelType]:
        query = select(self.model)
        if expressions:
            query = query.filter(*expressions)
        if kwargs:
            query = query.filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_all(self, session: AsyncSession, *expressions: Any, **kwargs) -> List[ModelType]:
        query = select(self.model)
        if expressions:
            query = query.filter(*expressions)
        if kwargs:
            query = query.filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_all_count(self, session: AsyncSession, *expressions: Any, **kwargs) -> int:
        query = select(func.count()).select_from(self.model)
        if expressions:
            query = query.filter(*expressions)
        if kwargs:
            query = query.filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalar()

def get_crud(model: Type[ModelType]) -> CRUD[ModelType]:
    return CRUD(model)
