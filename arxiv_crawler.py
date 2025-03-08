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
def send_email(papers, stats=None, recipient_name=None, recipient_email=None):
    """Send email with paper information"""
    try:
        # Get email credentials from config
        smtp_server = getattr(config, 'SEND_EMAIL_SERVER', 'smtp.163.com')
        smtp_port = getattr(config, 'SEND_EMAIL_PORT', 25)
        username = getattr(config, 'SEND_EMAIL', '')
        password = getattr(config, 'SEND_EMAIL_PASSWORD', '')
        
        # Check if we have credentials
        if not username or not password:
            logger.error("Missing email credentials in config (SEND_EMAIL and SEND_EMAIL_PASSWORD)")
            return False
        
        # Use provided recipient or default
        if recipient_email is None:
            # Try to get from config.ARXIV_LIST['subscriber']
            try:
                recipient = config.ARXIV_LIST['subscriber'][0]['email']
            except (AttributeError, KeyError, IndexError):
                logger.error("No recipient email provided and no default found in config")
                return False
        else:
            recipient = recipient_email
        
        # Set up the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        # Create message with new subject format
        msg = MIMEMultipart('alternative')
        today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        msg['Subject'] = f"PaperDogV1[{today_date}]: New Papers from Arxiv Today"
        msg['From'] = username
        msg['To'] = recipient
        
        # Separate papers into top papers and other papers
        top_papers = []
        other_papers = []
        
        for paper in papers:
            # Check if the paper has a recommendation reason
            if hasattr(paper, 'recommendation_reason') and paper.recommendation_reason:
                top_papers.append(paper)
            else:
                other_papers.append(paper)
        
        # Load template
        env = Environment(loader=FileSystemLoader('./'))
        template = env.get_template('arxiv.template')
        
        # Render HTML content with recipient name if provided
        html_content = template.render(
            papers=papers,
            top_papers=top_papers,
            other_papers=other_papers,
            date=today_date,
            recipient_name=recipient_name if recipient_name else "ArXiv Reader",
            stats=stats
        )
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        server.sendmail(username, recipient, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent to {recipient} with {len(top_papers)} top papers and {len(other_papers)} other papers")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

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

def check_gpt(title:str, summary:str, comment:str, model_name="deepseek-v3-241226"):
    try:
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
        res = chat_completion.choices[0].message.content.lower()
        
        # Check if response contains yes or no
        if 'yes' in res:
            return True
        elif 'no' in res:
            return False
        else:
            # If response doesn't contain yes or no, make a best guess
            logger.warning(f"Model didn't return clear yes/no for paper: {title}")
            logger.warning(f"Model response: {res}")
            
            # Look for positive or negative sentiment
            positive_words = ['relevant', 'improve', 'system', 'throughput', 'latency', 'performance', 'efficient']
            negative_words = ['not relevant', 'accuracy', 'precision', 'not aimed', 'doesn\'t aim', 'does not aim']
            
            # Count positive and negative indicators
            positive_count = sum(1 for word in positive_words if word in res)
            negative_count = sum(1 for word in negative_words if word in res)
            
            # Make decision based on sentiment analysis
            if positive_count > negative_count:
                logger.info(f"Guessing YES based on sentiment analysis for: {title}")
                return True
            else:
                logger.info(f"Guessing NO based on sentiment analysis for: {title}")
                return False
    except Exception as e:
        logger.error(f"Error in check_gpt: {e}")
        logger.error(f"Failed paper: {title}")
        # In case of error, skip this paper
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
            idx, reason_start = line.split('|', 1)
            idx = int(idx.strip())
            top_indices.append(idx)
            
            # Start collecting the new reason
            current_reason.append(reason_start.strip())
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
        print(f"[DEBUG] Check response lines: {response_lines}")

        # Create a list to store all papers
        all_papers = papers.copy()  # Keep a copy of all papers

        top_indices, reasons = parse_recommendations(response_lines)
        
        # Debug output
        print(f"[DEBUG] Top indices: {top_indices}")
        print(f"[DEBUG] Reasons: {reasons}")

        # Add recommendation reasons to top papers
        for idx, reason in zip(top_indices, reasons):
            if idx < len(all_papers):
                all_papers[idx].recommendation_reason = reason
                print(f"[DEBUG] Added reason to paper {idx}: {reason[:30]}...")
                
                # Add author_str attribute for template rendering
                authors = [author.name for author in all_papers[idx].authors]
                all_papers[idx].author_str = ", ".join(authors)

        # Add author_str to all papers for template rendering
        for paper in all_papers:
            if not hasattr(paper, 'author_str'):
                authors = [author.name for author in paper.authors]
                paper.author_str = ", ".join(authors)

        # Return all papers (some will have recommendation_reason attribute)
        return all_papers

    except Exception as e:
        print(f"[ERROR] Failed to rank papers: {e}")
        # Add author_str to all papers for template rendering
        for paper in papers:
            authors = [author.name for author in paper.authors]
            paper.author_str = ", ".join(authors)
        return papers  # Return original papers if ranking fails

def init_master_db():
    """Initialize the master database with all necessary tables"""
    db_path = "./content/papers.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Get the current schema
        cursor.execute("PRAGMA table_info(papers)")
        columns = [col[1] for col in cursor.fetchall()]
        logger.debug(f"Current papers table columns: {columns}")
        
        # Check if we need to rename id to entry_id or vice versa
        if 'id' in columns and 'entry_id' not in columns:
            logger.warning("Found 'id' column but no 'entry_id' column. Using 'id' for compatibility.")
        elif 'entry_id' in columns and 'id' not in columns:
            logger.warning("Found 'entry_id' column but no 'id' column. Using 'entry_id' for compatibility.")
    else:
        # Create the main papers table with both id and entry_id for compatibility
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT,
                entry_id TEXT,
                title TEXT,
                abstract TEXT,
                comment TEXT,
                authors TEXT,
                institutions TEXT,
                id TEXT,
                entry_id TEXT,
                title TEXT,
                abstract TEXT,
                comment TEXT,
                authors TEXT,
                institutions TEXT,
                categories TEXT,
                type_name TEXT,
                published_date DATE,
                updated_date DATE,
                date_added DATE,
                relevant BOOL DEFAULT 0,
                PRIMARY KEY (id, type_name)
            )
        """)
        
        # Create indexes for efficient querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON papers(published_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_name ON papers(type_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relevant ON papers(relevant)")
        
        logger.info("Created papers table with updated schema")
    
    conn.commit()
    return conn, cursor

def paper_exists(cursor, paper_id, type_name):
    """Check if a paper already exists in the database"""
    # Check if the table has entry_id or id column
    cursor.execute("PRAGMA table_info(papers)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'entry_id' in columns:
        cursor.execute(
            "SELECT COUNT(*) FROM papers WHERE entry_id = ? AND type_name = ?", 
            (paper_id, type_name)
        )
    elif 'id' in columns:
        cursor.execute(
            "SELECT COUNT(*) FROM papers WHERE id = ? AND type_name = ?", 
            (paper_id, type_name)
        )
    else:
        logger.error("Neither 'id' nor 'entry_id' column found in papers table")
        return False
        
    return cursor.fetchone()[0] > 0

def store_paper(cursor, paper, type_name, relevant, date_added=None):
    """Store paper in database"""
    if date_added is None:
        date_added = datetime.datetime.now().strftime("%Y-%m-%d")
        
    # Convert authors to string
    authors_str = ", ".join([author.name for author in paper.authors])
    
    # Convert categories to string
    categories_str = ", ".join(paper.categories)
    
    # Check if the table has entry_id or id column
    cursor.execute("PRAGMA table_info(papers)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Determine which columns to use
    has_id = 'id' in columns
    has_entry_id = 'entry_id' in columns
    
    if has_id and has_entry_id:
        # If both columns exist, use both
        cursor.execute("""
            INSERT OR IGNORE INTO papers 
            (id, entry_id, title, abstract, comment, authors, categories, 
             type_name, published_date, updated_date, date_added, relevant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.entry_id,
            paper.entry_id,
            paper.title,
            paper.summary,
            paper.comment,
            authors_str,
            categories_str,
            type_name,
            paper.published.strftime("%Y-%m-%d"),
            paper.updated.strftime("%Y-%m-%d"),
            date_added,
            1 if relevant else 0
        ))
    elif has_entry_id:
        # If only entry_id exists
        cursor.execute("""
            INSERT OR IGNORE INTO papers 
            (entry_id, title, abstract, comment, authors, categories, 
             type_name, published_date, updated_date, date_added, relevant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.entry_id,
            paper.title,
            paper.summary,
            paper.comment,
            authors_str,
            categories_str,
            type_name,
            paper.published.strftime("%Y-%m-%d"),
            paper.updated.strftime("%Y-%m-%d"),
            date_added,
            1 if relevant else 0
        ))
    elif has_id:
        # If only id exists
        cursor.execute("""
            INSERT OR IGNORE INTO papers 
            (id, title, abstract, comment, authors, categories, 
             type_name, published_date, updated_date, date_added, relevant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.entry_id,
            paper.title,
            paper.summary,
            paper.comment,
            authors_str,
            categories_str,
            type_name,
            paper.published.strftime("%Y-%m-%d"),
            paper.updated.strftime("%Y-%m-%d"),
            date_added,
            1 if relevant else 0
        ))
    else:
        logger.error("Neither 'id' nor 'entry_id' column found in papers table")
        return
    
    logger.info(f"Stored paper: {paper.title} (Relevant: {relevant})")

def fetch_arxiv_entries(sub_type, start_date=None, end_date=None):
    """Fetch entries from arxiv for a specific type and date range"""
    try:
        # If no dates provided, use yesterday to today
        if start_date is None:
            # Get yesterday's date
            yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0)
        
        if end_date is None:
            # Get today's date
            end_date = datetime.datetime.now()
        
        # Format dates for arXiv API
        start_date_str = start_date.strftime('%Y%m%d%H%M%S')
        end_date_str = end_date.strftime('%Y%m%d%H%M%S')
        
        # Create date range query
        date_query = f"submittedDate:[{start_date_str} TO {end_date_str}]"
        
        # Combine with category query
        query = f"cat:{sub_type} AND {date_query}"
        
        logger.info(f"Fetching papers with query: {query}")
        
        # Use the arXiv API to search for papers
        search = arxiv.Search(
            query=query,
            max_results=1000,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        # Fetch the results
        results = list(search.results())
        logger.warning(f"Found {len(results)} papers for {sub_type} between {start_date_str} and {end_date_str}")
        
        return results
    except Exception as e:
        logger.error(f"Error fetching arxiv entries: {e}")
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

def pull_papers(date=None, start_date=None, end_date=None):
    """Pull papers from arxiv and store in master DB"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Initialize master database
    conn, cursor = init_master_db()
    
    try:
        # If no date range specified, use yesterday to today
        if start_date is None or end_date is None:
            today = datetime.datetime.now()
            yesterday = today - datetime.timedelta(days=1)
            
            # Set start time to yesterday at 00:00:00
            start_date = yesterday.replace(hour=0, minute=0, second=0)
            
            # Set end time to today at current time
            end_date = today
        
        logger.info(f"Fetching papers from {start_date} to {end_date}")
        logger.info(f"Papers will be stored with date_added: {date}")
        
        for sub_type in config.ARXIV_LIST['types']:
            logger.info(f"Processing {sub_type}")
            entries = fetch_arxiv_entries(sub_type, start_date, end_date)
            
            for entry in entries:
                try:
                    # Check if paper exists in database
                    if paper_exists(cursor, entry.entry_id, sub_type):
                        logger.info(f"Paper already exists: {entry.title}")
                        continue
                    
                    # Process paper
                    paper = process_paper(entry)
                    if paper:
                        # Check if paper is relevant
                        try:
                            relevant = check_gpt(paper.title, paper.summary, paper.comment)
                        except Exception as e:
                            logger.error(f"Error checking relevance: {e}")
                            # Skip to next paper on error
                            continue
                            
                        # Store paper
                        store_paper(cursor, paper, sub_type, relevant, date_added=date)
                except Exception as e:
                    logger.error(f"Error processing paper {entry.entry_id}: {e}")
                    # Continue with next paper
                    continue
            
            conn.commit()
    except Exception as e:
        logger.error(f"Error in pull_papers: {e}")
    finally:
        conn.close()

def send_daily_email(date=None):
    """Send email based on papers from a specific date"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Connect to master database
    db_path = "./content/papers.db"
    if not os.path.exists(db_path):
        logger.error(f"Master database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize statistics dictionary
    stats = {
        'total_retrieved': 0,
        'total_selected': 0,
        'by_type': {}
    }
    
    # Get statistics by type
    cursor.execute("""
        SELECT type_name, COUNT(*), SUM(CASE WHEN relevant = 1 THEN 1 ELSE 0 END)
        FROM papers 
        WHERE date_added = ?
        GROUP BY type_name
    """, (date,))
    
    type_stats = cursor.fetchall()
    for type_name, total, selected in type_stats:
        stats['total_retrieved'] += total
        stats['total_selected'] += selected
        stats['by_type'][type_name] = {
            'retrieved': total,
            'selected': selected
        }
    
    # Get all relevant papers for the date
    cursor.execute("""
        SELECT * FROM papers 
        WHERE date_added = ? AND relevant = 1
    """, (date,))
    
    papers_data = cursor.fetchall()
    conn.close()
    
    if not papers_data:
        logger.info(f"No relevant papers found for date: {date}")
        return
    
    # Create paper objects
    all_papers = []
    for paper_data in papers_data:
        paper = create_paper_object(paper_data)
        all_papers.append(paper)
    
    logger.info(f"Found {len(all_papers)} relevant papers for {date}")
    
    # Rank and send papers
    ranked_papers = rank_and_summarize_papers(all_papers)
    send_email(ranked_papers, stats=stats)

def create_paper_object(db_row):
    """Create a paper object from DB row"""
    # Create an object that mimics the arxiv paper object
    class Paper:
        pass
    
    paper = Paper()
    
    # The expected schema for the papers table
    expected_fields = [
        'id', 'title', 'abstract', 'comment', 'authors', 'institutions', 
        'categories', 'type_name', 'published_date', 'date_added', 'relevant'
    ]
    
    if len(db_row) != len(expected_fields):
        logger.error(f"Database row has unexpected number of fields: {len(db_row)}")
        logger.error(f"Expected {len(expected_fields)} fields but got: {db_row}")
        logger.error("Using minimal fallback to prevent crash")
        
        # Set minimal required fields to prevent crashes
        paper.entry_id = db_row[0] if len(db_row) > 0 else "unknown_id"
        paper.title = db_row[1] if len(db_row) > 1 else "Unknown Title"
        paper.summary = db_row[2] if len(db_row) > 2 else "No summary available"
        paper.comment = db_row[3] if len(db_row) > 3 else ""
        paper.authors = []
        paper.institutions = []
        paper.categories = []
        paper.type_name = db_row[7] if len(db_row) > 7 else "unknown"
        paper.published_date = None
    else:
        # Unpack all fields
        (paper.entry_id, paper.title, paper.summary, paper.comment,
         authors_str, institutions_str, categories_str, paper.type_name,
         paper.published_date, paper.date_added, _) = db_row
        
        # Create author objects
        class Author:
            def __init__(self, name):
                self.name = name
        
        paper.authors = [Author(name) for name in authors_str.split('|') if name] if authors_str else []
        paper.institutions = institutions_str.split('|') if institutions_str else []
        paper.categories = categories_str.split('|') if categories_str else []
    
    # Create author string for display
    paper.author_str = ', '.join([author.name for author in paper.authors]) if paper.authors else "Unknown"
    
    return paper

def migrate_old_databases():
    """Migrate data from old database structure to new master database"""
    # Initialize master database
    conn, cursor = init_master_db()
    
    try:
        # Find all date directories
        content_dir = "./content"
        date_dirs = [d for d in os.listdir(content_dir) 
                    if os.path.isdir(os.path.join(content_dir, d)) 
                    and re.match(r'\d{4}-\d{2}-\d{2}', d)]
        
        for date_dir in date_dirs:
            date = date_dir
            dir_path = os.path.join(content_dir, date_dir)
            
            # Find all database files in the directory
            db_files = [f for f in os.listdir(dir_path) if f.endswith('.db')]
            
            for db_file in db_files:
                # Determine type_name from filename
                type_name = "cs." + db_file.replace('.db', '')
                
                # Connect to old database
                old_db_path = os.path.join(dir_path, db_file)
                old_conn = sqlite3.connect(old_db_path)
                old_cursor = old_conn.cursor()
                
                # Check schema to determine column names
                old_cursor.execute("PRAGMA table_info(arxiv)")
                columns = [col[1] for col in old_cursor.fetchall()]
                
                # Determine relevant column name
                relevant_col = 'relevant' if 'relevant' in columns else 'reject'
                
                # Get all papers from old database
                old_cursor.execute(f"SELECT * FROM arxiv WHERE {relevant_col} = 1")
                old_papers = old_cursor.fetchall()
                
                # Insert papers into master database
                for old_paper in old_papers:
                    # Map old schema to new schema
                    # This will need to be adjusted based on your actual old schema
                    paper_id = old_paper[0]
                    title = old_paper[1]
                    abstract = old_paper[2]
                    comment = old_paper[3] if len(old_paper) > 3 else ""
                    authors = old_paper[4] if len(old_paper) > 4 else ""
                    institutions = old_paper[5] if len(old_paper) > 5 else ""
                    categories = old_paper[6] if len(old_paper) > 6 else ""
                    
                    # Insert into master database
                    cursor.execute("""
                        INSERT OR IGNORE INTO papers 
                        (id, title, abstract, comment, authors, institutions, categories, 
                         type_name, published_date, date_added, relevant)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        paper_id, title, abstract, comment, authors, institutions, categories,
                        type_name, None, date
                    ))
                
                old_conn.close()
            
        conn.commit()
        logger.info("Migration of old databases completed successfully")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
    finally:
        conn.close()
    
def publish_daily_email(date=None):
    """Send email to all subscribers based on DB contents"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Connect to master database
    db_path = "./content/papers.db"
    if not os.path.exists(db_path):
        logger.error(f"Master database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize statistics dictionary
    stats = {
        'total_retrieved': 0,
        'total_selected': 0,
        'by_type': {}
    }
    
    # Get statistics by type
    cursor.execute("""
        SELECT type_name, COUNT(*), SUM(CASE WHEN relevant = 1 THEN 1 ELSE 0 END)
        FROM papers 
        WHERE date_added = ?
        GROUP BY type_name
    """, (date,))
    
    type_stats = cursor.fetchall()
    for type_name, total, selected in type_stats:
        stats['total_retrieved'] += total
        stats['total_selected'] += selected
        stats['by_type'][type_name] = {
            'retrieved': total,
            'selected': selected
        }
    
    # Get all relevant papers for the date
    cursor.execute("""
        SELECT * FROM papers 
        WHERE date_added = ? AND relevant = 1
    """, (date,))
    
    papers_data = cursor.fetchall()
    conn.close()
    
    if not papers_data:
        logger.info(f"No relevant papers found for date: {date}")
        return
    
    # Create paper objects
    all_papers = []
    for paper_data in papers_data:
        paper = create_paper_object(paper_data)
        all_papers.append(paper)
    
    logger.info(f"Found {len(all_papers)} relevant papers for {date}")
    
    # Rank and summarize papers
    ranked_papers = rank_and_summarize_papers(all_papers)
    
    # Get subscribers from config
    subscribers = config.ARXIV_LIST.get('subscribers', [])
    if not subscribers:
        logger.warning("No subscribers found in config. Email will not be sent.")
        return
    
    # Send email to each subscriber
    for subscriber in subscribers:
        subscriber_name = subscriber.get('name', 'Subscriber')
        subscriber_email = subscriber.get('email')
        
        if not subscriber_email:
            logger.warning(f"No email address for subscriber {subscriber_name}. Skipping.")
            continue
        
        logger.info(f"Sending email to {subscriber_name} <{subscriber_email}>")
        try:
            send_email(ranked_papers, stats=stats, recipient_name=subscriber_name, recipient_email=subscriber_email)
            logger.info(f"Email sent successfully to {subscriber_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {subscriber_email}: {str(e)}")
    
    logger.info(f"Published email to {len(subscribers)} subscribers")
    