# AI News Tracker & Analyst Pipeline
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Load variables from .env file
load_dotenv()

client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

rss_sources_url = [
    "https://huggingface.co/blog/feed.xml",
    "https://hnrss.github.io/search?q=AI+OR+LLM+OR+RAG",
    "https://techcrunch.com/category/artificial-intelligence/feed/"
]

res = requests.get(rss_sources_url[2], headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(res.content, 'xml')
# print(soup.find_all('item'))
publish_date = soup.find('lastBuildDate').text
print(f"Published on: {publish_date}\n")
articles = soup.find_all('item')
# Extract and format the articles as plain text

article_texts = []
for item in articles[:5]:
    title = item.find('title').text if item.find('title') else ''
    author = item.find('dc:creator').text if item.find('dc:creator') else ''
    description = item.find('description').text if item.find('description') else ''
    source_link = item.find('guid').text.strip() if item.find('guid') and item.find('guid').text.strip() else ''
    article_texts.append(f"Title: {title}\nAuthor: {author}\nContent: {description}\nLink: {source_link}\n")

# Join all articles into a single string
articles_str = "\n---\n".join(article_texts)
# print(articles_str)

# content = soup.find('div', class_='article--viewer_content')
# if content:
#     for para in content.find_all('p'):
#         print(para.text.strip())
# else:
#     print('no article found')

def filter_message():
    print("Filtering raw articles...")
    SYSTEM_PROMPT = 'You are a data filtering assistant. ' \
    'Look at this text and extract only the title, author, core content of actual news articles, and link of art. ' \
    'Ignore ads and sidebar links. Output this as a clean Python list of dictionaries.' 
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": articles_str}
    ]

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
    )
    
    return response.choices[0].message.content


def agent_analyst():
    PROMPT = "You are an AI Solutions Architect. Distill the text into exactly 3 punchy developer insights.\n\n" \
        "Use this strict markdown format for each:\n" \
        "**[Tech Shift]**: What model/framework dropped and what changed.\n"\
        "**[Use-Case]**: One specific business automation or software tool to build with it.\n"\
        "**[Constraint]**: A brutal production truth (cost, latency, or RAG vs fine-tuning limit).\n\n"\
        "RULES: No intro, filler, or summary. Total output MUST be under 1900 characters."
    

    filtered_messages = filter_message()
    print("Processing and writing analysis report...")
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": filtered_messages}
    ]

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        stream=True
    )

    full_analysis = ''
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            # print(content, end="", flush=True) 
            full_analysis += content

    return full_analysis

def send_discord_message(webhook_url: str, content: str):
    print("Sending report over to Discord...")
    payload = {
        'content': content
    }
    try:
        response = requests.post(webhook_url, json=payload)

        if response.status_code in [200, 204]:
            return "Message sent successfully!"
        else:
            return "Failed to send message. Status code: " + str(response.status_code)
    except Exception as e:
        return "An error occurred: " + str(e)


if __name__ == "__main__":
    report = agent_analyst()
    # print(f'Type: {type(result)}')
    webhook_url=os.getenv('DISCORD_WEBHOOK_URL')

    result = send_discord_message(webhook_url, report[:1500])
    print('\n'+result)

    # output_path = os.path.join(os.path.dirname(__file__), 'AI.md')
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     f.write(result)


    



