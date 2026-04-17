## Review by Cici, A16915609
## Review of Xiao

### 1. Prepared flow
_What did you learn from the team's prepared trace? Did the prompt trace make the pipeline's behavior clear? Were the cost and stats numbers credible? Note anything surprising._

Xiao fetched posts from hackernews and reddit/internship. 
The filter pipeline includes: 1.) valid item structure and source types 2.)  keywords filter & discussion 3.) semantic simliarity check with gold dataset 4.) tritonllm filter.
The trace made the pipeline's behavior clear. The cost and stats numbers are credible. Everything seems reasonable to me. 

### 2. Ad-hoc input
_What input did your group suggest? What happened when they ran it? How did the results compare to the prepared flow — any differences in quality, cost, or behavior? Link to the relevant entry in the team's session log._

I suggested adding tracking and summary statistics, such as the pass rate (e.g., the percentage of posts that are actual job postings), as well as metadata indicating the source platform (e.g., Reddit or Hacker News) in the final output. This would support deeper data analysis and system performance evaluation.
Since this requires changes beyond prompt-level adjustments, it was not implemented during the review session. This modification should not affect model cost, but it would improve observability and could help identify more relevant opportunities for users.
link: https://github.com/ucsd-cse-genai-programming-sp26/01-social-media-monitor-xiao-assignment1-cse190/issues/1#issue-4229647611

### 3. Gold dataset spot-check
_Read 10 random labeled examples from the project's gold dataset. How many do you agree with? For any disagreements, explain why you'd label it differently._

I agreed with them all. 

### 4. Feature suggestion
_What user-facing modification did you propose during Phase 3? Why would it matter for the use case? What parts of the pipeline would need to change to support it?_

I proposed adding a lightweight internship classification layer to categorize extracted internship opportunities by field (e.g., data science, software engineering, etc.). This would allow users to more easily filter and identify opportunities relevant to their interests.
To support this feature, the prompt could be extended to include an additional output field for the internship type. The output schema would also need to be updated.

### 5. Overall
_One specific thing this project does well. One specific area for improvement._

One strength of the project is that the system is well-structured, allowing different configuration executions through command-line flags.
One area for improvement is improving result quality and organization by adding more structured and useful metadata tags to the outputs.

## Review by Cici, A16915609
## Review of Shivani

### 1. Prepared flow
_What did you learn from the team's prepared trace? Did the prompt trace make the pipeline's behavior clear? Were the cost and stats numbers credible? Note anything surprising._

Shivani built a real time system and filterted posts by keyword(must in, or drop), sentiment(positive and negative), profanity, and then llm. The trace made the pipeline's behavior clear. The cost and stats numbers are credible. Everything seems reasonable to me. 

### 2. Ad-hoc input
_What input did your group suggest? What happened when they ran it? How did the results compare to the prepared flow — any differences in quality, cost, or behavior? Link to the relevant entry in the team's session log._

I suggested adding a geographic filter to limit posts to a specific region, such as San Diego or California. This would help narrow the scope and make the system more relevant to specific use cases. However, it may also reduce the amount of available data in the real-time stream, since many posts are not location-tagged or tied to a specific region. As a result, the system takes longer to collect sufficient data before passing inputs to the LLM stage and producing an output.
link: https://github.com/ucsd-cse-genai-programming-sp26/01-social-media-monitor-shivani-sridhar-assignment-1/issues/1#issue-4233305758

### 3. Gold dataset spot-check
_Read 10 random labeled examples from the project's gold dataset. How many do you agree with? For any disagreements, explain why you'd label it differently._

I agreed with them all. 

### 4. Feature suggestion
_What user-facing modification did you propose during Phase 3? Why would it matter for the use case? What parts of the pipeline would need to change to support it?_

I proposed using the location detail to present these posts on a map. 
To support this feature, the pipeline would need to reliably extract and normalize location entities during the LLM extraction stage. Additionally, the system would need to geocode location names into coordinates and pass this structured data to a frontend visualization layer for rendering on a map interface.

### 5. Overall
_One specific thing this project does well. One specific area for improvement._
One thing that this project does well is that Shivani has many useful filters before llm which saves cost. 
One area of improvement is to think of more keywords to be included when filtering, in case it misses some food recommendation posts. 

