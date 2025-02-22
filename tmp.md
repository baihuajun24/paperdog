PaperDog-Code
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
