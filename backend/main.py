import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from database import create_tables
from database import delete_tables
from router.auth import router as auth_router
from router.profile import router as profile_router
from utils.init_test_data import create_test_data




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    await delete_tables()
    print('База очищена')
    
    await create_tables()
    print('База готова к работе')
    
    # Инициализируем тестовые данные
    await create_test_data()
    
    yield
    
    print('Выключение')




def custom_openapi():
    """Кастомная OpenAPI схема с настройками безопасности."""
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="Hackathon Platform API",
        version="1.0.0",
        description="""API платформы для организации хакатонов
    
**Особенности:**
- Упрощенная авторизация через Telegram username
- Управление профилем пользователя
- Система навыков (тегов)
- Роли пользователей (user/admin)

*Для доступа к защищенным эндпоинтам используйте JWT токен*""",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Защищаем все эндпоинты, кроме /auth/login и /auth/refresh
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if path not in ["/auth/login", "/auth/refresh"]:
                openapi_schema["paths"][path][method]["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    
    return app.openapi_schema




app = FastAPI(lifespan=lifespan)
app.openapi = custom_openapi




app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(auth_router)
app.include_router(profile_router)




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
        port=3001,
        host="0.0.0.0"
    )