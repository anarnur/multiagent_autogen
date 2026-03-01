import os
import sys
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем промпты из твоего нового файла roles.py

PROMPT_OPTIMIST = """Ты - Техно-оптимист. Твоя задача — защищать инновации. 
Ты веришь, что технологии решают любые проблемы. Приводи примеры роста эффективности и прогресса. 
Будь энергичен и аргументирован."""

PROMPT_SKEPTIC = """Ты - Скептик. Твоя роль — выявлять риски, этические дилеммы и скрытые угрозы. 
Ты сомневаешься в безопасности бесконтрольного внедрения ИИ. 
Задавай неудобные вопросы о приватности и социальных последствиях."""

PROMPT_ANALYST = """Ты - Финансовый аналитик. Тебя интересуют только цифры, ROI и рыночная устойчивость. 
Оценивай затраты на внедрение и долгосрочную экономическую выгоду. Избегай эмоций, используй логику бизнеса."""

PROMPT_MODERATOR = """Ты - Модератор дебатов. Твоя задача:
1. Следить, чтобы дискуссия не уходила от темы.
2. Подводить промежуточные итоги после каждого раунда.
3. В конце дебатов (после 3 раундов) вынести финальное заключение, учитывая все точки зрения."""
# Загружаем переменные из .env (XAI_API_KEY)
load_dotenv()

# 1. Конфигурация для xAI (Grok)
llm_config = {
    "config_list": [
        {
            "model": "grok-3",
            "api_key": os.getenv("XAI_API_KEY"),
            "base_url": "https://api.x.ai/v1",
        }
    ],
    "temperature": 0.7,
}

# 2. Инициализация агентов
user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message="Организатор дебатов.",
    code_execution_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda x: "конец дебатов" in x.get("content", "").lower() # Кодовая фраза
)

optimist = autogen.AssistantAgent(
    name="Optimist",
    system_message=PROMPT_OPTIMIST,
    llm_config=llm_config,
)

skeptic = autogen.AssistantAgent(
    name="Skeptic",
    system_message=PROMPT_SKEPTIC,
    llm_config=llm_config,
)

analyst = autogen.AssistantAgent(
    name="Analyst",
    system_message=PROMPT_ANALYST,
    llm_config=llm_config,
)

moderator = autogen.AssistantAgent(
    name="Moderator",
    system_message=PROMPT_MODERATOR,
    llm_config=llm_config,
)

# 3. Кастомная функция выбора спикера (Расширенное требование)
def custom_speaker_selection(last_speaker, groupchat):
    messages = groupchat.messages

    # Если Модератор уже сказал финальное слово, заканчиваем
    if messages and "конец дебатов" in messages[-1]['content'].lower():
        return None
    """
    Определяет строгую последовательность: 
    Moderator -> Optimist -> Skeptic -> Analyst -> (цикл)
    """
    # Если это начало или говорит Admin, передаем слово Модератору
    if last_speaker == user_proxy or last_speaker is None:
        return moderator
    
    # Логика очереди
    if last_speaker == moderator:
        return optimist
    elif last_speaker == optimist:
        return skeptic
    elif last_speaker == skeptic:
        return analyst
    elif last_speaker == analyst:
        return moderator
    
    return moderator

# 4. Настройка GroupChat
groupchat = autogen.GroupChat(
    agents=[user_proxy, optimist, skeptic, analyst, moderator],
    messages=[],
    max_round=15,
    speaker_selection_method=custom_speaker_selection,
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# 5. Запуск дебатов
topic = "Заменит ли ИИ программистов в ближайшие 10 лет?"

print(f"--- Запуск дебатов на тему: {topic} ---")
user_proxy.initiate_chat(
    manager,
    message=f"Приветствую всех. Тема сегодняшних дебатов: '{topic}'. Модератор, представь участников и начинай."
)

# 6. Сохранение результата в Markdown (Требование проекта)
os.makedirs("output", exist_ok=True)
with open("output/debate_log.md", "w", encoding="utf-8") as f:
    f.write(f"# Протокол дебатов\n\n**Тема:** {topic}\n\n---\n\n")
    for msg in groupchat.messages:
        name = msg['name']
        content = msg['content']
        f.write(f"### {name}\n{content}\n\n")

print("\n--- Готово! Лог сохранен в output/debate_log.md ---")