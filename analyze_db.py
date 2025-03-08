import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

def analyze_papers_db(start_date="2025-03-01"):
    """Analyze the papers database to understand relevance filtering"""
    
    # Connect to the database
    db_path = "./content/papers.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Check the database schema
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(papers)")
    columns = [col[1] for col in cursor.fetchall()]
    print("Database columns:", columns)
    
    # Determine which ID column to use
    id_column = 'entry_id' if 'entry_id' in columns else 'id'
    print(f"Using {id_column} as the ID column")
    
    # Get overall statistics by type and date since start_date
    query = f"""
    SELECT 
        type_name,
        date_added,
        COUNT(*) as total,
        SUM(CASE WHEN relevant = 1 THEN 1 ELSE 0 END) as relevant,
        ROUND(SUM(CASE WHEN relevant = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as relevant_percentage
    FROM papers
    WHERE date_added >= '{start_date}'
    GROUP BY type_name, date_added
    ORDER BY date_added, type_name
    """
    
    df = pd.read_sql_query(query, conn)
    print("\n=== Overall Statistics by Type and Date ===")
    print(df)
    
    # Create a pivot table for better visualization
    pivot_df = df.pivot_table(
        index='date_added', 
        columns='type_name', 
        values='total',
        fill_value=0
    )
    
    print("\n=== Total Papers by Date and Type ===")
    print(pivot_df)
    
    # Create a pivot table for relevant papers
    pivot_relevant = df.pivot_table(
        index='date_added', 
        columns='type_name', 
        values='relevant',
        fill_value=0
    )
    
    print("\n=== Relevant Papers by Date and Type ===")
    print(pivot_relevant)
    
    # Get the total and relevant counts for each date
    date_stats = df.groupby('date_added').agg({
        'total': 'sum',
        'relevant': 'sum'
    })
    date_stats['relevant_percentage'] = (date_stats['relevant'] / date_stats['total'] * 100).round(2)
    
    print("\n=== Daily Statistics ===")
    print(date_stats)
    
    # Get statistics for each type across all dates
    type_stats = df.groupby('type_name').agg({
        'total': 'sum',
        'relevant': 'sum'
    })
    type_stats['relevant_percentage'] = (type_stats['relevant'] / type_stats['total'] * 100).round(2)
    type_stats = type_stats.sort_values('total', ascending=False)
    
    print("\n=== Type Statistics ===")
    print(type_stats)
    
    # Check the most common categories for relevant papers
    # First, determine if we have a categories column
    if 'categories' in columns:
        query_categories = f"""
        SELECT 
            categories,
            COUNT(*) as count
        FROM papers
        WHERE relevant = 1 AND date_added >= '{start_date}'
        GROUP BY categories
        ORDER BY count DESC
        LIMIT 20
        """
        
        df_categories = pd.read_sql_query(query_categories, conn)
        print("\n=== Top Categories for Relevant Papers ===")
        print(df_categories)
    
    # Check if there are any patterns in titles of relevant vs non-relevant papers
    # Get sample of relevant papers
    query_relevant = f"""
    SELECT {id_column}, title, abstract, type_name, date_added
    FROM papers
    WHERE relevant = 1 AND date_added >= '{start_date}'
    ORDER BY date_added DESC
    LIMIT 10
    """
    
    df_relevant = pd.read_sql_query(query_relevant, conn)
    print("\n=== Sample of Relevant Papers ===")
    for _, row in df_relevant.iterrows():
        print(f"ID: {row[id_column]}")
        print(f"Type: {row['type_name']}")
        print(f"Date: {row['date_added']}")
        print(f"Title: {row['title']}")
        print("---")
    
    # Get sample of non-relevant papers
    query_nonrelevant = f"""
    SELECT {id_column}, title, abstract, type_name, date_added
    FROM papers
    WHERE relevant = 0 AND date_added >= '{start_date}'
    ORDER BY date_added DESC
    LIMIT 10
    """
    
    df_nonrelevant = pd.read_sql_query(query_nonrelevant, conn)
    print("\n=== Sample of Non-Relevant Papers ===")
    for _, row in df_nonrelevant.iterrows():
        print(f"ID: {row[id_column]}")
        print(f"Type: {row['type_name']}")
        print(f"Date: {row['date_added']}")
        print(f"Title: {row['title']}")
        print("---")
    
    # Close the connection
    conn.close()
    
    # Plot the data if matplotlib is available
    try:
        # Plot the total papers by date and type
        plt.figure(figsize=(12, 8))
        pivot_df.plot(kind='bar', stacked=True, ax=plt.gca())
        plt.title('Total Papers by Date and Type')
        plt.xlabel('Date')
        plt.ylabel('Number of Papers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('total_papers_by_date_type.png')
        
        # Plot the relevant papers by date and type
        plt.figure(figsize=(12, 8))
        pivot_relevant.plot(kind='bar', stacked=True, ax=plt.gca())
        plt.title('Relevant Papers by Date and Type')
        plt.xlabel('Date')
        plt.ylabel('Number of Papers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('relevant_papers_by_date_type.png')
        
        # Plot the relevance percentage by date
        plt.figure(figsize=(12, 6))
        date_stats['relevant_percentage'].plot(kind='bar', ax=plt.gca())
        plt.title('Relevance Percentage by Date')
        plt.xlabel('Date')
        plt.ylabel('Relevance Percentage')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('relevance_by_date.png')
        
        # Plot the relevance percentage by type
        plt.figure(figsize=(12, 6))
        type_stats['relevant_percentage'].plot(kind='bar', ax=plt.gca())
        plt.title('Relevance Percentage by Type')
        plt.xlabel('Type')
        plt.ylabel('Relevance Percentage')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('relevance_by_type.png')
        
        print("\nAnalysis complete. Check the generated plots for visual representation.")
    except Exception as e:
        print(f"Error generating plots: {e}")
        print("Analysis complete without plots.")

if __name__ == "__main__":
    import sys
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2025-03-01"
    analyze_papers_db(start_date)