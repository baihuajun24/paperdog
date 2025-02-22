import requests
from urllib.parse import quote
import time

def get_author_affiliations(author_name):
    """
    Get author's affiliations using OpenAlex API with improved search and error handling.
    
    Args:
        author_name (str): The name of the author to search for
        
    Returns:
        list: List of institution names or ["Unknown"] if not found
    """
    # Construct the URL with query parameters directly
    url = f"https://api.openalex.org/authors?search={author_name}"
        
    try:
        response = requests.get(url)
        # print(f"Check response.text: {response.text}")
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            affiliations_list = []
            # Process the first three results
            for author_info in data['results'][:1]:
                affiliations = author_info.get('affiliations', [])
                print(f"Check affiliations: {affiliations}")
                for affiliation in affiliations:
                    institution_name = affiliation['institution']['display_name']
                    affiliations_list.append(institution_name)
            
            return affiliations_list if affiliations_list else ['Unknown']
        else:
            return ['Unknown']
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] OpenAlex API request error: {e}")
        return ['Unknown']
    except Exception as e:
        print(f"[DEBUG] Unexpected error while getting affiliations: {str(e)}")
        return ["Unknown"]
    finally:
        # Rate limiting
        time.sleep(0.1)

# Example usage
if __name__ == "__main__":
    # Test cases
    test_authors = [
        "Qing Wang",
        "Geoffrey Hinton",
        "Yann LeCun"
    ]
    
    for author in test_authors:
        affiliations = get_author_affiliations(author)
        print(f"\nAuthor: {author}")
        print(f"Top 1 Affiliation: {affiliations[0]}")