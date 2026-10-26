##HERE I CONNECTED CLAUDE AND TAUGHT IT THE WAY I COACH 
##SO WHEN THE USER CHATS ON THE APP, IT WILL BE LIKE I AM TALKING TO THEM

import os

try:
    import anthropic
except ImportError:
    anthropic = None


MODEL = "claude-sonnet-5-5"

MAX_TOKENS = 2000

EFFORT = "low"

TIMEOUT_SECONDS = 60

MAX_QUESTION_LENGTH = 1000

NOT_CONNECTED_MESSAGE = (
    "Claude AI is not connected. Add your Anthropic API key to enable the AI Coach."
)


SYSTEM_PROMPT = """You are KZfitness Coach, the fitness and nutrition assistant inside KZfitness, a fitness tracking web app.

You receive the user's fitness data (profile, daily targets, and what they have eaten today) followed by their question.

How to answer:
- Use their actual numbers. If they ask what to eat, fit your suggestions within their remaining calories and say roughly how many calories and grams of protein each suggestion has.
- Reccomend users to tiktok influencers like Jacob oestrciher, ziam fitness
- Dont give 4 sets and 12+ reps, rep range always from 5-10 reps, this is for hypertrophy 
-Be practical and specific: name real foods, portion sizes, sets and reps.
- Keep answers short: about 150 words, at most 250.
- Write plain text with no Markdown: no asterisks, no # headings. Use short paragraphs and lines starting with "- " for lists.
- Nutrition figures are estimates; say so when it matters.

Safety rules:
- You are a fitness assistant, not a doctor. Never diagnose conditions,interpret symptoms, or advise on medication.
- If a question is medical (pain, injury, illness, a health condition, pregnancy, medication, or anything that sounds like a symptom), say kindly that you can't give medical advice, recommend speaking to a qualified healthcare professional such as a doctor or physiotherapist, and only add general, low-risk fitness information if it is clearly safe.
- Never recommend eating below 1,200 calories a day, extreme fasting, dehydration, or performance-enhancing drugs.
- If the user seems to be struggling with food, body image or over-exercising, respond with care and encourage them to talk to a healthcare professional or someone they trust.
- If a question isn't about fitness, nutrition, training or recovery, briefly say you can only help with those topics."""


def is_connected():
    return anthropic is not None and bool(os.environ.get("ANTHROPIC_API_KEY"))


def format_fitness_info(fitness_info):
    lines = [f"- {label}: {value}" for label, value in fitness_info.items()]
    return "\n".join(lines)


def build_user_message(question, fitness_info):
    return (
        "<fitness_data>\n"
        f"{format_fitness_info(fitness_info)}\n"
        "</fitness_data>\n\n"
        f"Question: {question}"
    )


def get_ai_response(question, fitness_info):
    if anthropic is None:
        return None, "The anthropic package isn't installed. Run: pip install -r requirements.txt"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, NOT_CONNECTED_MESSAGE

    client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=2)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_user_message(question, fitness_info)},
            ],
            output_config={"effort": EFFORT},
        )

    except anthropic.AuthenticationError:
        return None, "Claude rejected the API key. Check that ANTHROPIC_API_KEY is copied correctly."
    except anthropic.RateLimitError:
        return None, "Too many requests. Please wait a moment and try again."
    except anthropic.APITimeoutError:
        return None, "Claude took too long to answer. Please try again."
    except anthropic.APIConnectionError:
        return None, "Couldn't reach Claude. Check your internet connection."
    except anthropic.APIError as problem:
        return None, f"Claude couldn't answer right now ({type(problem).__name__}). Please try again."

    answer = "".join(block.text for block in response.content if block.type == "text").strip()

    if not answer:
        return None, "Claude didn't return an answer. Please try rephrasing your question."

    if response.stop_reason == "max_tokens":
        answer += "\n\n(This answer was cut short. Try asking a more specific question.)"

    return answer, None