# AI Assistant — Edge Cases

## Introduction

The AI assistant subsystem integrates OpenAI GPT-4o for conversational question-answering, LangChain.js for retrieval-augmented generation (RAG) orchestration, OpenAI `text-embedding-3-small` for article embeddings, pgvector for similarity search, and BullMQ for asynchronous embedding pipeline management. The AI assistant is the platform's highest-value differentiator but also its most operationally complex and ethically sensitive component.

Unlike traditional software failures, AI assistant failures are often silent, gradual, and hard to detect: an incorrect answer, a privacy leak in a prompt, or a hallucinated fact may go unnoticed for days or weeks. The eight edge cases below address the complete spectrum of AI failure modes: infrastructure availability, factual accuracy, data privacy, capacity constraints, cost management, knowledge freshness, conversational reliability, and content safety.

---

## EC-AI-001: OpenAI API Outage

### Failure Mode
The OpenAI API (api.openai.com) becomes unavailable due to an OpenAI infrastructure incident. All calls to `client.chat.completions.create()` and `client.embeddings.create()` in the NestJS `AiAssistantService` and `EmbeddingService` time out or return HTTP 503. The AI Q&A chat feature becomes completely non-functional. If the embedding pipeline is also blocked, newly published articles are not indexed into pgvector, causing semantic search degradation in addition to the Q&A outage.

### Impact
**Severity: High**
- The AI assistant feature is unavailable for the duration of the outage (historically 30 minutes to 4 hours for major OpenAI incidents).
- Users seeking answers to complex questions are left without support.
- The embedding pipeline falls behind, causing semantic search results to become stale for all articles published during the outage.
- If not handled gracefully, the UI displays blank responses, loading spinners, or opaque error messages.

### Detection
- **OpenAI API Health Probe**: A synthetic monitoring job pings `GET https://api.openai.com/v1/models` every 60 seconds. Alert if it fails 3 consecutive times.
- **Chat Completion Error Rate**: CloudWatch metric `ai.chat_completion_errors` > 10% of requests over 5 minutes triggers a High alert.
- **Embedding Pipeline Stall**: BullMQ `embed_article` queue depth growing without jobs being processed for 5 minutes.
- **OpenAI Status Page Webhook**: Subscribe to `https://status.openai.com` status change webhooks to receive notifications directly.

### Mitigation/Recovery
1. Activate the AI assistant degradation mode: disable the Q&A chat interface and display a clear message — "AI assistant is temporarily unavailable. Please use search to find articles directly."
2. Pause the BullMQ embedding pipeline workers (do not fail the jobs — leave them in the queue so they process when the API recovers).
3. Serve cached AI responses for the top-100 most-asked questions (stored in Redis with 24-hour TTL) if available.
4. When the OpenAI API recovers, un-pause the embedding workers and monitor queue drain.
5. Post a status update to the platform status page.

### Prevention
- Implement a fallback to an alternative LLM provider (e.g., Anthropic Claude via API, or a self-hosted model on AWS Bedrock) for the Q&A feature. The fallback model does not need to match GPT-4o quality — a degraded but functional answer is better than no answer.
- Cache the last 1,000 successful AI responses in Redis with a 6-hour TTL. Serve cached responses during outages when a semantically similar query matches a cached one (cosine similarity > 0.95).
- Use exponential backoff and circuit breaker (via the `opossum` library) for all OpenAI API calls. Open the circuit after 5 consecutive failures and half-open it after 60 seconds.

---

## EC-AI-002: LLM Hallucination

### Failure Mode
The RAG pipeline retrieves the top-5 most relevant articles for a user's question using pgvector similarity search. GPT-4o receives the retrieved article chunks as context and generates an answer. Despite the retrieved context being accurate, GPT-4o synthesizes an answer that goes beyond the source material, fabricating specific details (version numbers, step sequences, configuration values) that are not present in any retrieved article. The answer is delivered with high confidence and no indication that it contains non-source-based content. The user follows the fabricated instructions and encounters production errors.

### Impact
**Severity: High**
- Users take incorrect technical actions based on fabricated guidance.
- For knowledge bases used in customer support, a hallucinated answer can cause data loss, misconfiguration, or security vulnerabilities on the customer's side.
- Detecting hallucinations after the fact requires manual review of conversation logs, which is operationally expensive.
- Trust in the AI assistant is severely damaged once users experience or hear about hallucinations.

### Detection
- **Faithfulness Score**: After each AI response, compute a faithfulness score using a secondary LLM call (or a lightweight NLI model) that checks whether every claim in the response is entailed by the retrieved source articles. Log responses with faithfulness score < 0.80.
- **Citation Absence Check**: If the AI response references specific facts (version numbers, dates, URLs) that are not present in any retrieved article chunk, flag the response as `POTENTIALLY_HALLUCINATED`.
- **User Feedback**: Track "thumbs down" ratings and written feedback for AI responses. Cluster negative feedback by topic area to identify systematic hallucination patterns.
- **Manual Spot-Check**: Conduct a weekly manual review of 50 randomly sampled AI responses against their source articles.

### Mitigation/Recovery
1. If a hallucinated response is detected post-delivery, flag it in the conversation history as `INACCURATE` and display a correction banner to the user if they revisit the conversation.
2. Temporarily reduce GPT-4o `temperature` to 0.0 for the affected query type to decrease creativity and increase adherence to source material.
3. Add an explicit instruction to the system prompt: "You must only state facts that are directly supported by the provided source articles. If the source articles do not contain information to answer the question, say 'I don't have enough information in the knowledge base to answer this accurately.'"
4. Update the retrieval pipeline to return more context (increase from top-5 to top-10 articles) for the affected query categories.

### Prevention
- Enforce strict prompt engineering: include a grounding instruction that forbids the model from making claims outside the retrieved context.
- Implement retrieval-augmented verification (RAV): after generating the answer, use a second LLM pass to identify claims in the answer and verify each against the source passages.
- Display the source articles used for every AI answer, enabling users to self-verify the response.
- Maintain a hallucination test suite: known questions with correct answers. Run this suite on every LLM prompt change in the CI pipeline.

---

## EC-AI-003: PII Leakage in Prompt

### Failure Mode
A user asking the AI assistant a question inadvertently includes personally identifiable information in their message — for example: "Why can't John Doe (john.doe@company.com, employee ID 12345) access the SSO settings page?" The NestJS `AiAssistantService` passes this question, along with the user's session context, directly to the OpenAI API as the user prompt. The PII (name, email, employee ID) is transmitted to OpenAI's servers and potentially logged, used for model improvement (if data retention is enabled), or exposed in a future OpenAI API response.

### Impact
**Severity: Critical**
- GDPR Article 44 prohibits transfer of EU personal data to third countries without appropriate safeguards. Sending PII to OpenAI without documented safeguards may violate this.
- CCPA requires disclosure of data sold or shared with third parties.
- Enterprise customers with strict data processing agreements may have contractual prohibitions on sending employee data to third-party AI services.
- Regulatory fines and customer trust damage.

### Detection
- **PII Pre-Screening Regex**: Before every OpenAI API call, scan the user prompt for patterns matching emails (`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`), SSNs (`\b\d{3}-\d{2}-\d{4}\b`), phone numbers, and names matching the user's workspace directory. Log any detection as `PII_DETECTED_IN_PROMPT`.
- **Presidio Integration**: Use Microsoft Presidio (open-source PII detection) as the production PII scanner. Track `pii.detected_and_redacted_count` metric.
- **Audit Log**: Every AI API call must log: user ID, workspace ID, prompt hash, timestamp. Do NOT log the full prompt — log only the hash and the PII detection result.

### Mitigation/Recovery
1. Redact all detected PII from the prompt before sending to OpenAI: replace with placeholders (`[EMAIL]`, `[NAME]`, `[ID]`). Inform the user: "Personal information was removed from your question before processing for privacy."
2. If PII was already sent to OpenAI (detection failed), immediately submit a data deletion request to OpenAI using their API data retention controls.
3. Document the incident in the privacy incident log and notify the Data Protection Officer.
4. If the workspace has a strict no-PII policy enabled, reject the query entirely and display an explanatory message rather than sending redacted content.

### Prevention
- Deploy Presidio or an equivalent PII detection service as a pre-flight middleware for all AI prompts. This middleware is non-optional and cannot be bypassed.
- Enable OpenAI's "no training" data retention option (Zero Data Retention policy) via the API organization settings.
- Add a user-facing notice in the AI chat UI: "Do not include personal information in your question."
- Audit all system prompts to ensure they do not inadvertently include PII from the article context being passed to the model.
- Include PII leakage testing in the security test suite.

---

## EC-AI-004: Context Window Overflow

### Failure Mode
The LangChain.js RAG pipeline retrieves the top-10 article chunks for a user's complex question. Each chunk is up to 2,000 tokens. Together with the system prompt (500 tokens), conversation history (2,000 tokens), and instructions (500 tokens), the total context exceeds GPT-4o's 128,000 token limit. LangChain.js does not automatically handle overflow — it either throws a `context_length_exceeded` error (causing a 500 response to the user) or silently truncates the end of the context, removing the most recently retrieved articles. If the critical answer is in one of the truncated chunks, the AI generates an incomplete or incorrect response.

### Impact
**Severity: Medium**
- Users receive an error message or an incomplete answer for complex, multi-article questions.
- Silent truncation is worse than an error: the user receives a confidently wrong answer.
- Articles published later in the workspace (higher IDs, thus appearing later in context) are disproportionately truncated.

### Detection
- **Token Count Logging**: Log the total token count of every prompt sent to OpenAI. Alert if any prompt exceeds 100,000 tokens (providing a 28k buffer).
- **OpenAI API Error**: `context_length_exceeded` error code captured in Sentry. Alert immediately.
- **Truncation Detection**: After building the context, log whether any chunks were dropped due to the token limit.

### Mitigation/Recovery
1. Implement a token budget manager in the `AiAssistantService`: before building the final prompt, count tokens using the `tiktoken` library and apply a descending priority truncation strategy:
   - Priority 1: System prompt + instructions (never truncate)
   - Priority 2: Top-3 most relevant chunks (truncate last)
   - Priority 3: Conversation history (summarize if too long)
   - Priority 4: Chunks 4–10 (truncate first)
2. If the token budget is exceeded even after truncation, respond to the user: "Your question requires more context than I can process at once. Try asking about one specific topic."
3. For ongoing overflow on a specific query type, reduce chunk size from 2,000 to 1,000 tokens.

### Prevention
- Implement the token budget manager as a standard middleware in the RAG pipeline, not as a recovery measure.
- Use `tiktoken` to count tokens for every RAG request before dispatching to OpenAI.
- Set a maximum conversation history length of 10 exchanges; after 10, summarize earlier exchanges using a cheaper model (GPT-4o-mini) and replace them with the summary.
- Test the full RAG pipeline against articles of maximum size (10MB) to verify graceful handling.

---

## EC-AI-005: Embedding Cost Spike

### Failure Mode
A workspace administrator uses the bulk article import feature to import 50,000 legacy knowledge base articles from a CSV export. Each article is enqueued as an `EmbedArticleJob` in BullMQ. If the BullMQ worker concurrency is not rate-limited, all 50,000 jobs run concurrently against the OpenAI embeddings API. At approximately 1,000 tokens per article, this generates 50 million tokens of embedding calls, costing approximately $500 on the `text-embedding-3-small` pricing. This happens within minutes, far exceeding the monthly budget. The unexpected cost spike may trigger OpenAI rate limits (tier-based), causing all embedding jobs to fail simultaneously.

### Impact
**Severity: High**
- Unexpected $500+ API cost from a single import operation.
- OpenAI rate limit errors cause embedding failures for all active workspaces, not just the importing workspace.
- BullMQ queue fills with failed jobs; semantic search for all newly published articles is unavailable until the backlog is cleared.
- If the platform shares a single OpenAI API key across workspaces, one workspace's bulk import degrades service for all others.

### Detection
- **OpenAI Cost Alert**: Monitor spending via the OpenAI Usage API. Alert when daily spending exceeds 2x the daily average or crosses $100.
- **BullMQ Concurrency Monitor**: Alert when `embed_article` queue active jobs exceed 50 simultaneously.
- **Rate Limit Error Rate**: `openai.rate_limit_errors` metric spike triggers immediate alert.
- **Import Operation Audit**: Log bulk import sizes. Alert when an import job contains more than 1,000 articles.

### Mitigation/Recovery
1. Immediately pause all `EmbedArticleJob` workers: `await queue.pause()`.
2. Identify the bulk import that triggered the spike and place its remaining jobs at the back of the queue with a low priority.
3. Reduce BullMQ worker concurrency to 5 jobs and add a rate limiter: `{ max: 60, duration: 60000 }` (60 embeddings per minute, matching OpenAI's tier-1 limit).
4. Notify the workspace admin: "Your bulk import will complete over the next [estimated time]. Embedding processing has been rate-limited to protect platform stability."
5. Resume the queue with the new rate-limited settings.

### Prevention
- Implement per-workspace and per-operation embedding quotas. Bulk imports of >500 articles must request admin approval.
- Add a rate limiter to the `EmbedArticleJob` queue using BullMQ's built-in rate limiting: `{ max: 100, duration: 60000 }`.
- Set a hard monthly OpenAI spending cap via the OpenAI API's usage limits feature. At 90% of budget, auto-pause non-critical embedding jobs.
- Implement batch embeddings: send articles in batches of 20 to the `embeddings` endpoint rather than one at a time, reducing API call overhead.
- Use per-workspace OpenAI API subkeys (via OpenAI's project feature) to isolate rate limits.

---

## EC-AI-006: Stale Knowledge in RAG

### Failure Mode
An article is updated with significant corrections — for example, a security advisory article is updated to reflect a new CVE severity score. The article is saved in PostgreSQL and re-indexed in OpenSearch (text search is updated). However, the `UpdateEmbeddingJob` BullMQ job fails silently (OpenAI API timeout that is not retried) and the pgvector embedding for the article is not regenerated. For the next 12 hours (until the next full reconciliation), semantic search and AI Q&A retrieve the old embedding, matching on the original article context. The AI assistant answers questions about the CVE using the old (incorrect) severity information from the stale embedding.

### Impact
**Severity: High**
- AI answers are based on outdated information despite the article having been corrected.
- Users relying on the AI assistant for security-critical information receive stale guidance.
- The discrepancy between full-text search results (which are current) and AI answers (which are stale) is confusing and erodes trust.
- For regulated industries, serving outdated security or compliance information via AI constitutes a risk.

### Detection
- **Embedding Freshness Check**: Store `embeddings.last_embedded_at` and compare it against `articles.updated_at`. Any article where `updated_at > last_embedded_at + 5 minutes` is flagged as `EMBEDDING_STALE`.
- **Reconciliation Job**: A nightly job queries for all stale embeddings and alerts if the count exceeds 50.
- **UpdateEmbeddingJob Failure Tracking**: Log all failed embedding update jobs with the article ID. Alert on failure rate > 5%.

### Mitigation/Recovery
1. Run a targeted re-embedding for all articles flagged as `EMBEDDING_STALE`: `npm run jobs:reembed -- --staleSince=60m`.
2. Temporarily fall back to OpenSearch full-text search for AI context retrieval for stale-flagged articles, bypassing pgvector until re-embedding completes.
3. Display a disclaimer in the AI assistant for responses that cite a stale-flagged article: "This answer references an article that was recently updated. Verify with the latest version."
4. Investigate the `UpdateEmbeddingJob` failure cause (typically OpenAI timeout or BullMQ worker crash) and fix the root cause.

### Prevention
- Implement idempotent `UpdateEmbeddingJob` with 3 retries and exponential backoff. Never silently swallow failures — send failed jobs to the DLQ.
- Add a transactional outbox pattern: when `articles.updated_at` is updated, insert a record into `embedding_update_queue` table. A poller picks these up and re-creates BullMQ jobs, ensuring no update is missed.
- Run the stale embedding reconciliation job every hour (not nightly) and auto-remediate by re-queuing stale embeddings.
- Display the article's `updated_at` date alongside every AI response so users can cross-check recency.

---

## EC-AI-007: Infinite Conversation Loop

### Failure Mode
A user asks the AI assistant an ambiguous question. The AI responds with a clarifying question. The user provides an answer that is equally ambiguous or contradicts their original question. The AI asks another clarifying question. This loop continues indefinitely, with neither the user nor the AI making progress. Alternatively, a poorly constructed system prompt causes the AI to repeat a specific phrase or redirect pattern regardless of user input. Each exchange in the loop triggers an OpenAI API call, accumulating costs and approaching the workspace's token rate limit.

### Impact
**Severity: Medium**
- User frustration as the conversation never produces a useful answer.
- OpenAI API costs accumulate from repetitive API calls.
- If the workspace's rate limit is hit, other users' AI requests are rejected.
- In automated integration scenarios (API-based AI chat), infinite loops can cause service runaway.

### Detection
- **Conversation Depth Counter**: Track the number of exchanges in a conversation session. Alert if a single conversation exceeds 20 exchanges without a "resolved" or user-exit signal.
- **Response Similarity**: Compare the last 3 AI responses using cosine similarity. If similarity > 0.90, detect a repetition loop and alert.
- **Token Accumulation Rate**: Alert if a single conversation session accumulates more than 10,000 tokens in a 10-minute window.
- **User Abandonment Signal**: If a user sends the same message 3 times in a row, flag as `LOOP_DETECTED`.

### Mitigation/Recovery
1. After 15 consecutive exchanges in a single conversation without a user marking the question as resolved, surface a banner: "This conversation seems to be going in circles. Would you like to start fresh or search directly?"
2. If loop detection triggers (high response similarity), inject a fallback response: "I'm having difficulty answering your question with the available information. Here are the most relevant articles I found: [list]. Would you like to rephrase your question?"
3. Cap conversation sessions at 25 exchanges. After the cap, require the user to start a new conversation.
4. For API-based consumers, return a `CONVERSATION_LIMIT_REACHED` error code after 25 exchanges so integrations can handle the condition programmatically.

### Prevention
- Design the AI system prompt to include an explicit exit instruction: "If you have asked two clarifying questions and still cannot answer, provide the most relevant articles and tell the user you cannot answer with the available information."
- Set a conversation session token budget at the start of each session (e.g., 8,000 tokens). When the budget is 80% consumed, the system prompt is updated to instruct the model to attempt a final answer rather than continuing to clarify.
- Implement a response deduplication check: if the generated response has > 0.85 cosine similarity to the previous response, regenerate with a higher temperature or add an explicit instruction: "Provide a different type of response."

---

## EC-AI-008: Bias or Harmful Content in Response

### Failure Mode
A user in a customer-facing public knowledge base asks the AI assistant a question that, combined with the retrieved context, causes GPT-4o to generate a response containing biased, discriminatory, harmful, or policy-violating content. This can happen when: (1) the knowledge base contains articles with inadvertently biased language that is amplified by the model, (2) a user crafts a prompt that leads the model toward harmful outputs (jailbreak attempt), or (3) the model exhibits baseline bias in its responses to certain demographic-related questions.

### Impact
**Severity: Critical**
- Customer-facing harmful content creates legal liability, reputational damage, and potential regulatory action.
- Users from marginalized groups who encounter discriminatory responses experience harm.
- The incident becomes a public relations crisis if reported.
- Enterprise customers may terminate contracts.

### Detection
- **Content Moderation API**: Run every AI response through the OpenAI Moderation API (`POST /v1/moderations`) before delivering it to the user. Flag responses scoring above 0.7 on any harm category.
- **Sentry Alert**: `HarmfulContentDetected` event with the moderation scores and the conversation ID.
- **User Reports**: In-chat "Report this response" button. Alert on-call engineer for every user report.
- **Keyword Filter**: Maintain a blocklist of policy-violating phrases and scan responses before delivery.

### Mitigation/Recovery
1. If the moderation API flags a response, do not deliver it. Instead, respond: "I wasn't able to generate a helpful answer to your question. Please rephrase or contact support."
2. Log the flagged response (including the conversation context) in a secure, access-controlled `ai_flagged_responses` table for review by the Trust & Safety team.
3. If a harmful response was delivered before detection, reach out to the affected user, apologize, correct the record, and document the incident.
4. Temporarily disable AI responses for the query type or topic area where the harmful response occurred until the root cause is addressed.

### Prevention
- Add a robust system-level safety instruction to every AI prompt: "You are a helpful knowledge base assistant. You must not produce discriminatory, harmful, or policy-violating content under any circumstances, even if the user's question appears to request it."
- Run all responses through the OpenAI Moderation API in production. This is non-optional.
- Test the AI assistant against a library of known jailbreak patterns and adversarial prompts quarterly. Ensure all attempts are blocked.
- Implement a human review queue for flagged responses. Review and use them to improve the system prompt and safety instructions.
- Add Rate limiting for users who repeatedly trigger content moderation flags: 3 flags in 24 hours results in a 24-hour suspension of AI access.

---

## Summary Table

| ID       | Edge Case                        | Severity | Primary Owner         | Status   |
|----------|----------------------------------|----------|-----------------------|----------|
| EC-AI-001 | OpenAI API Outage               | High     | Backend / SRE         | Open     |
| EC-AI-002 | LLM Hallucination               | High     | AI / Product          | Open     |
| EC-AI-003 | PII Leakage in Prompt           | Critical | Security / Backend    | Open     |
| EC-AI-004 | Context Window Overflow         | Medium   | Backend / AI          | Open     |
| EC-AI-005 | Embedding Cost Spike            | High     | Backend / Finance     | Open     |
| EC-AI-006 | Stale Knowledge in RAG          | High     | Backend / AI          | Open     |
| EC-AI-007 | Infinite Conversation Loop      | Medium   | Backend / AI          | Open     |
| EC-AI-008 | Bias or Harmful Content         | Critical | AI / Trust & Safety   | Open     |

---

## Operational Policy Addendum

### 1. AI Response Quality Policy

Every AI response delivered to users must be traceable to a specific set of retrieved source articles. Anonymous or unsourced AI answers are prohibited. Source attribution must be displayed alongside every AI response. The AI assistant must include a disclaimer on all responses: "AI-generated answers may contain errors. Verify with the linked articles." Responses in regulated content categories (legal, medical, financial, security) must include an additional disclaimer advising professional consultation.

### 2. OpenAI Data Processing Policy

The platform must maintain a signed Data Processing Agreement (DPA) with OpenAI. All OpenAI API calls must use the Zero Data Retention (ZDR) configuration if the workspace contains any EU-person data, as defined under GDPR. No personally identifiable information from the user's conversation may be sent to the OpenAI API. All prompts must be screened by the PII detection middleware before dispatch. The DPA status must be reviewed annually.

### 3. AI Cost Governance Policy

Monthly OpenAI spending must not exceed the approved budget without Engineering Lead approval. A budget alert must be configured at 70% and 90% of monthly budget. When spending reaches 90% of budget, non-critical embedding jobs (bulk re-indexing, draft article embedding) must be automatically paused. The on-call engineer is authorized to suspend all AI features if daily spending exceeds 3x the daily average without further approval. Monthly cost reports must be reviewed by the product and engineering leads.

### 4. AI Safety and Content Policy

The OpenAI Moderation API must be called on 100% of AI responses in the production environment. Responses flagged by the Moderation API must never be delivered to users. A Trust & Safety reviewer must examine all flagged responses within 5 business days. The AI assistant's system prompt must be treated as a security artifact: changes require review by both Engineering and Trust & Safety. Jailbreak testing must be conducted quarterly using an up-to-date adversarial prompt library.
