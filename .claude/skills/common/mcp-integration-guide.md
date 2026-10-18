# MCP Integration Guide & Tool Registry

Skills may reference external data only through tool IDs on this registry. **Never invent a
tool ID.** The toolkit CLI (`doddle.tool.cli.dsocial`) covers everything deterministic; MCP
tools cover live, account-specific data.

## Registry

| Tool ID | Provides | Typical skills | Required |
|---------|----------|----------------|----------|
| `doddle.tool.cli.dsocial` | Deterministic specs, post validation, hashtag stats, calendar, export audit | all `social-*` | yes (bundled) |
| `doddle.tool.v1.canva.design` | Design asset generation and brand kits | social-creative-brief, social-ugc | no |
| `doddle.tool.v1.buffer.profiles` | Connected profiles, queue, scheduled posts | social-content-calendar, social-reporting | no |
| `doddle.tool.v1.hubspot.contacts` | CRM segments and lifecycle stage | social-strategy, social-ugc | no |
| `doddle.tool.v1.ga4.getReport` | Analytics: sessions, conversions, social referral | social-analytics, social-reporting | no |
| `doddle.tool.v1.meta.ads` | Meta ad account: campaigns, spend, results | social-paid-strategy, social-meta-ads | no |
| `doddle.tool.v1.tiktok.ads` | TikTok ad account: campaigns, spend, results | social-paid-strategy, social-tiktok-ads | no |
| `doddle.tool.v1.linkedin.ads` | LinkedIn ad account: campaigns, spend, results | social-paid-strategy, social-linkedin-ads | no |
| `doddle.tool.v1.notion.pages` | Planning docs, briefs, content banks | social-content-calendar, social-creative-brief | no |

Platform-native analytics exports (Instagram/TikTok/LinkedIn insights) are ingested through
`dsocial audit` as a file — no MCP tool needed, and no scraping.

## Rules

1. **Deterministic first.** If `dsocial` can compute it, do not ask an MCP tool for it.
2. **Optional tools are optional.** Every MCP tool in a blueprint is `required: false` with
   `fallback: manual_review`. Their absence degrades the report, it does not fail the skill.
3. **Unavailable ⇒ say so.** Print `⚠️ NOT AVAILABLE — configure <tool>` and name the setup.
   Never estimate a substitute.
4. **Live numbers are `live` class.** Tag them. They are not part of the deterministic score.
5. **Never put API keys on a command line** or in the conversation. Read them from the
   environment or the harness's secret store.

## Fallback behaviour by tool

| Tool missing | What to do |
|--------------|------------|
| `canva.design` | Provide the creative brief and specs; do not generate assets |
| `buffer.profiles` | Produce the calendar as a plan; note scheduling was not actioned |
| `ga4.getReport` | Report site conversions as NOT AVAILABLE; still audit the export |
| `meta.ads` / `tiktok.ads` / `linkedin.ads` | Report ad performance as NOT AVAILABLE; plan from strategy and specs only |
| `hubspot.contacts` | Ask the user for the audience/segment; do not invent one |
| `notion.pages` | Keep planning output inline |
