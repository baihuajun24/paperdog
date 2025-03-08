# paperdog
daily arxiv paper news feed by email


## Recent Update on 2025-03-08
- I noticed categories have | in them, how would these affect relevance and summarizaiton?
```
rimary_category     paper_count  relevant_count  relevance_percentage
-------------------  -----------  --------------  --------------------
cs.CL                914          58              6.35                
cs.CL|cs.AI          748          58              7.75                
cs.LG|cs.AI          541          53              9.8                 
cs.LG                525          43              8.19                
cs.DC                508          166             32.68               
cs.CL|cs.AI|cs.LG    355          70              19.72               
cs.LG|cs.AI|cs.CL    250          39              15.6                
cs.CL|cs.LG          172          23              13.37               
cs.CV|cs.AI          126          8               6.35                
cs.AI                126          3               2.38                
cs.LG|cs.CL          113          19              16.81               
cs.CV|cs.LG          84           4               4.76                
cs.LG|stat.ML        83           2               2.41                
cs.AI|cs.LG          82           5               6.1                 
cs.AI|cs.CL          81           5               6.17                
cs.LG|cs.DC          80           45              56.25               
stat.ML|cs.LG        72           0               0.0                 
                     65           65              100.0               
cs.CV|cs.AI|cs.LG    59           9               15.25               
cs.DC|cs.LG          57           40              70.18               
cs.DC|cs.AI          55           38              69.09               
cs.LG|cs.AI|cs.CV    52           7               13.46               
cs.CR|cs.DC          50           3               6.0                 
cs.LG|cs.AI|stat.ML  48           0               0.0                 
cs.CV|cs.AI|cs.CL    43           3               6.98                
cs.CR|cs.AI          39           0               0.0                 
cs.LG|cs.CV          36           3               8.33                
cs.AI|cs.CL|cs.LG    35           3               8.57                
cs.DC|cs.AI|cs.LG    34           28              82.35               
cs.RO|cs.AI|cs.LG    31           2               6.45    
```

## Recent Updates (2025-02-25)
- [x] Completely refactored database structure:
  - Moved from date-based directory structure to a single consolidated database
  - Added `published_date` field to track when papers were published on arXiv
  - Added `type_name` field to properly categorize papers by arXiv category
  - Implemented duplicate checking to avoid processing the same paper multiple times
  - Added migration functionality to import data from old database structure
- [x] Improved email content:
  - Updated statistics wording to be more accurate and informative
  - Better handling of author information in email template
- [x] Added institutions field to store author affiliations
- [x] Enhanced logging with different colors for existing vs. new papers
- [x] Added default date parameter to simplify command-line usage

## TODO
- [x] Get a new OPENAI API
  - Got a deepseek-v3-241226 API key from ARK
- [x] Add author institutions as a list behind Authors List
  - [x] Added institutions field to database schema
  - [x] Implemented extraction of institution data when available
- [ ] Improve author affiliation data:
  - [ ] Use OpenAlex API to get author affiliations
  - [ ] Store a local table for author info as well
- [ ] Implement personalized paper recommendations:
  - [ ] Collect subscriber academic profiles (webpage/Google Scholar)
  - [ ] Generate custom prompts based on subscriber research interests
- [x] Add Chinese language support for recommendation explanations
  - [ ] Needs further prompt engineering; tried Chinese prompt but not ideal, parsing response has problems
- [ ] Make the code compatible with other LLM APIs 
- [x] Add logs/stats in email content to show retrieval numbers
  - [x] Now shows total papers published, relevant papers, and categories covered
- [ ] Testing if computer is sleeping, crontab can execute
- [ ] Add command to show database statistics (paper counts by date, relevance, etc.)

## Update on 20250225
- Refactored database structure for better performance and organization
- Fixed issues with author information display
- Improved email content with better statistics and paper selection

## Update on 20250222
- Adding crontab
```
<!-- 15 14 * * * cd /Users/baihuajun/Documents/paperdog && source /opt/anaconda3/bin/activate hw4 && /opt/anaconda3/envs/hw4/bin/python crawler.py >> log/$(date +\%Y-\%m-\%d).log 2>&1 -->

30 9 * * * cd /Users/baihuajun/Documents/paperdog && source /opt/anaconda3/bin/activate hw4 && /opt/anaconda3/envs/hw4/bin/python paperdog.py >> log/$(date +\%Y-\%m-\%d).log 2>&1
```

## Appendix

### arXiv API Object Structure
```
[DEBUG] Available attributes: ['Author', 'Link', 'MissingFieldError', '__annotations__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_from_feed_entry', '_get_default_filename', '_get_pdf_url', '_raw', '_to_datetime', 'authors', 'categories', 'comment', 'doi', 'download_pdf', 'download_source', 'entry_id', 'get_short_id', 'journal_ref', 'links', 'pdf_url', 'primary_category', 'published', 'summary', 'title', 'updated']

[DEBUG] Authors: [arxiv.Result.Author('Zixiang Cui'), arxiv.Result.Author('Xintong Ling'), arxiv.Result.Author('Xingyu Zhou'), arxiv.Result.Author('Jiaheng Wang'), arxiv.Result.Author('Zhi Ding'), arxiv.Result.Author('Xiqi Gao')]