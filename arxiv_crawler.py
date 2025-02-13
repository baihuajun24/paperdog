import arxiv
import sqlite3
import config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import email
import datetime
import os
import smtplib
#CREATE TABLE IF NOT EXISTS arxiv (id TEXT, title TEXT,abstract TEXT, PRIMARY KEY (id),UNIQUE (ID))
def send_email(papers):
    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template("arxiv.template")
    
    # Generate email content
    email_html = template.render(papers=papers)
    
    # Debug print the content
    print("=== Email Content Preview ===")
    print(email_html)
    print("===========================")
    
    for subscriber in config.ARXIV_LIST["subscriber"]:
        smtp_server = config.SEND_EMAIL_SERVER
        smtp_port = config.SEND_EMAIL_PORT
        sender_email = config.SEND_EMAIL
        sender_password = config.SEND_EMAIL_PASSWORD
        receiver_email = subscriber["email"]
        subject = 'PageDog: New arxiv AI paper today'
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(email_html, 'html'))
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f'Email sent successfully to {receiver_email}')
        except Exception as e:
            print(f'Failed to send email: {e}')
        finally:
            server.quit()

import openai
from openai import OpenAI

client = OpenAI(
    base_url=config.OPENAI_URL,
    api_key=config.OPENAI_KEY,
)

def check_gpt(title:str,summary:str):
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a professional researcher and have read many papers. You are now chatting with a new paper's title and abstract. You must digest the topic well and answer user's questions precisely."
        },
        {
            "role": "user",
            "content": f"Title: {title}\nAbstract: {summary}\n\nFrom the above information, answer whether this paper is aimed at imporoving Machine Learning systems in terms of improving system throughput or reducing latency; exclude those papers that aim at improving the precision or accuracy. You should only return yes or no! ",
        }
    ],
    model="gpt-4o-mini-2024-07-18",
    max_tokens=100,
    )
    res=chat_completion.choices[0].message.content.lower()
    assert 'no' in res or 'yes' in res
    if('yes' in res):
       return True
    else:
        return False
    
import requests,re
session = requests.Session()
def pull_type(type_name:str):
    print(f"[DEBUG] Starting pull_type for {type_name}")
    local_db = sqlite3.connect(f"./content/{type_name[3:]}.db")
    cursor = local_db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS arxiv (id TEXT, title TEXT,abstract TEXT, reject BOOL DEFAULT 0, PRIMARY KEY (id))")
    local_db.commit()
    
    print(f"[DEBUG] Fetching arxiv listings for {type_name}")
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = session.get(
            f"https://arxiv.org/list/{type_name}/recent",
            # f"https://arxiv.org/list/{type_name}/recent?skip=0&show=2000",
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"[DEBUG] Response status code: {response.status_code}")
        print(f"[DEBUG] Response content length: {len(response.content)}")
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch arxiv listings. Status code: {response.status_code}")
            return []
            
        r = response.content.decode('utf-8')
        entries = re.findall(r'/abs/(\d+\.\d+)" title="Abstract"',r)
        print(f"[DEBUG] Found {len(entries)} papers in listing")
        
        # Print first few entries for debugging
        if entries:
            print(f"[DEBUG] First few entries: {entries[:3]}")
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch arxiv listings: {str(e)}")
        return []
    
    if(len(entries)==0):
        print("[DEBUG] No entries found, returning empty list")
        return []
        
    res = []
    batch_count = 0
    while(len(entries) > 0):
        batch_count += 1
        now_entries = entries[:10]
        entries = entries[10:]
        print(f"[DEBUG] Processing batch {batch_count}: {now_entries}")
        
        paper = arxiv.Search(id_list=now_entries)
        try:
            for result in paper.results():
                print(f"[DEBUG] Processing paper: {result.entry_id}")
                
                if("federated" in result.title.lower()):
                    print(f"[DEBUG] Skipping federated paper: {result.title}")
                    continue
                    
                # if local_db.execute("SELECT * FROM arxiv WHERE id=?",(result.entry_id,)).fetchone():
                #     print(f"[DEBUG] Paper exists in DB: {result.title}:{result.entry_id}")
                #     continue
                    
                try:
                    print(f"[DEBUG] Checking with GPT: {result.title}")
                    reject = check_gpt(result.title,result.summary)
                    print(f"[DEBUG] GPT decision for {result.entry_id}: {reject}")
                except Exception as e:
                    print(f"[DEBUG] GPT check failed with error: {e}")
                    exit(0)
                    
                if(reject):
                    print(f"[DEBUG] Adding paper to results: {result.entry_id}")
                    res.append(result)
                    
                print(f"[DEBUG] Inserting into DB: {result.entry_id}")
                local_db.execute("INSERT OR IGNORE INTO arxiv VALUES (?,?,?,?)",
                               (result.entry_id,result.title,result.summary,reject))
                local_db.commit()
                
        except Exception as e:
            print(f"[DEBUG] Batch processing error: {e}")
            local_db.commit()
        finally:
            local_db.commit()
            
    print(f"[DEBUG] pull_type complete. Found {len(res)} relevant papers")
    return res

def rank_and_summarize_papers(papers):
    if len(papers) == 0:
        return []
    
    # Convert papers to a format suitable for GPT
    paper_summaries = []
    for paper in papers:
        paper_summaries.append(f"Title: {paper.title}\nAbstract: {paper.summary}\nLink: {paper.entry_id}")
    
    prompt = """Analyze these ML system papers and:
1. Select the top 3 most significant papers focusing on system performance, efficiency, and scalability
2. For each selected paper, provide a brief reason for recommendation (1-2 sentences)
Format your response exactly like this:
0|This paper is important because it introduces a novel approach to reduce inference latency.
2|This work stands out for its scalable distributed training solution.
5|Notable for its memory optimization technique that reduces GPU memory by 50%.
"""
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a professional ML systems researcher who can identify important papers about system optimization, efficiency improvements, and scalability enhancements."
            },
            {
                "role": "user",
                "content": f"{prompt}\n\nPapers:\n" + "\n---\n".join(paper_summaries)
            }
        ],
        model="gpt-4o-mini-2024-07-18",
        max_tokens=300,
    )
    
    try:
        # Parse the response to get indices and reasons
        response_lines = chat_completion.choices[0].message.content.strip().split('\n')
        
        # Create a list to store all papers
        all_papers = papers.copy()  # Keep a copy of all papers
        
        # Track which papers are in top 3
        top_indices = []
        reasons = []
        
        # Process top 3 selections
        for line in response_lines[:3]:
            idx, reason = line.split('|')
            idx = int(idx.strip())
            if idx < len(papers):
                top_indices.append(idx)
                reasons.append(reason.strip())
        
        # Add recommendation reasons to top papers
        for idx, reason in zip(top_indices, reasons):
            all_papers[idx].recommendation_reason = reason
        
        # Reorder papers to put top 3 first
        top_papers = [all_papers[i] for i in top_indices]
        other_papers = [p for i, p in enumerate(all_papers) if i not in top_indices]
        
        # Return reordered list with top papers first, followed by others
        return top_papers + other_papers
        
    except Exception as e:
        print(f"[ERROR] Failed to rank papers: {e}")
        return papers  # Return original papers if ranking fails

def arxiv_crawl():
    print("[DEBUG] Starting arxiv_crawl()")
    papers = []
    for sub_type in config.ARXIV_LIST['types']:
        print(f"[DEBUG] Pulling papers for type: {sub_type}")
        papers.extend(pull_type(sub_type))
    print(f"[DEBUG] Total papers pulled: {len(papers)}")
    
    paper_map = {}
    for paper in papers:
        paper.author_str = ", ".join([author.name for author in paper.authors])
        paper_map[paper.entry_id] = paper
    print(f"[DEBUG] Unique papers after deduplication: {len(paper_map)}")
    
    papers = list(paper_map.values())
    if len(papers) > 0:
        print("[DEBUG] Starting paper ranking and summarization")
        top_papers = rank_and_summarize_papers(papers)
        print(f"[DEBUG] Got {len(top_papers)} top papers with reasons")
        
        # Get remaining papers
        top_paper_ids = {p.entry_id for p in top_papers}
        other_papers = [p for p in papers if p.entry_id not in top_paper_ids]
        print(f"[DEBUG] Other papers count: {len(other_papers)}")
        
        # Combine top papers and other papers
        papers = top_papers + other_papers
        print(f"[DEBUG] Sending email with total {len(papers)} papers")
        send_email(papers)
    else:
        print("[DEBUG] No papers found to process")
    
