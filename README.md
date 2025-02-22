# paperdog
daily arxiv paper news feed by email
## TODO
- [x] Get a new OPENAI API
  - Got a deepseek-v3-241226 API key from ARK
- [ ] Add author institutions as a list behind Authors List
- [ ] Implement personalized paper recommendations:
  - [ ] Collect subscriber academic profiles (webpage/Google Scholar)
  - [ ] Generate custom prompts based on subscriber research interests
- [x] Add Chinese language support for recommendation explanations
- [ ] Make the code compatible with other LLM APIs 

## Update on 20250222
- Adding crontab
```
   30 10 * * * source /opt/anaconda3/bin/activate hw4 && /opt/anaconda3/envs/hw4/bin/python /Users/baihuajun/Documents/paperdog/crawler.py
```
