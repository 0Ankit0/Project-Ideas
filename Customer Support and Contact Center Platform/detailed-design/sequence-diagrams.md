# Sequence Diagrams — Customer Support and Contact Center Platform

> **Document Purpose:** Defines runtime interaction flows between system participants using UML sequence diagrams rendered in Mermaid. Each diagram traces a key use case end-to-end, showing synchronous calls, asynchronous events, conditional branches, and error paths.

---

## SD-001 — Complete Ticket Lifecycle via Email

**Scenario:** A customer sends an email to the support address. The platform ingests it, deduplicates it, resolves the contact, creates a ticket, starts SLA clocks, routes to the best agent, notifies the agent, the agent replies, the customer is notified of the reply, the agent marks the ticket resolved, and a CSAT survey is dispatched.

**Participants:**
- `EmailConnector` — polls or receives webhooks from the email provider (Gmail / Outlook / IMAP)
- `IngestionService` — normalises raw email into platform `Message` objects
- `DeduplicationService` — prevents duplicate tickets from thread-reply chains
- `ContactService` — resolves or creates the `Contact` record
- `TicketService` — creates and manages `Ticket` lifecycle
- `SLAService` — starts first-response and resolution clocks
- `RoutingEngine` — selects the best queue/agent
- `AgentService` — updates agent load and availability
- `NotificationService` — pushes real-time and email alerts

```mermaid
sequenceDiagram
    autonumber
    participant EC as EmailConnector
    participant IS as IngestionService
    participant DS as DeduplicationService
    participant CS as ContactService
    participant TS as TicketService
    participant SLA as SLAService
    participant RE as RoutingEngine
    participant AS as AgentService
    participant NS as NotificationService

    EC->>IS: onEmailReceived(rawEmail)
    IS->>IS: parseHeaders(rawEmail)
    IS->>IS: extractBodyAndAttachments(rawEmail)
    IS->>DS: checkDuplicate(messageId, inReplyTo)
    alt Is duplicate / reply to existing thread
        DS-->>IS: existingTicketId
        IS->>TS: appendMessage(existingTicketId, message)
        TS-->>IS: messageId
        IS->>NS: notifyAgentNewReply(existingTicketId, agentId)
        NS-->>IS: dispatched
    else New conversation
        DS-->>IS: null (no duplicate found)
        IS->>CS: resolveOrCreateContact(fromEmail, fromName)
        CS-->>IS: contact
        IS->>TS: createTicket(CreateTicketCommand{contactId, subject, bodyHtml, channelId, priority})
        TS->>TS: validateCommand()
        TS->>TS: applyDefaultPriority()
        TS-->>IS: ticket
        IS->>SLA: startClocks(ticket)
        SLA->>SLA: selectPolicy(ticket)
        SLA->>SLA: calculateFirstResponseDeadline()
        SLA->>SLA: calculateResolutionDeadline()
        SLA-->>IS: slaClocks[firstResponse, resolution]
        IS->>RE: route(ticket)
        RE->>RE: evaluateRoutingRules(ticket)
        RE->>RE: extractRequiredSkills(ticket)
        RE->>RE: findEligibleAgents(queueId, skills)
        RE->>AS: getAvailableAgents(eligibleAgentIds)
        AS-->>RE: availableAgents
        RE->>RE: selectLeastLoaded(availableAgents)
        RE-->>IS: routingDecision{agentId, queueId}
        IS->>TS: assignTicket(ticketId, agentId)
        TS-->>IS: updated ticket
        IS->>AS: incrementLoad(agentId)
        AS-->>IS: ok
        IS->>NS: notifyAgentAssigned(agentId, ticketId)
        NS-->>IS: dispatched
    end

    Note over EC,NS: Agent views ticket and replies

    AS->>TS: addAgentMessage(ticketId, agentId, replyBody)
    TS->>TS: createMessage(direction=OUTBOUND)
    TS->>TS: transitionStatus(OPEN -> PENDING)
    TS-->>AS: message
    AS->>SLA: recordFirstResponse(ticketId)
    SLA->>SLA: stopFirstResponseClock()
    SLA-->>AS: ok
    AS->>EC: sendReply(toEmail, subject, body, inReplyTo)
    EC-->>AS: sent
    AS->>NS: notifyContactReply(contactId, ticketId)
    NS-->>AS: dispatched

    Note over EC,NS: Customer replies

    EC->>IS: onEmailReceived(customerReply)
    IS->>DS: checkDuplicate(messageId, inReplyTo)
    DS-->>IS: existingTicketId
    IS->>TS: appendMessage(existingTicketId, customerMessage)
    TS->>TS: transitionStatus(PENDING -> OPEN)
    TS-->>IS: message
    IS->>NS: notifyAgentCustomerReplied(agentId, ticketId)
    NS-->>IS: dispatched

    Note over EC,NS: Agent resolves ticket

    AS->>TS: resolveTicket(ticketId, wrapCodeId)
    TS->>TS: transitionStatus(OPEN -> RESOLVED)
    TS->>SLA: stopResolutionClock(ticketId)
    SLA-->>TS: ok
    TS-->>AS: updated ticket
    AS->>NS: dispatchCSAT(ticketId, contactId)
    NS->>NS: loadSurveyTemplate()
    NS->>NS: generateSurveyLink()
    NS->>CS: getContactEmail(contactId)
    CS-->>NS: email
    NS-->>AS: survey email queued
```

---

## SD-002 — Live Chat Session to Ticket

**Scenario:** A customer opens the chat widget. The bot greets them, identifies their intent via NLP, responds. The customer escalates to a human agent. The bot packages the session context, creates a ticket, the routing engine assigns an agent, and the agent joins the conversation.

**Participants:**
- `ChatWidget` — browser-embedded JS widget
- `ChatGateway` — WebSocket server handling real-time chat messages
- `SessionManager` — tracks live chat sessions state
- `BotEngine` — orchestrates bot conversation
- `NLPService` — intent classification via ML model
- `HandoffService` — coordinates bot-to-agent handoff
- `TicketService` — creates ticket from chat session
- `RoutingEngine` — assigns ticket to best agent
- `AgentService` — notifies and connects agent to chat

```mermaid
sequenceDiagram
    autonumber
    participant CW as ChatWidget
    participant CG as ChatGateway
    participant SM as SessionManager
    participant BE as BotEngine
    participant NLP as NLPService
    participant HS as HandoffService
    participant TS as TicketService
    participant RE as RoutingEngine
    participant AS as AgentService

    CW->>CG: connect(contactId, channelId, metadata)
    CG->>SM: createSession(contactId, channelId)
    SM-->>CG: session{sessionId, botId}
    CG->>BE: startSession(sessionId, botId, contactId)
    BE-->>CG: greeting message
    CG-->>CW: message{text: "Hi! How can I help?"}

    CW->>CG: sendMessage(sessionId, "I need help with my order")
    CG->>BE: processMessage(sessionId, text)
    BE->>NLP: classify(text, botId)
    NLP->>NLP: tokenize(text)
    NLP->>NLP: embedText(tokens)
    NLP->>NLP: runInference(embedding)
    NLP-->>BE: classification{intent: "order_inquiry", confidence: 0.87}
    BE->>BE: checkConfidenceThreshold(0.87 >= 0.75)
    BE->>BE: resolveIntent("order_inquiry")
    BE->>BE: generateResponse(intent, context)
    BE-->>CG: botResponse{text: "Sure, I can help with your order..."}
    CG-->>CW: message{text: "Sure, I can help with your order..."}

    CW->>CG: sendMessage(sessionId, "I want to talk to a human")
    CG->>BE: processMessage(sessionId, text)
    BE->>NLP: classify(text, botId)
    NLP-->>BE: classification{intent: "escalate_to_agent", confidence: 0.95}
    BE->>BE: flagHandoffRequired()
    BE-->>CG: botResponse{text: "I'll connect you to an agent now.", handoffRequired: true}
    CG-->>CW: message{text: "I'll connect you to an agent now."}

    CG->>HS: initiateHandoff(sessionId)
    HS->>SM: getSessionContext(sessionId)
    SM-->>HS: context{transcript, contactId, intentHistory, metadata}
    HS->>TS: createTicket(CreateTicketCommand{source: CHAT, contactId, subject, transcript, channelId})
    TS-->>HS: ticket{ticketId}
    HS->>RE: route(ticket)
    RE->>RE: selectAgent(queue, skills, availability)
    RE-->>HS: routingDecision{agentId}
    HS->>TS: assignTicket(ticketId, agentId)
    TS-->>HS: ok
    HS->>AS: notifyAgentChatAssigned(agentId, ticketId, sessionId)
    AS-->>HS: ok
    HS-->>CG: handoffComplete{agentId, estimatedWait: "2 min"}
    CG-->>CW: message{text: "Agent Alex will join you shortly (est. 2 min)"}

    AS->>CG: agentJoinSession(sessionId, agentId)
    CG->>SM: updateSessionOwner(sessionId, agentId)
    SM-->>CG: ok
    CG-->>CW: agentJoined{agentName: "Alex"}
    CG-->>AS: sessionContext{transcript, contactInfo}

    Note over CW,AS: Agent and customer converse via ChatGateway

    AS->>CG: resolveSession(sessionId)
    CG->>TS: resolveTicket(ticketId, wrapCodeId)
    TS-->>CG: ok
    CG-->>CW: sessionEnded{message: "Your issue has been resolved."}
```

---

## SD-003 — Skill-Based Routing

**Scenario:** A new ticket enters the queue. The routing engine evaluates routing rules, extracts required agent skills from the ticket metadata, finds eligible agents, checks real-time availability, selects the least-loaded agent, assigns the ticket, and notifies the agent.

```mermaid
sequenceDiagram
    autonumber
    participant TS as TicketService
    participant RE as RoutingEngine
    participant QS as QueueService
    participant SKM as AgentSkillMatcher
    participant AVS as AgentAvailabilityService
    participant ASS as AssignmentService
    participant NS as NotificationService

    TS->>RE: route(ticket)
    RE->>RE: loadRoutingRules(organizationId)
    RE->>RE: evaluateRules(ticket, rules)
    RE->>QS: resolveTargetQueue(ticket, matchedRuleId)
    QS-->>RE: queue{queueId, routingStrategy: SKILL_BASED}
    RE->>RE: extractRequiredSkills(ticket)
    Note right of RE: Skills derived from ticket category,<br/>tags, channel type, and custom fields
    RE->>SKM: findEligibleAgents(queueId, requiredSkills)
    SKM->>SKM: loadQueueAgents(queueId)
    SKM->>SKM: filterBySkillMatch(agents, requiredSkills)
    SKM->>SKM: scoreSkillAlignment(agents, requiredSkills)
    SKM-->>RE: eligibleAgents[{agentId, skillScore: 0.95}, {agentId, skillScore: 0.82}]

    alt No eligible agents found
        RE->>QS: enqueue(ticketId, priority)
        QS-->>RE: position
        RE-->>TS: routingDecision{outcome: QUEUED, position}
    else Eligible agents found
        RE->>AVS: getAvailableAgents(eligibleAgentIds)
        AVS->>AVS: checkStatus(agentIds)
        AVS->>AVS: checkConcurrentLoad(agentIds)
        AVS->>AVS: checkShiftSchedule(agentIds)
        AVS-->>RE: availableAgents[agentId1, agentId2]

        alt No available agents
            RE->>QS: enqueue(ticketId, priority)
            QS-->>RE: position
            RE-->>TS: routingDecision{outcome: QUEUED, position}
        else Available agents found
            RE->>RE: calculateLoadScore(availableAgents)
            RE->>RE: selectLeastLoaded(availableAgents)
            RE-->>ASS: assign(ticketId, selectedAgentId, queueId)
            ASS->>ASS: createAssignment(ticketId, agentId)
            ASS->>AVS: incrementLoad(agentId)
            ASS-->>RE: assignment{assignmentId}
            RE-->>TS: routingDecision{outcome: ASSIGNED, agentId}
            RE->>NS: notifyAgentAssigned(agentId, ticketId)
            NS->>NS: sendInAppNotification(agentId, payload)
            NS->>NS: sendEmailIfOffline(agentId, payload)
            NS-->>RE: dispatched
        end
    end
```

---

## SD-004 — SLA Breach Detection and Escalation

**Scenario:** A scheduled job fires every minute. The SLA service checks all active SLA clocks, identifies clocks approaching their deadline, emits warnings, detects breaches, publishes breach events, and the escalation engine evaluates rules and takes configured actions (reassign, notify supervisor, etc.).

```mermaid
sequenceDiagram
    autonumber
    participant SCHED as SLAScheduler
    participant SLA as SLAService
    participant TS as TicketService
    participant EE as EscalationEngine
    participant ERR as EscalationRuleRepository
    participant ASS as AssignmentService
    participant NS as NotificationService
    participant AUD as AuditService

    SCHED->>SLA: tick(currentTime)
    SLA->>SLA: loadActiveClocks()
    SLA->>SLA: evaluateClocks(currentTime)

    loop For each active SLA clock
        SLA->>SLA: calculateRemaining(clock, currentTime)
        alt Remaining < warningThreshold
            SLA->>SLA: emitWarningEvent(clock)
            SLA->>TS: getTicket(clock.ticketId)
            TS-->>SLA: ticket
            SLA->>NS: sendSLAWarning(ticket, clock, remainingMinutes)
            NS-->>SLA: dispatched
        end
        alt Remaining <= 0 AND clock.status != BREACHED
            SLA->>SLA: markBreached(clock, currentTime)
            SLA->>SLA: createSLABreach(clock)
            SLA->>EE: publishSLABreached(breach)
        end
    end

    EE->>ERR: getRulesForTrigger(SLA_BREACHED, organizationId)
    ERR-->>EE: escalationRules[]

    loop For each escalation rule
        EE->>TS: getTicket(breach.ticketId)
        TS-->>EE: ticket
        EE->>EE: evaluate(rule, ticket)
        alt Rule conditions match
            EE->>EE: executeActions(rule.actions, ticket)
            loop For each action
                alt Action: REASSIGN
                    EE->>ASS: reassignToQueue(ticketId, rule.targetQueueId)
                    ASS-->>EE: ok
                else Action: NOTIFY_SUPERVISOR
                    EE->>NS: notifySupervisor(supervisorId, ticketId, breach)
                    NS-->>EE: dispatched
                else Action: CHANGE_PRIORITY
                    EE->>TS: updatePriority(ticketId, URGENT)
                    TS-->>EE: ok
                else Action: ADD_TAG
                    EE->>TS: addTag(ticketId, "sla-breached")
                    TS-->>EE: ok
                end
            end
            EE->>AUD: logEscalationExecuted(ruleId, ticketId, actions)
            AUD-->>EE: auditId
            alt Rule has stopOnMatch = true
                EE->>EE: breakRuleLoop()
            end
        end
    end

    SLA-->>SCHED: tickComplete{processed: N, warnings: W, breaches: B}
```

---

## SD-005 — Bot NLP Intent Recognition and Handoff

**Scenario:** A message arrives in a bot session. The bot gateway looks up the session, the NLP classifier determines intent with confidence score. If confidence is below threshold, a fallback KB search is attempted. If the customer requests a human (or bot cannot resolve), a handoff is initiated — the context is packaged, a ticket is created, and the routing engine assigns an agent.

```mermaid
sequenceDiagram
    autonumber
    participant CW as ChatWidget
    participant BG as BotGateway
    participant BSM as BotSessionManager
    participant NLP as NLPClassifier
    participant KBS as KBSearch
    participant BRG as BotResponseGenerator
    participant HC as HandoffCoordinator
    participant TS as TicketService
    participant RE as RoutingEngine
    participant ANS as AgentNotificationService

    CW->>BG: message(sessionId, text: "How do I reset my password?")
    BG->>BSM: getSession(sessionId)
    BSM-->>BG: session{botId, contactId, contextVariables, turnHistory}
    BG->>NLP: classify(text, botId, context)
    NLP->>NLP: preprocess(text)
    NLP->>NLP: vectorize(text)
    NLP->>NLP: runModel(vector)
    NLP-->>BG: result{intent: "password_reset", confidence: 0.91, entities: {}}

    BG->>BG: checkConfidence(0.91 >= threshold 0.75)
    BG->>BRG: generateResponse(intent: "password_reset", context)
    BRG->>KBS: searchArticles("password reset", organizationId)
    KBS->>KBS: vectorSearch(query)
    KBS-->>BRG: articles[{id, title, snippet, score: 0.88}]
    BRG->>BRG: composeResponse(intent, articles)
    BRG-->>BG: response{text: "Here's how to reset...", articleSuggestions: [...]}
    BG->>BSM: updateSession(sessionId, intent, response)
    BSM-->>BG: ok
    BG-->>CW: message{text: "Here's how to reset...", suggestions: [link]}

    CW->>BG: message(sessionId, text: "I still can't figure it out, get me a human")
    BG->>BSM: getSession(sessionId)
    BSM-->>BG: session
    BG->>NLP: classify(text, botId, context)
    NLP-->>BG: result{intent: "request_human_agent", confidence: 0.98}
    BG->>BG: handoffRequired = true

    BG->>HC: initiateHandoff(sessionId)
    HC->>BSM: getFullSessionContext(sessionId)
    BSM-->>HC: context{transcript, contactId, intentHistory, resolvedEntities}
    HC->>HC: packageHandoffContext(context)
    HC->>TS: createTicket(CreateTicketCommand{
    Note right of HC: source=CHAT, contactId,<br/>subject="Password Reset Issue",<br/>transcript, channelId,<br/>handoffContext
    HC->>TS: })
    TS-->>HC: ticket{ticketId, ticketNumber}
    HC->>RE: route(ticket)
    RE->>RE: matchSkills(ticket.tags, agents)
    RE->>RE: selectAvailableAgent()
    RE-->>HC: routingDecision{agentId}
    HC->>TS: assignTicket(ticketId, agentId)
    TS-->>HC: ok
    HC->>ANS: notifyAgentHandoff(agentId, ticketId, sessionId, context)
    ANS-->>HC: dispatched
    HC->>BSM: markSessionHandedOff(sessionId, ticketId)
    BSM-->>HC: ok
    HC-->>BG: handoffResult{ticketId, agentName, estimatedWait}
    BG-->>CW: message{text: "Connecting you to Sarah (est. wait: 3 min)", ticketId}
```

---

## SD-006 — CSAT Survey Dispatch and Response Collection

**Scenario:** A ticket is resolved. The survey trigger service evaluates whether to send a survey (checking cooldown periods and opt-out preferences). A survey link is generated and dispatched via email. The customer submits the survey. The response is stored, the score is aggregated, and the analytics service updates agent and team CSAT metrics.

```mermaid
sequenceDiagram
    autonumber
    participant TS as TicketService
    participant STS as SurveyTriggerService
    participant STMPL as SurveyTemplateService
    participant NS as NotificationService
    participant CS as ContactService
    participant ES as EmailService
    participant SRH as SurveyResponseHandler
    participant ANL as AnalyticsService

    TS->>STS: onTicketResolved(ticketResolvedEvent)
    STS->>STS: checkSurveyPolicy(organizationId)
    STS->>CS: getContact(event.contactId)
    CS-->>STS: contact{email, language, optOutSurveys}

    alt Contact opted out of surveys
        STS-->>TS: surveySkipped(reason: OPT_OUT)
    else Not opted out
        STS->>STS: checkCooldown(contactId, lastSurveyAt)
        alt Within cooldown period (e.g. 30 days)
            STS-->>TS: surveySkipped(reason: COOLDOWN)
        else Outside cooldown
            STS->>STMPL: getTemplate(organizationId, language, channel: EMAIL)
            STMPL-->>STS: template{id, subject, bodyHtml, questions[]}
            STS->>STS: checkAlreadySent(ticketId)
            alt Survey already sent for this ticket
                STS-->>TS: surveySkipped(reason: ALREADY_SENT)
            else Not yet sent
                STS->>STS: generateSurveyToken(ticketId, contactId)
                STS->>STS: buildSurveyLink(token, templateId)
                STS->>NS: dispatchSurvey(contactId, templateId, surveyLink, channel: EMAIL)
                NS->>ES: sendEmail(to: contact.email, subject, bodyHtml{surveyLink})
                ES-->>NS: messageId
                NS-->>STS: dispatched{messageId}
                STS->>STS: recordSurveyDispatched(ticketId, contactId, templateId, messageId)
                STS-->>TS: surveyDispatched{surveyToken}
            end
        end
    end

    Note over TS,ANL: Customer clicks link and submits survey

    SRH->>SRH: onSurveySubmitted(token, responses{Q1:5, Q2:4, comment:"Great help!"})
    SRH->>SRH: validateToken(token)
    SRH->>SRH: resolveTicketAndContact(token)
    SRH->>SRH: calculateCSATScore(responses)
    Note right of SRH: CSAT = (positive responses / total) * 100<br/>NPS = promoters% - detractors%
    SRH->>SRH: storeSurveyResponse(SurveyResponse{ticketId, contactId, score, comment, submittedAt})
    SRH->>TS: getTicket(ticketId)
    TS-->>SRH: ticket{assignedAgentId, teamId}
    SRH->>ANL: recordCSATScore(agentId, teamId, organizationId, score, ticketId)
    ANL->>ANL: updateAgentCSATRolling(agentId, score)
    ANL->>ANL: updateTeamCSATRolling(teamId, score)
    ANL->>ANL: updateOrgCSATRolling(organizationId, score)
    ANL->>ANL: emitCSATMetricEvent(MetricEvent{type: CSAT, ...})
    ANL-->>SRH: ok
    SRH->>NS: notifyAgentCSATReceived(agentId, ticketId, score, comment)
    NS-->>SRH: dispatched
    SRH-->>SRH: markSurveyComplete(token)
```

---

*Last updated: 2025 | Version: 1.0 | Owner: Platform Engineering*
