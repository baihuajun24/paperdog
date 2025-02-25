import argparse
import datetime
import os
from arxiv_crawler import pull_papers, send_daily_email
from loguru import logger

def setup_directories():
    """Create necessary directories"""
    os.makedirs("./content", exist_ok=True)
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"./content/{date}", exist_ok=True)
    return date

def backup_db(date):
    """Backup database files"""
    from config import ARXIV_LIST
    for sub_type in ARXIV_LIST['types']:
        src = f"./content/{sub_type[3:]}_plus.db"
        dst = f"./content/{date}/{sub_type[3:]}_plus.db"
        if os.path.exists(src):
            os.system(f"cp {src} {dst}")

def main():
    parser = argparse.ArgumentParser(description='PaperDog: ArXiv Paper Crawler and Emailer')
    parser.add_argument('--pull', action='store_true', help='Only pull papers and build DB')
    parser.add_argument('--email', action='store_true', help='Only send email from existing DB')
    parser.add_argument('--date', type=str, default=datetime.datetime.now().strftime("%Y-%m-%d"), 
                        help='Specify date (YYYY-MM-DD) for DB operations (defaults to today)')
    
    args = parser.parse_args()
    date = args.date if args.date else datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Setup directories
    setup_directories()
    
    if args.pull:
        logger.info(f"Pulling papers for date: {date}")
        pull_papers(date)
        # backup_db(date)
    elif args.email:
        logger.info(f"Sending email for date: {date}")
        send_daily_email(date)
    else:
        # Default behavior: do both
        logger.info("Running complete workflow")
        pull_papers(date)
        # backup_db(date)
        send_daily_email(date)

if __name__ == '__main__':
    main() 