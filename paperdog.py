import argparse
import datetime
import os
from arxiv_crawler import pull_papers, send_daily_email, migrate_old_databases, init_master_db, publish_daily_email
from loguru import logger

def setup_directories():
    """Create necessary directories"""
    os.makedirs("./content", exist_ok=True)
    return datetime.datetime.now().strftime("%Y-%m-%d")

def main():
    parser = argparse.ArgumentParser(description='PaperDog: ArXiv Paper Crawler and Emailer')
    parser.add_argument('--pull', action='store_true', help='Only pull papers and build DB')
    parser.add_argument('--email', action='store_true', help='Only send email from existing DB')
    parser.add_argument('--publish', action='store_true', help='Send email to all subscribers in config')
    parser.add_argument('--date', type=str, default=datetime.datetime.now().strftime("%Y-%m-%d"), 
                        help='Specify date (YYYY-MM-DD) for DB operations (defaults to today)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD) for pulling papers')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD) for pulling papers')
    parser.add_argument('--migrate', action='store_true', help='Migrate old databases to new master database')
    
    args = parser.parse_args()
    date = args.date
    
    # Setup directories
    setup_directories()
    
    if args.migrate:
        logger.info("Migrating old databases to new master database")
        migrate_old_databases()
    elif args.pull:
        # Check if date range is specified
        if args.start_date and args.end_date:
            logger.info(f"Pulling papers from {args.start_date} to {args.end_date}")
            
            # Convert string dates to datetime objects
            start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")
            
            # Add one day to end_date to include the end date in the range
            end_date = end_date + datetime.timedelta(days=1)
            
            # Set time to midnight for start date and 23:59:59 for end date
            start_date = start_date.replace(hour=0, minute=0, second=0)
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            pull_papers(date, start_date=start_date, end_date=end_date)
        else:
            logger.info(f"Pulling papers for date: {date}")
            pull_papers(date)
    elif args.email:
        logger.info(f"Sending email for date: {date}")
        send_daily_email(date)
    elif args.publish:
        logger.info(f"Publishing email to all subscribers for date: {date}")
        publish_daily_email(date)
    else:
        # Default behavior: do both
        logger.info("Running complete workflow")
        pull_papers(date)
        send_daily_email(date)

if __name__ == '__main__':
    main() 