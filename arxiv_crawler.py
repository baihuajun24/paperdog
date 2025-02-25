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
from volcenginesdkarkruntime import Ark
import requests
from loguru import logger
import re

#CREATE TABLE IF NOT EXISTS arxiv (id TEXT, title TEXT,abstract TEXT, PRIMARY KEY (id),UNIQUE (ID))
def send_email(papers, stats=None):
    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template("arxiv.template")
    
    # Split papers into top papers and others
    top_papers = [p for p in papers if hasattr(p, 'recommendation_reason')]
    other_papers = [p for p in papers if not hasattr(p, 'recommendation_reason')]
    
    print(f"[DEBUG] Email will contain {len(top_papers)} top papers and {len(other_papers)} other papers")
    
    # Debug the first top paper if available
    if top_papers:
        print(f"[DEBUG] First top paper: {top_papers[0].title}")
        print(f"[DEBUG] First top paper reason: {getattr(top_papers[0], 'recommendation_reason', 'No reason')}")
    
    # Generate email content
    email_html = template.render(
        papers=papers,
        top_papers=top_papers,
        other_papers=other_papers,
        stats=stats
    )
    
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
        
        # Modify the email subject
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        subject = f"PaperDogV1[{current_date}]: New Papers from Arxiv Today"
        
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

# client = OpenAI(
#     base_url=config.OPENAI_URL,
#     api_key=config.OPENAI_KEY,
# )

client = Ark(
    base_url=config.ARK_URL,
    api_key=config.ARK_KEY,
)

def check_model_response(model_name):
    # Send a simple query to the model to check its response
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Who are you? And who developed you?"
                }
            ],
            model=model_name,
            max_tokens=30,
        )
        response = completion.choices[0].message.content.strip()
        print(f"Model response: {response}")
    except Exception as e:
        print(f"Error checking model response: {e}")

def check_gpt(title:str,summary:str, comment:str, model_name="deepseek-v3-241226"):
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": config.AGENT_PROMPT
        },
        {
            "role": "user",
            "content": config.CLASSIFY_PROMPT.format(title=title, summary=summary, comment=comment)
        }
    ],
    # model="gpt-4o-mini-2024-07-18",
    model=model_name,
    max_tokens=100,
    )
    res=chat_completion.choices[0].message.content.lower()
    assert 'no' in res or 'yes' in res
    if('yes' in res):
       return True
    else:
        return False
    
session = requests.Session()
def pull_type(type_name:str, model_name="deepseek-v3-241226", stats=None):
    print(f"[DEBUG] Starting pull_type for {type_name}")
    local_db = sqlite3.connect(f"./content/{type_name[3:]}_plus.db")
    cursor = local_db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS arxiv (id TEXT, title TEXT,abstract TEXT, comment TEXT, relevant BOOL DEFAULT 0, PRIMARY KEY (id))")
    local_db.commit()
    
    print(f"[DEBUG] Fetching arxiv listings for {type_name}")
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = session.get(
            # f"https://arxiv.org/list/{type_name}/recent", # debug use
            f"https://arxiv.org/list/{type_name}/recent?skip=0&show=2000", # deploy use
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
        total_retrieved = len(entries)  # This is the total count of papers retrieved
        print(f"[DEBUG] Found {total_retrieved} papers in listing")
        
        # Update stats if provided
        if stats is not None:
            stats['total_retrieved'] += total_retrieved
            if type_name not in stats['by_type']:
                stats['by_type'][type_name] = {'retrieved': total_retrieved, 'selected': 0}
            else:
                stats['by_type'][type_name]['retrieved'] = total_retrieved
        
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
            # Convert the iterator to a list to process it
            paper_results = list(paper.results())
            
            for result in paper_results:
                if("federated" in result.title.lower()):
                    print(f"[DEBUG] Skipping federated paper: {result.title}")
                    continue
                    
                # if local_db.execute("SELECT * FROM arxiv WHERE id=?",(result.entry_id,)).fetchone():
                #     print(f"[DEBUG] Paper exists in DB: {result.title}:{result.entry_id}")
                #     continue
                    
                try:
                    print(f"[DEBUG] Checking with GPT: {result.title}")
                    relevant = check_gpt(result.title, result.summary, result.comment, model_name)
                    print(f"[DEBUG] GPT decision for {result.entry_id}: {relevant}")
                except Exception as e:
                    print(f"[DEBUG] GPT check failed with error: {e}")
                    exit(0)
                    
                if(relevant):
                    print(f"[DEBUG] Adding paper to results: {result.entry_id}")
                    res.append(result)
                    # Update selected count in stats
                    if stats is not None:
                        stats['total_selected'] += 1
                        stats['by_type'][type_name]['selected'] += 1
                    
                print(f"[DEBUG] Inserting into DB: {result.entry_id}")
                # Include the comment in the database insertion
                local_db.execute("INSERT OR IGNORE INTO arxiv VALUES (?,?,?,?,?)",
                                 (result.entry_id, result.title, result.summary, result.comment, relevant))
                # local_db.execute("INSERT OR IGNORE INTO arxiv VALUES (?,?,?,?)",
                #                (result.entry_id,result.title,result.summary,relevant))
                local_db.commit()
                
        except Exception as e:
            print(f"[DEBUG] Batch processing error: {e}")
            local_db.commit()
        finally:
            local_db.commit()
            
    print(f"[DEBUG] pull_type complete. Found {len(res)} relevant papers out of {total_retrieved} total")
    return res
            
    print(f"[DEBUG] pull_type complete. Found {len(res)} relevant papers")
    return res

def parse_recommendations(response_lines):
    top_indices = []
    reasons = []
    current_reason = []

    for line in response_lines:
        if '|' in line:
            # If there's a current reason being built, save it
            if current_reason:
                reasons.append(' '.join(current_reason).strip())
                current_reason = []

            # Parse the index
            idx, _ = line.split('|', 1)
            idx = int(idx.strip())
            top_indices.append(idx)
        else:
            # Collect reason lines
            current_reason.append(line.strip())

    # Append the last reason if it exists
    if current_reason:
        reasons.append(' '.join(current_reason).strip())

    return top_indices, reasons

def rank_and_summarize_papers(papers, model_name="deepseek-v3-241226"):
    if len(papers) == 0:
        return []
    
    # Convert papers to a format suitable for GPT
    paper_summaries = []
    for idx, paper in enumerate(papers):
        paper_summaries.append(f"Paper ID: {idx} Title: {paper.title}\nAbstract: {paper.summary}\nComment: {paper.comment}\nLink: {paper.entry_id}")
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config.AGENT_PROMPT
            },
            {
                "role": "user",
                "content": config.PROMPT_CHINESE_AD + "\n\nPapers:\n" + "\n---\n".join(paper_summaries)
            }
        ],
        # model="gpt-4o-mini-2024-07-18",
        model=model_name,
        max_tokens=300,
    )
    
    try:
        # Parse the response to get indices and reasons
        response_lines = chat_completion.choices[0].message.content.strip().split('\n')
        print(f"[0222DEBUG] Check response lines: {response_lines}")

        # Create a list to store all papers
        all_papers = papers.copy()  # Keep a copy of all papers

        top_indices, reasons = parse_recommendations(response_lines)

        # Add recommendation reasons to top papers
        for idx, reason in zip(top_indices, reasons):
            if idx < len(all_papers):
                all_papers[idx].recommendation_reason = reason
                print(f"[DEBUG] Added reason to paper {idx}: {reason[:30]}...")

        # Return all papers (some will have recommendation_reason attribute)
        return all_papers

    except Exception as e:
        print(f"[ERROR] Failed to rank papers: {e}")
        return papers  # Return original papers if ranking fails

def init_db(type_name: str, db_path=None):
    """Initialize database for a specific type"""
    if db_path is None:
        db_path = f"./content/{type_name[3:]}_plus.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arxiv (
            id TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            comment TEXT,
            authors TEXT,
            institutions TEXT,
            categories TEXT,
            relevant BOOL DEFAULT 0,
            date_added DATE
        )
    """)
    conn.commit()
    return conn, cursor

def fetch_arxiv_entries(type_name):
    """Fetch recent entries from arxiv for a specific type"""
    print(f"[DEBUG] Fetching arxiv listings for {type_name}")
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = session.get(
            f"https://arxiv.org/list/{type_name}/recent?skip=0&show=2000",
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"[DEBUG] Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch arxiv listings. Status code: {response.status_code}")
            return []
            
        r = response.content.decode('utf-8')
        entries = re.findall(r'/abs/(\d+\.\d+)" title="Abstract"', r)
        print(f"[DEBUG] Found {len(entries)} papers in listing")
        
        # Get paper details using arxiv API
        if entries:
            paper_search = arxiv.Search(id_list=entries)
            return list(paper_search.results())
        return []
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch arxiv listings: {str(e)}")
        return []

def process_paper(paper):
    """Process a paper from arxiv API to extract relevant information"""
    try:
        # Skip papers with "federated" in the title
        if "federated" in paper.title.lower():
            print(f"[DEBUG] Skipping federated paper: {paper.title}")
            return None
            
        return paper
    except Exception as e:
        print(f"[ERROR] Failed to process paper: {str(e)}")
        return None

def store_paper(cursor, paper, relevant, date):
    """Store paper information in the database"""
    try:
        # Extract authors and their institutions
        authors = [author.name for author in paper.authors]
        authors_str = '|'.join(authors)
        
        # Extract institutions if available
        institutions = []
        if hasattr(paper, 'affiliations'):
            institutions = paper.affiliations
        elif hasattr(paper, 'authors') and hasattr(paper.authors[0], 'affiliation'):
            institutions = [getattr(author, 'affiliation', '') for author in paper.authors]
        institutions_str = '|'.join(institutions)
        
        # Extract categories
        categories = paper.categories if hasattr(paper, 'categories') else []
        categories_str = '|'.join(categories)
        
        # Insert paper into database
        cursor.execute("""
            INSERT OR IGNORE INTO arxiv 
            (id, title, abstract, comment, authors, institutions, categories, relevant, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.entry_id,
            paper.title,
            paper.summary,
            getattr(paper, 'comment', ''),
            authors_str,
            institutions_str,
            categories_str,
            1 if relevant else 0,
            date
        ))
        print(f"[DEBUG] Stored paper in DB: {paper.title}, {relevant}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to store paper: {str(e)}")
        return False

def check_existing_db(date):
    """Check if database exists for the given date and print summary if it does"""
    date_dir = f"./content/{date}"
    if not (os.path.exists(date_dir) and os.path.isdir(date_dir)):
        return False
        
    print(f"[INFO] Database directory for {date} already exists.")
    
    # Check for database files in the directory
    db_files = [f for f in os.listdir(date_dir) if f.endswith('.db')]
    if not db_files:
        return False
        
    print(f"[INFO] Found {len(db_files)} database files for {date}:")
    
    total_entries = 0
    total_selected = 0
    
    for db_file in db_files:
        db_path = os.path.join(date_dir, db_file)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM arxiv")
        count = cursor.fetchone()[0]
        total_entries += count
        
        # Check which column exists: 'reject' or 'relevant'
        cursor.execute("PRAGMA table_info(arxiv)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'relevant' in columns:
            # New column name
            cursor.execute("SELECT COUNT(*) FROM arxiv WHERE relevant = 1")
        else:
            # Old column name
            cursor.execute("SELECT COUNT(*) FROM arxiv WHERE reject = 1")
            
        selected = cursor.fetchone()[0]
        total_selected += selected
        
        print(f"[INFO] {db_file}: {count} entries, {selected} selected papers")
        
        # Get first 3 entries sorted by title - handle both column names
        if 'relevant' in columns:
            cursor.execute("SELECT id, title FROM arxiv WHERE relevant = 1 ORDER BY title LIMIT 3")
        else:
            cursor.execute("SELECT id, title FROM arxiv WHERE reject = 1 ORDER BY title LIMIT 3")
            
        samples = cursor.fetchall()
        
        if samples:
            print(f"[INFO] Sample papers from {db_file}:")
            for paper_id, title in samples:
                print(f"[INFO] - {title[:80]}... (ID: {paper_id})")
        
        conn.close()
    
    print(f"[INFO] Summary for {date}: {total_entries} total entries, {total_selected} selected papers")
    return True

def pull_papers(date=None):
    """Pull papers from arxiv and store in DB"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Check if database already exists for this date
    if check_existing_db(date):
        return
    
    # If no directory or database exists for this date, proceed with pulling papers
    print(f"[INFO] Pulling papers for date: {date}")
    
    # Create date directory if it doesn't exist
    date_dir = f"./content/{date}"
    if not os.path.exists(date_dir):
        os.makedirs(date_dir)
    
    for sub_type in config.ARXIV_LIST['types']:
        db_path = os.path.join(date_dir, f"{sub_type[3:]}.db")
        conn, cursor = init_db(sub_type, db_path)
        try:
            entries = fetch_arxiv_entries(sub_type)
            for entry in entries:
                paper = process_paper(entry)
                if paper:
                    # Store all papers, with relevant flag from check_gpt
                    relevant = check_gpt(paper.title, paper.summary, paper.comment)
                    store_paper(cursor, paper, relevant, date)
            conn.commit()
        finally:
            conn.close()

def send_daily_email(date=None):
    """Send email based on DB contents"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
    date_dir = f"./content/{date}"
    if not os.path.exists(date_dir):
        print(f"[ERROR] No database directory found for date: {date}")
        return
        
    all_papers = []
    db_files = [f for f in os.listdir(date_dir) if f.endswith('.db')]
    
    # Initialize statistics dictionary
    stats = {
        'total_retrieved': 0,
        'total_selected': 0,
        'by_type': {}
    }
    
    for db_file in db_files:
        db_path = os.path.join(date_dir, db_file)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the type name from the db file name
        type_name = "cs." + db_file.replace('.db', '')
        
        # Check which column exists: 'reject' or 'relevant'
        cursor.execute("PRAGMA table_info(arxiv)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM arxiv")
        total_count = cursor.fetchone()[0]
        stats['total_retrieved'] += total_count
        
        # Get selected papers count
        if 'relevant' in columns:
            cursor.execute("SELECT COUNT(*) FROM arxiv WHERE relevant = 1")
        else:
            cursor.execute("SELECT COUNT(*) FROM arxiv WHERE reject = 1")
        selected_count = cursor.fetchone()[0]
        stats['total_selected'] += selected_count
        
        # Add type statistics
        stats['by_type'][type_name] = {
            'retrieved': total_count,
            'selected': selected_count
        }
        
        # Get papers where relevant=1 (or reject=1 for older DBs)
        if 'relevant' in columns:
            cursor.execute("SELECT * FROM arxiv WHERE relevant = 1")
        else:
            cursor.execute("SELECT * FROM arxiv WHERE reject = 1")
            
        papers = cursor.fetchall()


        
        for paper_data in papers:
            paper = create_paper_object(paper_data)
            all_papers.append(paper)
            
        conn.close()
    
    if all_papers:
        print(f"[INFO] Found {len(all_papers)} papers to include in email")
        ranked_papers = rank_and_summarize_papers(all_papers)
        # Pass the stats parameter to send_email
        send_email(ranked_papers, stats=stats)
    else:
        print(f"[INFO] No papers found for date: {date}")

def create_paper_object(db_row):
    """Create a paper object from DB row"""
    # Create an object that mimics the arxiv paper object
    class Paper:
        pass
    
    paper = Paper()
    
    # Debug what fields are available in the paper_data
    print(f"[DEBUG] Fields in paper_data: {db_row}")
    
    # Handle different database schemas based on the number of columns
    if len(db_row) >= 9:  # New schema with 9 columns (including institutions)
        (paper.entry_id, paper.title, paper.summary, paper.comment, 
         authors_str, institutions_str, categories_str, _, _) = db_row
        
        # Create author objects similar to arxiv API
        class Author:
            def __init__(self, name):
                self.name = name
                
        paper.authors = [Author(name) for name in authors_str.split('|') if name] if authors_str else []
        paper.institutions = institutions_str.split('|') if institutions_str else []
        paper.categories = categories_str.split('|') if categories_str else []
    else:
        # Instead of trying to handle unknown schemas, provide a clear error message
        print(f"[ERROR] Database row has unexpected number of fields: {len(db_row)}")
        print(f"[ERROR] Expected 9 fields but got: {db_row}")
        print(f"[ERROR] Using minimal fallback to prevent crash")
        
        # Set minimal required fields to prevent crashes
        paper.entry_id = db_row[0] if len(db_row) > 0 else "unknown_id"
        paper.title = db_row[1] if len(db_row) > 1 else "Unknown Title"
        paper.summary = db_row[2] if len(db_row) > 2 else "No summary available"
        paper.comment = db_row[3] if len(db_row) > 3 else ""
        paper.authors = []
        paper.institutions = []
        paper.categories = []
    
    # Create author string for display
    paper.author_str = ', '.join([author.name for author in paper.authors]) if hasattr(paper, 'authors') and paper.authors else "Unknown"
    
    return paper

def arxiv_crawl():
    model_name = "deepseek-v3-241226"
    check_model_response(model_name)

    # Initialize statistics dictionary
    stats = {
        'total_retrieved': 0,  # Total papers found on arxiv
        'total_selected': 0,   # Total papers selected by check_gpt()
        'by_type': {}
    }
    
    
    print("[DEBUG] Starting arxiv_crawl()")
    papers = []
    for sub_type in config.ARXIV_LIST['types']:
        print(f"[DEBUG] Pulling papers for type: {sub_type}")
        papers.extend(pull_type(sub_type, model_name=model_name, stats=stats))
        stats['total_selected'] += len(papers)
        stats['by_type'][sub_type] = len(papers)

    print(f"[DEBUG] Total papers pulled: {stats['total_retrieved']}")
    
    paper_map = {}
    for paper in papers:
        paper.author_str = ", ".join([author.name for author in paper.authors])
        paper_map[paper.entry_id] = paper
    print(f"[DEBUG] Unique papers after deduplication: {len(paper_map)}")
    
    papers = list(paper_map.values())
    if len(papers) > 0:
        print("[DEBUG] Starting paper ranking and summarization")
        ranked_papers = rank_and_summarize_papers(papers, model_name=model_name)
        
        # Split papers into those with recommendations and those without
        top_papers = [p for p in ranked_papers if hasattr(p, 'recommendation_reason')]
        other_papers = [p for p in ranked_papers if not hasattr(p, 'recommendation_reason')]
        
        print(f"[DEBUG] Got {len(top_papers)} top papers with reasons")
        print(f"[DEBUG] Other papers count: {len(other_papers)}")
        
        # Combine top papers and other papers (top papers first)
        papers_to_send = top_papers + other_papers
        print(f"[DEBUG] Sending email with total {len(papers_to_send)} papers")
        
        # Pass both the combined list and the separated lists to send_email
        send_email(papers_to_send, stats=stats)
    else:
        print("[DEBUG] No papers found to process")
    