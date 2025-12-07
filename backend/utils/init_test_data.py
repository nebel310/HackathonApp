from datetime import datetime, timedelta, timezone
import json

from repositories.user import UserRepository
from repositories.hackathon import HackathonRepository
from repositories.team import TeamRepository
from schemas.user import UserCreate, UserUpdate
from schemas.hackathon import HackathonCreate, HackathonSkillCreate
from schemas.team import TeamCreate, TeamInvitationCreate
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
        
        # Обновляем профиль администратора
        admin_update = UserUpdate(
            full_name="Администратор Системы",
            position="Главный администратор",
            about="Отвечаю за работу платформы хакатонов",
            contacts={"email": "admin@hackathon.ru", "telegram": "@admin_hack"}
        )
        await UserRepository.update_user(admin.id, admin_update)
        
        # Добавляем навыки администратору
        admin_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "DevOps"]
        for skill in admin_skills:
            try:
                from schemas.user import UserSkillCreate
                await UserRepository.add_user_skill(admin.id, UserSkillCreate(skill_name=skill))
            except ValueError:
                pass
        
        print(f"Тестовый администратор создан: {admin_username}")
        return admin
    else:
        print(f"Администратор уже существует: {admin_username}")
        return admin




async def create_test_users():
    """Создает тестовых пользователей."""
    test_users = [
        {
            "telegram_username": "ivan_dev",
            "full_name": "Иван Петров",
            "position": "Бэкенд разработчик",
            "about": "Занимаюсь разработкой на Python более 3 лет",
            "contacts": {"email": "ivan@example.com", "telegram": "@ivan_dev"},
            "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Docker"]
        },
        {
            "telegram_username": "anna_design",
            "full_name": "Анна Сидорова",
            "position": "UX/UI дизайнер",
            "about": "Создаю удобные интерфейсы для веб и мобильных приложений",
            "contacts": {"email": "anna@example.com", "telegram": "@anna_design"},
            "skills": ["Figma", "Adobe XD", "UI/UX", "Prototyping", "User Research"]
        },
        {
            "telegram_username": "alex_front",
            "full_name": "Алексей Иванов",
            "position": "Фронтенд разработчик",
            "about": "Люблю React и современный JavaScript",
            "contacts": {"email": "alex@example.com", "telegram": "@alex_front"},
            "skills": ["JavaScript", "React", "TypeScript", "Vue.js", "HTML/CSS"]
        },
        {
            "telegram_username": "maria_mobile",
            "full_name": "Мария Кузнецова",
            "position": "Мобильный разработчик",
            "about": "Разрабатываю приложения для iOS и Android",
            "contacts": {"email": "maria@example.com", "telegram": "@maria_mobile"},
            "skills": ["Swift", "Kotlin", "React Native", "Flutter", "Android SDK"]
        },
        {
            "telegram_username": "dmitry_data",
            "full_name": "Дмитрий Смирнов",
            "position": "Data Scientist",
            "about": "Работаю с большими данными и машинным обучением",
            "contacts": {"email": "dmitry@example.com", "telegram": "@dmitry_data"},
            "skills": ["Python", "Machine Learning", "TensorFlow", "Pandas", "SQL"]
        },
        {
            "telegram_username": "olga_devops",
            "full_name": "Ольга Васильева",
            "position": "DevOps инженер",
            "about": "Настраиваю инфраструктуру и CI/CD",
            "contacts": {"email": "olga@example.com", "telegram": "@olga_devops"},
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux"]
        },
        {
            "telegram_username": "sergey_fullstack",
            "full_name": "Сергей Николаев",
            "position": "Fullstack разработчик",
            "about": "Работаю как с фронтендом, так и с бэкендом",
            "contacts": {"email": "sergey@example.com", "telegram": "@sergey_fullstack"},
            "skills": ["JavaScript", "Python", "React", "FastAPI", "PostgreSQL"]
        },
        {
            "telegram_username": "ekaterina_qa",
            "full_name": "Екатерина Морозова",
            "position": "QA инженер",
            "about": "Тестирую приложения и ищу баги",
            "contacts": {"email": "ekaterina@example.com", "telegram": "@ekaterina_qa"},
            "skills": ["Manual Testing", "Automation", "Selenium", "Test Planning", "Bug Tracking"]
        }
    ]
    
    created_users = []
    for user_data in test_users:
        try:
            # Создаем пользователя
            user = await UserRepository.get_user_by_telegram_username(user_data["telegram_username"])
            if not user:
                user = await UserRepository.create_user(UserCreate(
                    telegram_username=user_data["telegram_username"]
                ))
            
            # Обновляем профиль
            user_update = UserUpdate(
                full_name=user_data["full_name"],
                position=user_data["position"],
                about=user_data["about"],
                contacts=user_data["contacts"]
            )
            await UserRepository.update_user(user.id, user_update)
            
            # Добавляем навыки
            for skill in user_data["skills"]:
                try:
                    from schemas.user import UserSkillCreate
                    await UserRepository.add_user_skill(user.id, UserSkillCreate(skill_name=skill))
                except ValueError:
                    pass
            
            created_users.append(user)
            print(f"Создан тестовый пользователь: {user_data['telegram_username']}")
        except Exception as e:
            print(f"Ошибка при создании пользователя {user_data['telegram_username']}: {e}")
    
    return created_users




async def create_test_hackathons():
    """Создает тестовые хакатоны."""
    now = datetime.now(timezone.utc)
    
    test_hackathons = [
        {
            "name": "AI Hackathon 2024",
            "description": "Соревнование по созданию инновационных решений в области искусственного интеллекта и машинного обучения. Участникам предстоит решать реальные задачи бизнеса с помощью AI.",
            "start_date": now + timedelta(days=10),
            "end_date": now + timedelta(days=12),
            "status": "registration",
            "min_team_size": 2,
            "max_team_size": 4,
            "skills": [
                {"skill_name": "Python", "priority": 1},
                {"skill_name": "Machine Learning", "priority": 1},
                {"skill_name": "Data Science", "priority": 2},
                {"skill_name": "TensorFlow", "priority": 3}
            ]
        },
        {
            "name": "Web Development Challenge",
            "description": "Хакатон по веб-разработке. Создайте современное веб-приложение с использованием современных технологий и фреймворков.",
            "start_date": now + timedelta(days=5),
            "end_date": now + timedelta(days=7),
            "status": "registration",
            "min_team_size": 3,
            "max_team_size": 5,
            "skills": [
                {"skill_name": "JavaScript", "priority": 1},
                {"skill_name": "React", "priority": 1},
                {"skill_name": "Python", "priority": 2},
                {"skill_name": "FastAPI", "priority": 2},
                {"skill_name": "PostgreSQL", "priority": 3}
            ]
        },
        {
            "name": "Mobile App Marathon",
            "description": "Разработайте мобильное приложение для решения социальных или бизнес-задач. Поддерживаются как нативные, так и кроссплатформенные решения.",
            "start_date": now - timedelta(days=2),
            "end_date": now + timedelta(days=1),
            "status": "in_progress",
            "min_team_size": 2,
            "max_team_size": 4,
            "skills": [
                {"skill_name": "Kotlin", "priority": 1},
                {"skill_name": "Swift", "priority": 1},
                {"skill_name": "React Native", "priority": 2},
                {"skill_name": "Flutter", "priority": 2}
            ]
        },
        {
            "name": "Blockathon: Blockchain Solutions",
            "description": "Хакатон посвященный разработке решений на блокчейне. Создавайте смарт-контракты, децентрализованные приложения и крипто-решения.",
            "start_date": now - timedelta(days=15),
            "end_date": now - timedelta(days=13),
            "status": "finished",
            "min_team_size": 2,
            "max_team_size": 4,
            "skills": [
                {"skill_name": "Solidity", "priority": 1},
                {"skill_name": "Blockchain", "priority": 1},
                {"skill_name": "Web3", "priority": 2},
                {"skill_name": "JavaScript", "priority": 3}
            ]
        }
    ]
    
    created_hackathons = []
    for hackathon_data in test_hackathons:
        try:
            # Создаем хакатон
            hackathon_create = HackathonCreate(
                name=hackathon_data["name"],
                description=hackathon_data["description"],
                start_date=hackathon_data["start_date"],
                end_date=hackathon_data["end_date"],
                status=hackathon_data["status"],
                min_team_size=hackathon_data["min_team_size"],
                max_team_size=hackathon_data["max_team_size"]
            )
            
            hackathon = await HackathonRepository.create_hackathon(hackathon_create)
            
            # Добавляем навыки хакатону
            for skill_data in hackathon_data["skills"]:
                try:
                    await HackathonRepository.add_hackathon_skill(
                        hackathon.id,
                        HackathonSkillCreate(**skill_data)
                    )
                except ValueError:
                    pass
            
            created_hackathons.append(hackathon)
            print(f"Создан тестовый хакатон: {hackathon_data['name']}")
        except Exception as e:
            print(f"Ошибка при создании хакатона {hackathon_data['name']}: {e}")
    
    return created_hackathons




async def create_test_registrations_and_teams(users, hackathons):
    """Создает тестовые регистрации и команды."""
    try:
        # Регистрируем пользователей на хакатоны
        for user in users:
            for hackathon in hackathons:
                try:
                    # Пропускаем завершенные хакатоны
                    if hackathon.status == "finished":
                        continue
                    
                    # Регистрируем пользователя на хакатон
                    from schemas.hackathon import HackathonRegistrationCreate
                    registration_data = HackathonRegistrationCreate(hackathon_id=hackathon.id)
                    
                    # Используем метод репозитория напрямую
                    await HackathonRepository.register_for_hackathon(hackathon.id, user.id)
                    print(f"Пользователь {user.telegram_username} зарегистрирован на хакатон {hackathon.name}")
                except ValueError as e:
                    # Пользователь уже зарегистрирован
                    pass
        
        # Создаем команды для активных хакатонов
        active_hackathons = [h for h in hackathons if h.status in ["registration", "in_progress"]]
        
        for hackathon in active_hackathons:
            # Создаем команду для AI Hackathon
            if "AI" in hackathon.name:
                captain = next((u for u in users if u.telegram_username == "dmitry_data"), None)
                if captain:
                    try:
                        team = await TeamRepository.create_team(
                            TeamCreate(
                                name="Data Wizards",
                                description="Команда экспертов в области данных и машинного обучения",
                                hackathon_id=hackathon.id
                            ),
                            captain.id
                        )
                        print(f"Создана команда Data Wizards для хакатона {hackathon.name}")
                        
                        # Добавляем участников в команду
                        team_members = [
                            next((u for u in users if u.telegram_username == "ivan_dev"), None),
                            next((u for u in users if u.telegram_username == "sergey_fullstack"), None)
                        ]
                        
                        for member in team_members:
                            if member and member.id != captain.id:
                                try:
                                    await TeamRepository.add_team_member(team.id, member.id)
                                    print(f"Пользователь {member.telegram_username} добавлен в команду Data Wizards")
                                except ValueError:
                                    pass
                    except ValueError as e:
                        print(f"Ошибка при создании команды для {hackathon.name}: {e}")
            
            # Создаем команду для Web Development Challenge
            elif "Web" in hackathon.name:
                captain = next((u for u in users if u.telegram_username == "alex_front"), None)
                if captain:
                    try:
                        team = await TeamRepository.create_team(
                            TeamCreate(
                                name="Code Masters",
                                description="Фронтенд и бэкенд разработчики, создающие современные веб-приложения",
                                hackathon_id=hackathon.id
                            ),
                            captain.id
                        )
                        print(f"Создана команда Code Masters для хакатона {hackathon.name}")
                        
                        # Добавляем участников в команду
                        team_members = [
                            next((u for u in users if u.telegram_username == "ivan_dev"), None),
                            next((u for u in users if u.telegram_username == "anna_design"), None),
                            next((u for u in users if u.telegram_username == "ekaterina_qa"), None)
                        ]
                        
                        for member in team_members:
                            if member and member.id != captain.id:
                                try:
                                    await TeamRepository.add_team_member(team.id, member.id)
                                    print(f"Пользователь {member.telegram_username} добавлен в команду Code Masters")
                                except ValueError:
                                    pass
                    except ValueError as e:
                        print(f"Ошибка при создании команды для {hackathon.name}: {e}")
            
            # Создаем команду для Mobile App Marathon
            elif "Mobile" in hackathon.name:
                captain = next((u for u in users if u.telegram_username == "maria_mobile"), None)
                if captain:
                    try:
                        team = await TeamRepository.create_team(
                            TeamCreate(
                                name="App Innovators",
                                description="Команда мобильных разработчиков, создающих кроссплатформенные приложения",
                                hackathon_id=hackathon.id
                            ),
                            captain.id
                        )
                        print(f"Создана команда App Innovators для хакатона {hackathon.name}")
                        
                        # Добавляем участников в команду
                        team_members = [
                            next((u for u in users if u.telegram_username == "olga_devops"), None),
                            next((u for u in users if u.telegram_username == "anna_design"), None)
                        ]
                        
                        for member in team_members:
                            if member and member.id != captain.id:
                                try:
                                    await TeamRepository.add_team_member(team.id, member.id)
                                    print(f"Пользователь {member.telegram_username} добавлен в команду App Innovators")
                                except ValueError:
                                    pass
                    except ValueError as e:
                        print(f"Ошибка при создании команды для {hackathon.name}: {e}")
        
        # Создаем тестовые приглашения
        web_hackathon = next((h for h in active_hackathons if "Web" in h.name), None)
        web_team = None
        
        if web_hackathon:
            # Находим команду Code Masters
            from database import new_session
            from sqlalchemy import select
            from models.team import TeamOrm
            
            async with new_session() as session:
                query = select(TeamOrm).where(
                    TeamOrm.hackathon_id == web_hackathon.id,
                    TeamOrm.name == "Code Masters"
                )
                result = await session.execute(query)
                web_team = result.scalars().first()
        
        if web_team:
            # Приглашаем пользователей в команду
            invitees = [
                next((u for u in users if u.telegram_username == "dmitry_data"), None),
                next((u for u in users if u.telegram_username == "maria_mobile"), None)
            ]
            
            captain = next((u for u in users if u.telegram_username == "alex_front"), None)
            
            for invitee in invitees:
                if invitee and captain:
                    try:
                        await TeamRepository.create_invitation(
                            TeamInvitationCreate(
                                team_id=web_team.id,
                                invitee_id=invitee.id,
                                message="Присоединяйтесь к нашей команде для веб-хакатона!"
                            ),
                            captain.id
                        )
                        print(f"Создано приглашение для {invitee.telegram_username} в команду Code Masters")
                    except ValueError as e:
                        print(f"Ошибка при создании приглашения для {invitee.telegram_username}: {e}")
    
    except Exception as e:
        print(f"Ошибка при создании тестовых регистраций и команд: {e}")




async def create_test_data():
    """
    Функция для создания тестовых данных.
    Вызывается в lifespan приложения.
    """
    print("Инициализация тестовых данных...")
    
    # Создаем тестового администратора
    admin = await init_test_admin()
    
    # Создаем тестовых пользователей
    users = await create_test_users()
    
    # Создаем тестовые хакатоны
    hackathons = await create_test_hackathons()
    
    # Создаем тестовые регистрации и команды
    await create_test_registrations_and_teams(users, hackathons)
    
    print("Тестовые данные успешно инициализированы")
    print(f"Всего создано: {len(users)} пользователей, {len(hackathons)} хакатонов")
    
    return {
        "admin": admin,
        "users": users,
        "hackathons": hackathons
    }