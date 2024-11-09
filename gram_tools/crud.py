from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type, TypeVar, Generic, Optional, List

ModelType = TypeVar('ModelType')

class CRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def add(self, session: AsyncSession, instance: ModelType) -> None:
        try:
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
        except Exception as e:
            await session.rollback()
            raise e

    async def delete(self, session: AsyncSession, instance: ModelType) -> None:
        try:
            await session.delete(instance)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    async def update(self, session: AsyncSession, instance: ModelType, **kwargs) -> None:
        try:
            for attr, value in kwargs.items():
                setattr(instance, attr, value)
            await session.commit()
            await session.refresh(instance)
        except Exception as e:
            await session.rollback()
            raise e

    async def get(self, session: AsyncSession, **kwargs) -> Optional[ModelType]:
        query = select(self.model).filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_all(self, session: AsyncSession, **kwargs) -> List[ModelType]:
        query = select(self.model).filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_all_count(self, session: AsyncSession, **kwargs) -> int:
        query = select(func.count()).select_from(self.model).filter_by(**kwargs)
        result = await session.execute(query)
        return result.scalar()

def get_crud(model: Type[ModelType]) -> CRUD[ModelType]:
    return CRUD(model)
