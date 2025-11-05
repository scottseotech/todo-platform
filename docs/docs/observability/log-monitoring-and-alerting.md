# Log Monitoring and Alerting

## Why It Matters

Modern observability stacks are powerful, but dashboards don’t always catch issues fast enough.
This scheduled job exists to **close that awareness gap** — automatically surfacing log anomalies in real time where the team already works: Slack.

The intent is simple: *errors should never wait for someone to open Grafana*.
By scanning logs on a regular cadence, the system provides a steady heartbeat of operational health, reinforcing reliability and proactive detection.

**Context-Rich Alerts** — messages summarize error patterns to reduce alert noise.  
**Low Overhead** — lightweight automation without needing a full log analysis pipeline.

### What It Does
Every 15 minutes, a Dagu `Job` scans the most recent logs for the keyword `error`.  
It aggregates and reports:

- Total count of matching log entries
- Signature of each unique error pattern

The job formats these results into a Slack message and posts them to an alert channel through a bot token.

### How It Fits the DevOps Stack
| Concern | Role of This Job |
|----------|-----------------|
| **Observability** | Continuously inspects logs for new or recurring error patterns. |
| **Incident Response** | Bridges detection and communication, reducing mean time to awareness (MTTA). |
| **Automation** | Fully automated via Dagu Job, no manual checks needed. |
| **ChatOps** | Publishes real-time error summaries directly into Slack. |
| **Reliability Engineering** | Adds redundancy to monitoring—serves as a fallback when dashboards are quiet. |

### Example Slack Alert
```bash
9 [default/todo-bot] --- stderr F from todoclientmcp import TodoMCPClient, MCPError

4 [default/todo-bot] --- stderr F openai.OpenAIError: The api_key client option must be set...
```