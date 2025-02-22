# paperdog
daily arxiv paper news feed by email
## TODO
- [x] Get a new OPENAI API
  - Got a deepseek-v3-241226 API key from ARK
- [ ] Add author institutions as a list behind Authors List
  - [ ] Got this type of info
  [DEBUG] Available attributes: ['Author', 'Link', 'MissingFieldError', '__annotations__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_from_feed_entry', '_get_default_filename', '_get_pdf_url', '_raw', '_to_datetime', 'authors', 'categories', 'comment', 'doi', 'download_pdf', 'download_source', 'entry_id', 'get_short_id', 'journal_ref', 'links', 'pdf_url', 'primary_category', 'published', 'summary', 'title', 'updated']
  - Use OpenAlex API to get author affiliations, store a local table for author info as well
[DEBUG] Authors: [arxiv.Result.Author('Zixiang Cui'), arxiv.Result.Author('Xintong Ling'), arxiv.Result.Author('Xingyu Zhou'), arxiv.Result.Author('Jiaheng Wang'), arxiv.Result.Author('Zhi Ding'), arxiv.Result.Author('Xiqi Gao')]
- [ ] Implement personalized paper recommendations:
  - [ ] Collect subscriber academic profiles (webpage/Google Scholar)
  - [ ] Generate custom prompts based on subscriber research interests
- [x] Add Chinese language support for recommendation explanations
  - [ ] Needs further prompt engineering; tried Chinese prompt but not ideal, parsing response has problems
- [ ] Make the code compatible with other LLM APIs 
- [ ] Some logs/stats in email content to show retreieval numbers: like how many papers in total in arxiv link, how many papers are relevant, and how the top 3 papers are ranked.
- [ ] testing if computer is sleeping, crontab can execute

## Update on 20250222
- Adding crontab
```
   30 10 * * * source /opt/anaconda3/bin/activate hw4 && /opt/anaconda3/envs/hw4/bin/python /Users/baihuajun/Documents/paperdog/crawler.py
```
