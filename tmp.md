sudo plutil -lint /Library/LaunchDaemons/com.example.paperdog.plist
sudo launchctl unload /Library/LaunchDaemons/com.example.paperdog.plist
sudo launchctl load /Library/LaunchDaemons/com.example.paperdog.plist
sudo launchctl list | grep com.example.paperdog

# Auto-run
# 创建 plist 文件
sudo tee /Library/LaunchDaemons/com.example.wakeup.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.wakeup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/your/script.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <dict>
        <key>PathState</key>
        <dict>
            <key>/var/run/your_trigger</key>
            <false/>
        </dict>
    </dict>
</dict>
</plist>
EOF

# 加载并启用
sudo launchctl load /Library/LaunchDaemons/com.example.wakeup.plist


# result entry
[DEBUG] Check result fields: {'entry_id': 'http://arxiv.org/abs/2502.14691v1', 'updated': datetime.datetime(2025, 2, 20, 16, 18, 15, tzinfo=datetime.timezone.utc), 'published': datetime.datetime(2025, 2, 20, 16, 18, 15, tzinfo=datetime.timezone.utc), 'title': 'Parallelizing a modern GPU simulator', 'authors': [arxiv.Result.Author('Rodrigo Huerta'), arxiv.Result.Author('Antonio González')], 'summary': 'Simulators are a primary tool in computer architecture research but are\nextremely computationally intensive. Simulating modern architectures with\nincreased core counts and recent workloads can be challenging, even on modern\nhardware. This paper demonstrates that simulating some GPGPU workloads in a\nsingle-threaded state-of-the-art simulator such as Accel-sim can take more than\nfive days. In this paper we present a simple approach to parallelize this\nsimulator with minimal code changes by using OpenMP. Moreover, our\nparallelization technique is deterministic, so the simulator provides the same\nresults for single-threaded and multi-threaded simulations. Compared to\nprevious works, we achieve a higher speed-up, and, more importantly, the\nparallel simulation does not incur any inaccuracies. When we run the simulator\nwith 16 threads, we achieve an average speed-up of 5.8x and reach 14x in some\nworkloads. This allows researchers to simulate applications that take five days\nin less than 12 hours. By speeding up simulations, researchers can model larger\nsystems, simulate bigger workloads, add more detail to the model, increase the\nefficiency of the hardware platform where the simulator is run, and obtain\nresults sooner.', 'comment': None, 'journal_ref': 'CAMS 2024', 'doi': None, 'primary_category': 'cs.DC', 'categories': ['cs.DC', 'cs.AR', 'cs.PF'], 'links': [arxiv.Result.Link('http://arxiv.org/abs/2502.14691v1', title=None, rel='alternate', content_type=None), arxiv.Result.Link('http://arxiv.org/pdf/2502.14691v1', title='pdf', rel='related', content_type=None)], 'pdf_url': 'http://arxiv.org/pdf/2502.14691v1', '_raw': {'id': 'http://arxiv.org/abs/2502.14691v1', 'guidislink': True, 'link': 'http://arxiv.org/abs/2502.14691v1', 'updated': '2025-02-20T16:18:15Z', 'updated_parsed': time.struct_time(tm_year=2025, tm_mon=2, tm_mday=20, tm_hour=16, tm_min=18, tm_sec=15, tm_wday=3, tm_yday=51, tm_isdst=0), 'published': '2025-02-20T16:18:15Z', 'published_parsed': time.struct_time(tm_year=2025, tm_mon=2, tm_mday=20, tm_hour=16, tm_min=18, tm_sec=15, tm_wday=3, tm_yday=51, tm_isdst=0), 'title': 'Parallelizing a modern GPU simulator', 'title_detail': {'type': 'text/plain', 'language': None, 'base': '', 'value': 'Parallelizing a modern GPU simulator'}, 'summary': 'Simulators are a primary tool in computer architecture research but are\nextremely computationally intensive. Simulating modern architectures with\nincreased core counts and recent workloads can be challenging, even on modern\nhardware. This paper demonstrates that simulating some GPGPU workloads in a\nsingle-threaded state-of-the-art simulator such as Accel-sim can take more than\nfive days. In this paper we present a simple approach to parallelize this\nsimulator with minimal code changes by using OpenMP. Moreover, our\nparallelization technique is deterministic, so the simulator provides the same\nresults for single-threaded and multi-threaded simulations. Compared to\nprevious works, we achieve a higher speed-up, and, more importantly, the\nparallel simulation does not incur any inaccuracies. When we run the simulator\nwith 16 threads, we achieve an average speed-up of 5.8x and reach 14x in some\nworkloads. This allows researchers to simulate applications that take five days\nin less than 12 hours. By speeding up simulations, researchers can model larger\nsystems, simulate bigger workloads, add more detail to the model, increase the\nefficiency of the hardware platform where the simulator is run, and obtain\nresults sooner.', 'summary_detail': {'type': 'text/plain', 'language': None, 'base': '', 'value': 'Simulators are a primary tool in computer architecture research but are\nextremely computationally intensive. Simulating modern architectures with\nincreased core counts and recent workloads can be challenging, even on modern\nhardware. This paper demonstrates that simulating some GPGPU workloads in a\nsingle-threaded state-of-the-art simulator such as Accel-sim can take more than\nfive days. In this paper we present a simple approach to parallelize this\nsimulator with minimal code changes by using OpenMP. Moreover, our\nparallelization technique is deterministic, so the simulator provides the same\nresults for single-threaded and multi-threaded simulations. Compared to\nprevious works, we achieve a higher speed-up, and, more importantly, the\nparallel simulation does not incur any inaccuracies. When we run the simulator\nwith 16 threads, we achieve an average speed-up of 5.8x and reach 14x in some\nworkloads. This allows researchers to simulate applications that take five days\nin less than 12 hours. By speeding up simulations, researchers can model larger\nsystems, simulate bigger workloads, add more detail to the model, increase the\nefficiency of the hardware platform where the simulator is run, and obtain\nresults sooner.'}, 'authors': [{'name': 'Rodrigo Huerta'}, {'name': 'Antonio González'}], 'author_detail': {'name': 'Antonio González'}, 'author': 'Antonio González', 'arxiv_journal_ref': 'CAMS 2024', 'links': [{'href': 'http://arxiv.org/abs/2502.14691v1', 'rel': 'alternate', 'type': 'text/html'}, {'title': 'pdf', 'href': 'http://arxiv.org/pdf/2502.14691v1', 'rel': 'related', 'type': 'application/pdf'}], 'arxiv_primary_category': {'term': 'cs.DC', 'scheme': 'http://arxiv.org/schemas/atom'}, 'tags': [{'term': 'cs.DC', 'scheme': 'http://arxiv.org/schemas/atom', 'label': None}, {'term': 'cs.AR', 'scheme': 'http://arxiv.org/schemas/atom', 'label': None}, {'term': 'cs.PF', 'scheme': 'http://arxiv.org/schemas/atom', 'label': None}]}}

# PaperDog-Code
    prompt = """Analyze these ML system papers and:
1. Select the top 3 most significant papers focusing on system performance, efficiency, and scalability
2. For each selected paper, provide a brief reason for recommendation (1-2 sentences)
Format your response exactly like this:
0|This paper is important because it introduces a novel approach to reduce inference latency.
2|This work stands out for its scalable distributed training solution.
5|Notable for its memory optimization technique that reduces GPU memory by 50%.
"""
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a professional ML systems researcher who can identify important papers about system optimization, efficiency improvements, and scalability enhancements."
            },
            {
                "role": "user",
                "content": f"{prompt}\n\nPapers:\n" + "\n---\n".join(paper_summaries)
            }
        ],
        model="gpt-4o-mini-2024-07-18",
        max_tokens=300,
    )
    
    try:
        # Parse the response to get indices and reasons
        response_lines = chat_completion.choices[0].message.content.strip().split('\n')
        
        # Create a list to store all papers
        all_papers = papers.copy()  # Keep a copy of all papers
        
        # Track which papers are in top 3
        top_indices = []
        reasons = []
        
        # Process top 3 selections
        for line in response_lines[:3]:
            idx, reason = line.split('|')
            idx = int(idx.strip())
            if idx < len(papers):
                top_indices.append(idx)
                reasons.append(reason.strip())
        
        # Add recommendation reasons to top papers
        for idx, reason in zip(top_indices, reasons):
            all_papers[idx].recommendation_reason = reason
        
        # Reorder papers to put top 3 first
        top_papers = [all_papers[i] for i in top_indices]
        other_papers = [p for i, p in enumerate(all_papers) if i not in top_indices]
        
        # Return reordered list with top papers first, followed by others
        return top_papers + other_papers
