from repositories.user import UserRepository
from schemas.user import UserCreate
from models.user import UserRole




async def init_test_admin():
    """
    Инициализирует тестового администратора при запуске приложения.
    Создает администратора, если его не существует.
    """
    admin_username = "admin"
    
    # Проверяем, существует ли уже администратор
    admin = await UserRepository.get_user_by_telegram_username(admin_username)
    
    if not admin:
        # Создаем администратора
        user_data = UserCreate(telegram_username=admin_username)
        admin = await UserRepository.create_user(user_data)
        
        # Обновляем роль на администратора
        await UserRepository.update_user_role(admin.id, UserRole.ADMIN)
        
        print(f"Тестовый администратор создан: {admin_username}")
        return admin
    else:
        print(f"Администратор уже существует: {admin_username}")
        return admin




async def create_test_data():
    """
    Функция для создания тестовых данных.
    Вызывается в lifespan приложения.
    """
    print("Инициализация тестовых данных...")
    
    # Создаем тестового администратора
    admin = await init_test_admin()
    
    # Здесь можно добавить создание других тестовых данных
    if admin:
        print("Тестовые данные успешно инициализированы")
    else:
        print("Тестовые данные не были созданы")
    
    return admin