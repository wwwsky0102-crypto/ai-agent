import os
import requests
import re  # We need this to hide DeepSeek's <think> tags
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI

# 1. Load your hidden secrets
YT_API_KEY = os.environ['YT_API_KEY']
HF_TOKEN = os.environ['HF_TOKEN']
EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

# 2. Ask YouTube for the top coding videos from the last 24 hours
yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat("T") + "Z"
url = "https://youtube.googleapis.com/youtube/v3/search"
params = {
    "part": "snippet",
    "q": "coding | programming | web development | python | AI",
    "order": "viewCount",
    "publishedAfter": yesterday,
    "maxResults": 5,
    "type": "video",
    "key": YT_API_KEY
}

print("Fetching videos from YouTube...")
response = requests.get(url, params=params).json()

if 'items' not in response or not response['items']:
    print("No new videos found in the last 24 hours. Exiting.")
    exit()

video_text = ""
for item in response.get("items", []):
    title = item["snippet"]["title"]
    video_id = item["id"]["videoId"]
    # Grab the high-quality thumbnail image URL
    thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
    video_text += f"Title: {title}\nLink: https://www.youtube.com/watch?v={video_id}\nThumbnail: {thumbnail}\n\n"

# 3. Sending data to AI Agent using your exact code
print("Sending data to AI Agent...")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# We ask the AI to specifically write HTML and CSS
prompt_message = f"""You are an expert developer. Read these YouTube videos. 
Filter out clickbait and write a beautifully formatted HTML email summarizing the best ones I should watch today. 

STRICT RULES:
1. Output ONLY valid HTML code. Do not use markdown like ```html.
2. Use professional, clean inline CSS (e.g., font-family: Arial; background-color: #f4f4f9; padding: 20px; border-radius: 10px;).
3. For EACH video, you MUST display its Thumbnail image using an HTML <img> tag (style="width: 100%; max-width: 320px; border-radius: 8px;").
4. Make the video Title a bold, clickable hyperlink.
5. Add a 1-sentence summary below each video.

Here is the video data:
{video_text}
"""

completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:novita",
    messages=[
        {
            "role": "user",
            "content": prompt_message
        }
    ],
)

# Extract the AI's response text
ai_response_text = completion.choices[0].message.content

# Remove DeepSeek-R1's <think> tags so they don't show up in your email
html_content = re.sub(r'<think>.*?</think>', '', ai_response_text, flags=re.DOTALL).strip()

# Remove markdown code blocks if the AI accidentally wraps the HTML
html_content = html_content.replace('```html', '').replace('```', '').strip()

# 4. Email the final newsletter to yourself
print("Sending email...")
msg = MIMEMultipart()
msg['From'] = EMAIL_ADDRESS
msg['To'] = EMAIL_ADDRESS
msg['Subject'] = "ðŸš€ Your DeepSeek AI Agent Report"

# THIS IS THE MAGIC: Change 'plain' to 'html' so Gmail renders the CSS and Images
msg.attach(MIMEText(html_content, 'html'))

# Connect to Gmail and send
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
server.send_message(msg)
server.quit()

print("Success! HTML Email delivered.")
