from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import asyncpg
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Task(BaseModel):
    id: int
    family_id: int
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=10, max_length=300)
    reward: int
    assigned_to: int
    created_at: datetime
class User(BaseModel):
    id: int
    name: str
    username: str
    balance: int
    family_id: Optional[int] = None
    role: str
    created_at: datetime

class TaskRepository:
    def __init__(self, db_pool):
        self.db_pool = db_pool
    async def add_family(self, name, user_id, invite_code):
    	try:
    		async with self.db_pool.acquire() as conn:
    			async with conn.transaction():
    				family_id = await conn.fetchval(
    				"INSERT INTO families(name, invite_code) RETURNING id", name, invite_code
    				)
    				await conn.execute(
    				"UPDATE users SET family_id = $1, role='parent' WHERE id = $2", family_id, user_id
    				)
    				return family_id
    	except Exception as e:
    		logger.critical(f"Ошибка при создании семьи: {e}")
    async def add_user(self, name, username, password_hash):
        try:
            async with self.db_pool.acquire() as conn:
                user_id = await conn.fetchval(
                    "INSERT INTO users(name, username, password_hash) VALUES($1, $2, $3) RETURNING id", name, username, password_hash
                )
                return user_id
        except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return False
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте добавления пользователя: {e}")
            return False
    async def add_task(self, title, description, reward, user_id, family_id):
        try:
            async with self.db_pool.acquire() as conn:
                task_id = await conn.fetchval(
                    "INSERT INTO tasks(title, description, reward, assigned_to, family_id) VALUES ($1, $2, $3, $4, $5) RETURNING id", title, description, reward, user_id, family_id
                )
                return task_id
        except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return False
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте добавления задачи: {e}")
            return False
    async def get_all_tasks(self, family_id: int):
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM tasks WHERE family_id = $1", family_id
                )
                return [Task(**dict(row)) for row in rows]
        except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return []
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте запроса данных: {e}")
            return None
            
    async def get_task(self, id: int):
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM tasks WHERE id = $1", id
                )
                if row is None:
                	return None
                return Task(**dict(row))
        except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return []
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте запроса данных: {e}")
            return None
    async def get_all_user(self, family_id):
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM users WHERE family_id = $1", family_id
                )
                return [User(**dict(row)) for row in rows]
        except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return []
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте запроса данных: {e}")
            return None
    async def update_budget(self, contribution, family_id):
    	try:
    		async with self.db_pool.acquire() as conn:
    			await conn.execute(
    				"UPDATE families SET budget = budget + $1 WHERE id = $2", contribution, family_id
    			)
    			return True
    	except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return False
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте изменения бюджета: {e}")
            return False
    async def get_user(self, id: int):
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1", id
                )
                return User(**dict(row))
        except (asyncpg.ConnectionDoesNotExistError, OSError) as e:
            logger.critical(f"Пропало соединение с базой: {e}")
            return None
        except Exception as e:
            logger.critical(f"Ошибка в базе данных на моменте запроса данных: {e}")
            return None