import arxiv
import sqlite3
import config
from jinja2 import Environment, FileSystemLoader
import mail
import datetime
import os
#CREATE TABLE IF NOT EXISTS arxiv (id TEXT, title TEXT,abstract TEXT, PRIMARY KEY (id),UNIQUE (ID))
def send_email(papers):
    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template("arxiv.template")
    # construct parameters to use jinja2
    render_input = []
    email_html = template.render(papers=papers)
    emails=[item["email"] for item in config.ARXIV_LIST["subscriber"]]
    mail.send("PageDog: New arxiv AI paper today", email_html, config.ARXIV_LIST['from_email'], emails)

import openai
from openai import OpenAI

client = OpenAI(
    base_url='https://api.openai-proxy.org/v1',
    api_key='sk-0HKYasB4TFALRzleJcV1si3MDPAIer1bL6XCQM5orCI50CV2',
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
    model="gpt-3.5-turbo-0125",
    max_tokens=100,
    )
    res=chat_completion.choices[0].message.content.lower()
    assert 'no' in res or 'yes' in res
    if('yes' in res):
       return True
    else:
        return False

def pull_type(type_name:str):
    print(type_name)
    local_db = sqlite3.connect(f"./content/{type_name[3:]}.db")
    cursor = local_db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS arxiv (id TEXT, title TEXT,abstract TEXT, reject BOOL DEFAULT 0, PRIMARY KEY (id))")
    local_db.commit()
    r=arxiv.Search(query=f"cat:{type_name}",max_results=3000,sort_by=arxiv.SortCriterion.SubmittedDate)
    c=arxiv.Client(num_retries=10)
    res=[]
    try:
        for result in c.results(r,offset=0):
            if("federated" in result.title.lower()):
                continue
            if local_db.execute("SELECT * FROM arxiv WHERE id=?",(result.entry_id,)).fetchone():
                # print(f"{result.title}:{result.entry_id} exist in db.")
                continue
            try:
                reject = check_gpt(result.title,result.summary)
            except Exception as e:
                print(e)
                exit(0)
            if(reject):
                res.append(result)
            # update the reject column
            # local_db.execute("UPDATE arxiv SET reject=? WHERE id=?",(reject,result.entry_id))
            print(f"UPSERT ({result.entry_id},{result.title},{reject})")
            local_db.execute("INSERT OR IGNORE INTO arxiv VALUES (?,?,?,?)",(result.entry_id,result.title,result.summary,reject))
            local_db.commit()
    except Exception as e:
        print(e)
        local_db.commit()
    finally:
        local_db.commit()
        return res

def arxiv_crawl():
    papers=[]
    for sub_type in config.ARXIV_LIST['types']:
        # crawl_type(sub_type)
        papers.extend(pull_type(sub_type))
    paper_map={}
    for paper in papers:
        paper.author_str=", ".join([author.name for author in paper.authors])
        paper_map[paper.entry_id]=paper
    papers=paper_map.values()
    if len(papers) > 0:
        send_email(papers)
    
