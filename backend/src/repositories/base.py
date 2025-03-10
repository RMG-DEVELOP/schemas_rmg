from typing import TypeVar, Generic, Type, Optional, List,  Callable


from loguru import logger
from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import DatabaseError

from src.database._models import Base


ModelType = TypeVar("ModelType", bound=Base)

SessionFactory = Callable[[], async_sessionmaker[AsyncSession]]


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session_factory: SessionFactory):
        self.model = model
        self._session_factory = session_factory

    async def _create(self, **kwargs) -> ModelType:
        """Создает новый объект модели в базе данных.
        
        Args:
            session: Сессия базы данных
            **kwargs: Атрибуты для создания объекта
            
        Returns:
            Созданный объект модели
        """
        try:
            async with self._session_factory() as session:
                obj = self.model(**kwargs)
                session.add(obj)
                await session.commit()
                await session.refresh(obj)
                return obj
        except Exception as e:
            logger.error(f"Ошибка при создании {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось создать {self.model.__name__}") from e

    async def _get(self, **kwargs) -> Optional[ModelType]:
        """Получает один объект модели по заданным параметрам.
        
        Args:
            session: Сессия базы данных
            **kwargs: Параметры фильтрации
            
        Returns:
            Найденный объект или None
        """
        try:
            async with self._session_factory() as session:
                query = select(self.model).filter_by(**kwargs)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось получить {self.model.__name__}") from e
    
    async def _create_if_not_exists(self, **kwargs) -> ModelType:
        """Создает новый объект модели в базе данных, если он не существует.
        
        Args:
            session: Сессия базы данных
            **kwargs: Атрибуты для создания объекта 
            
        Returns:
            Созданный объект модели
        """
        try:
            obj = await self._get(**kwargs)
            created = False

            if not obj:
                obj = await self._create(**kwargs)
                created = True
            return obj, created
        
        except Exception as e:
            logger.error(f"Ошибка при создании объекта {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось создать объект {self.model.__name__}") from e

    async def _get_all(self, **kwargs) -> List[ModelType]:
        """Получает все объекты модели по заданным параметрам.
        
        Args:
            session: Сессия базы данных
            **kwargs: Параметры фильтрации
            
        Returns:
            Список найденных объектов
        """
        try:
            async with self._session_factory() as session:
                query = select(self.model).filter_by(**kwargs)
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении всех объектов {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось получить все объекты {self.model.__name__}") from e

    async def _update(self, obj: ModelType, **kwargs) -> ModelType:
        """Обновляет существующий объект модели.
        
        Args:
            session: Сессия базы данных
            obj: Объект для обновления
            **kwargs: Новые значения атрибутов
            
        Returns:
            Обновленный объект
        """
        try:
            async with self._session_factory() as session:
                for key, value in kwargs.items():
                    setattr(obj, key, value)
                    session.add(obj)
                    await session.commit()
                    await session.refresh(obj)
                    return obj
        except Exception as e:
            logger.error(f"Ошибка при обновлении объекта {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось обновить объект {self.model.__name__}") from e
    
    async def _delete(self, obj: ModelType) -> None:
        """Удаляет объект из базы данных.
        
        Args:
            session: Сессия базы данных
            obj: Объект для удаления
        """
        try:
            async with self._session_factory() as session:
                await session.delete(obj)
                await session.commit()  
        except Exception as e:
            logger.error(f"Ошибка при удалении объекта {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось удалить объект {self.model.__name__}") from e

    async def _exists(self, **kwargs) -> bool:
        """Проверяет существование объекта по id.
        
        Args:
            session: Сессия базы данных
            **kwargs: Должен содержать id для проверки
            
        Returns:
            True если объект существует, иначе False
        """
        try:
            async with self._session_factory() as session:
                query = select(exists().where(self.model.id == kwargs['id']))
                result = await session.execute(query)
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке существования объекта {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось проверить существование объекта {self.model.__name__}") from e

    async def _filter(self, **kwargs) -> List[ModelType]:
        """Фильтрует объекты по заданным параметрам.
        
        Args:
            session: Сессия базы данных
            **kwargs: Параметры фильтрации
            
        Returns:
            Список отфильтрованных объектов
        """
        try:
            async with self._session_factory() as session:
                query = select(self.model).filter_by(**kwargs)
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при фильтрации объектов {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось отфильтровать объекты {self.model.__name__}") from e
    
    async def _delete_all(self) -> None:
        """Удаляет все объекты модели."""
        try:
            async with self._session_factory() as session:
                stmt = delete(self.model)
                await session.execute(stmt)
                await session.commit()
                logger.success(f"Все объекты {self.model.__name__} успешно удалены")
        except Exception as e:
            logger.error(f"Ошибка при удалении всех объектов {self.model.__name__}: {e}")
            raise DatabaseError(f"Не удалось удалить все объекты {self.model.__name__}") from e
    

