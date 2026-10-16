# Personal Data Reclamation App: Market, Ideology, Legal Rights, and Purge/Opt-Out (as of Oct 2026)

Not legal advice. Sources are mostly secondary tech press plus a few regulator pages. Items marked **[background, not re-verified this session]** come from widely known statutory text or long-standing public facts, with canonical URLs, and were not fetched during this research pass. Writers should spot-check them.

---

## 1. Adjacent products and what happened to them

### Takeaway
"Record everything / second brain" hardware and software startups mostly ended in Big Tech acqui-hires or shutdowns: Rewind/Limitless went to Meta, Bee to Amazon, Humane's assets to HP. Each time, users lost or had to re-consent to their data, which is a strong argument for a user-owned copy. Consumer privacy apps (Jumbo, Mine/SayMine) also got absorbed by security incumbents. Data-broker removal (DeleteMe, Incogni, Optery) is the established paid category, but California's free DROP platform now commoditizes part of it. Vana takes the opposite approach: pool your data and sell or license it for AI training.

### Cited Findings
**Lifelogging / AI memory devices and software**
- **Rewind → Limitless → Meta.** Meta acquired Limitless (formerly Rewind, maker of a $99 conversation-recording pendant) in early December 2025. Terms were not disclosed. The team was folded into Reality Labs wearables under Meta's "personal superintelligence" framing. Pendant sales ended. Existing customers are supported for at least a year, with subscriptions waived (free unlimited plan). Continuing users must accept an updated privacy policy and ToS. The Rewind desktop software is being wound down — [TechCrunch](https://www.techcrunch.com/2025/12/05/meta-acquires-ai-device-startup-limitless/); [Neowin](https://www.neowin.net/news/meta-acquires-ai-startup-limitless-ending-sales-of-its-popular-pendant-wearable); [eMarketer](https://www.emarketer.com/content/meta-acquires-ai-wearables-startup-limitless-fuel-device-ambitions)
- Users in markets including the UK and South Korea reported on LinkedIn that their devices stopped working — [Social Samosa](https://www.socialsamosa.com/news-2/meta-acquires-limitless-10910875) (anecdotal)
- Rewind Mac app screen and audio capture were disabled on December 19, 2025, after the December 5, 2025 acquisition — [Screenpipe blog (competitor, self-interested)](https://screenpi.pe/blog/rewind-ai-alternative-2026)
- **Bee → Amazon.** Amazon agreed to acquire Bee (a $50 Pioneer wristband that records and transcribes conversations, plus a $19/month subscription) on July 22, 2025. The team joins Amazon Devices under Panos Panay. Amazon promised "strong data control features" such as a mic mute but did not confirm that Bee's existing protections (e.g., not storing audio) would remain — [Entrepreneur](https://www.entrepreneur.com/business-news/amazon-acquires-bee-startup-behind-eavesdropping-wearable/494971); [Bloomberg Law](https://news.bloomberglaw.com/private-equity/amazon-buys-bee-maker-of-50-wearable-ai-personal-assistant). A 2026 secondary site refers to an "Amazon Bee" $11.99 subscription — [tech-insider.org](https://tech-insider.org/amazon-bee-ai-wearables-11-99-subscription-upsell-2026) (unverified)
- **Humane AI Pin → HP.** HP bought Humane's assets (software platform, 300+ patents, most staff) for a reported $116M. Humane had raised about $230–241M. The AI Pin was bricked on February 28, 2025 (calling, messaging, AI queries and cloud access all cut), and refunds were limited to the 90-day window — [Axios](https://www.axios.com/2025/02/18/humane-ai-pin-shut-down-hp); [Fortune](https://www.fortune.com/2025/02/19/hp-humane-deal-ai-pin-shutting-down); [TechStartups](https://techstartups.com/2025/02/19/humane-ai-pin-startup-shuts-down-sells-to-hp-for-116m-after-burning-through-230m-in-investor-cash/)
- **Plaud** is the commercial success story. It is bootstrapped (founder savings plus a $1M crowdfund), had sold more than 1M devices and was profitable by September 2025 — [Forbes](https://www.forbes.com/sites/iainmartin/2025/09/02/how-an-ai-notetaker-became-one-of-the-few-profitable-ai-startups/). In June 2026 it reported more than 2M users and a target of $500M in 2026 sales, and is planning an agent-oriented wearable — [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-16/plaud-plans-new-wearable-as-ai-note-taking-startup-eyes-500-million-in-sales)
- **Omi (Based Hardware)** is an open-source pendant. It raised $2M led by Tim Draper (January 2025) — [Omi](https://www.omi.me/blogs/news/omi-raises-2m). It claims 300K+ users, while the Play Store shows only 10K+ downloads — [Layer3Labs review](https://www.layer3labs.io/guides/omi-ai-review) (secondary; numbers conflict)
- **Friend (Avi Schiffmann)** is an AI companion necklace, not a note-taker. The original sold for $99. "Friend 2.0" reportedly launched at $249 in July 2026, and the first production run reportedly sold about 5,000 units — [Layer3Labs](https://www.layer3labs.io/gear/reviews/friend-ai-necklace) (secondary, low confidence)
- **Microsoft Recall** rolled out to Copilot+ PCs in spring 2025 (KB5055627), after delays and a redesign (opt-in, encrypted, Windows Hello gate). Signal blocked Recall screenshots via a DRM flag (May 2025). Brave (July 2025) and AdGuard block it by default. Critics compared it to a keylogger, and testers found it captured credit card numbers and SSNs despite filters — [Engadget](https://engadget.com/ai/brave-and-adguard-now-block-microsoft-recall-by-default-152601475.html); [AlternativeTo](https://alternativeto.net/news/2025/7/adguard-joins-signal-and-brave-in-blocking-microsoft-recall-calling-it-a-privacy-concern-)
- **Screenpipe** is a Paris-based YC company founded in 2024, with about 10 staff and $3.4M raised — [startups.fm](https://startups.fm/startups/screenpipe). It markets itself as the open-source, local-first Rewind replacement — [Screenpipe docs](https://docs.screenpi.pe/vs-rewind). The business model is contested. Its own blog cites a $400 lifetime license. A third party says it has moved to subscriptions ($25/mo Standard, $50/seat Pro, $150/seat Enterprise) and that the license is "source-available" under a commercial license rather than MIT — [MemX](https://memx.app/alternatives/rewind-ai/) (conflict unresolved)

**Personal data stores / "own your data" infrastructure**
- **Solid / Inrupt:** Tim Berners-Lee's Solid Pods are personal online data stores with app-level access control — [Wikipedia](https://en.wikipedia.org/wiki/Solid_(web_decentralization_project)). The Open Data Institute took stewardship of the Solid Project in October 2024. In 2025 Inrupt announced Solid+MCP "Agentic Wallets" (May 29, 2025) and continued its Digital Flanders government deployment — [Inrupt blog](https://www.inrupt.com/blog)
- **digi.me:** I found no 2025–26 news.
- **MyData Global:** not researched in this pass.

**Consumer privacy apps that consolidated**
- **Jumbo** (privacy assistant, which also deleted old social posts) was acquired by Coalition (cyber insurance) in July 2023. It stopped being updated, services ended by June 2024, and it was removed from Google Play on January 1, 2025 — [TechCrunch](https://techcrunch.com/2023/07/12/cyber-insurance-startup-coalition-acquires-privacy-assistant-jumbo/); [AppBrain](https://www.appbrain.com/app/jumbo-privacy-security/com.jumboprivacy)
- **Mine / SayMine** (it scanned your inbox to find which companies hold your data and sent deletion requests). MineOS sold the SayMine consumer app to McAfee in November 2025 for an estimated "few tens of millions" of dollars. The app was to shut down by the end of 2025 and its technology was to be folded into McAfee. MineOS had raised $42M and has pivoted to enterprise privacy governance, including a $30M Series B — [Jerusalem Post](https://www.jpost.com/business-and-innovation/article-875099); [PR Newswire](https://www.prnewswire.com/news-releases/mine-secures-30-million-in-series-b-funding-to-transform-the-landscape-of-data-privacy-governance-for-the-enterprise-302005981.html)

**Data-broker removal services**
- **Optery:** $7.45M total raised, including $4.25M in April 2025 — [CB Insights](https://www.cbinsights.com/company/optery/financials). Another source lists different totals — [Simplify](https://simplify.jobs/c/Optery). Premium tier is $249/year.
- **Incogni** (Amsterdam; Surfshark/Nord family; covers 180+ brokers) and **DeleteMe** (Somerville, MA; founded 2011): I found no public funding or revenue figures — [CB Insights](https://www.cbinsights.com/compare/incogni-vs-optery)
- **Consumer Reports Permission Slip** acts as a CCPA authorized agent. Users verify email and phone and sign an authorization. CR emails each request with proof of designation and uses web forms where a company refuses email — [CR Innovation](https://innovation.consumerreports.org/?p=9066)
- **Vana (the opposite approach):** $25M raised (Paradigm $18M Series A, Coinbase Ventures $5M, Polychain $2M seed; announced September 2024). Users pool data into "DataDAOs" that license it for AI training in exchange for ownership in the resulting models — [Vana](https://vana.org/posts/vana-raises-funding-to-build-user-owned-ai-and-overcome-the-data-wall); [The Block](https://www.theblock.co/post/316962/coinbase-ventures-leads-5-million-round-in-vana-a-network-for-user-owned-data). Mainnet launched, with "dozens" of DataDAOs live. The Reddit DataDAO reportedly has about 140K users — [Vana 2025](https://vana.org/posts/2025-call-for-datadaos); [Solana Compass](https://solanacompass.com/learn/accelerate-25/ship-or-die-at-accelerate-2025-lightning-talk-vana)

### Inferences
- The recurring pattern is that a cloud-hosted lifelog vendor is acquired, then shuts down, the device is bricked, or users must re-consent to new terms (Humane, Limitless/Rewind, Bee). This is the strongest marketing hook for a "your copy lives in your storage" app. It also argues for local-first or user-held storage over a vendor cloud, since the reclamation app could be acquired too.
- Consumer privacy-utility apps struggle as standalone businesses (Jumbo, SayMine) and tend to end up as features of security suites (Coalition, McAfee). Subscription removal services survive on recurring data-broker re-listing, which a one-time purge does not need. A recurring "AI-training watch" plus "new data since last sync" could create that recurrence.
- Positioning versus Vana: Vana tells users to monetize their data. A reclaim-and-purge app tells users to withdraw it. Both start with the same export pipeline (Takeout, DMA APIs), so the two could even be complementary.

### Gaps
- No verified traction or funding numbers for DeleteMe, Incogni, Privacy Bee, digi.me, or MyData Global. Permission Slip usage counts not found.
- Status of Bee after the acquisition (closing date, whether audio is now stored) is not confirmed from primary sources.
- Screenpipe's licensing and pricing conflict is unresolved. The repository LICENSE should be checked.

---

## 2. Legal rights the app can leverage

### Takeaway
The EU offers the strongest toolkit: GDPR access, erasure, portability and objection rights, plus DMA Art. 6(9), which forces gatekeepers to provide continuous, real-time portability APIs to authorized third parties. In the US, CCPA/CPRA rights plus the authorized-agent regulation (11 CCR §7063) let an app file requests on a user's behalf, and California's DROP platform (live for consumers since January 1, 2026; brokers obligated from August 1, 2026) handles data brokers for free. Korea's PIPA Art. 35-2 portability right is phasing in by sector, with a 2025 draft decree to extend it to large controllers generally.

### Cited Findings
**EU**
- GDPR Art. 15 (access), 17 (erasure, with exceptions such as legal obligations and legal claims), 20 (portability of data the user "provided," in machine-readable form, including direct transmission where technically feasible) and 21 (right to object to processing based on legitimate interest) — **[background, not re-verified this session]** [gdpr-info.eu Art 15](https://gdpr-info.eu/art-15-gdpr/), [Art 17](https://gdpr-info.eu/art-17-gdpr/), [Art 20](https://gdpr-info.eu/art-20-gdpr/), [Art 21](https://gdpr-info.eu/art-21-gdpr/)
- **Art. 21 in practice (Meta AI training):** Meta began training on EU users' public Facebook/Instagram content on May 27, 2025 under "legitimate interest" (Art. 6(1)(f)). Users had to file an objection form, and noyb says Meta treated objections as effective only if filed before training began — [The Hacker News](https://thehackernews.com/2025/05/meta-to-train-ai-on-eu-user-data-from.html); [noyb cease-and-desist (PDF)](https://noyb.eu/sites/default/files/2025-05/noyb_cease%20and%20desist%20letter_Meta%20AI_pub.pdf). The Irish DPC allowed it to proceed after Meta gave guarantees — [The Register](https://www.theregister.com/2025/05/22/irish_data_protection_commission_gives/)
- **DMA Art. 6(9):** Gatekeepers (Google, Meta, Apple, Amazon, Microsoft, ByteDance, Booking) must provide effective portability of data "provided by" or "generated through the activity of" users, with continuous and real-time access, free of charge, to the user or to third parties the user authorizes. In practice this is delivered as APIs. Google's Data Portability API supports authorizations of up to 180 days — [EU Commission DMA developer portal](https://digital-markets-act.ec.europa.eu/developer-portal/end-user-data-portability_de); [Tech Policy Press](https://techpolicy.press/can-data-portability-shift-power-in-europes-digital-ecosystem)

**California / US**
- CCPA/CPRA rights to know/access, delete, correct and opt out of sale/sharing (Cal. Civ. Code §§1798.100–.135) — **[background, not re-verified]** [CPPA](https://cppa.ca.gov/)
- **Authorized agents (11 CCR §7063):** A business may require proof of the consumer's signed permission and may also require the consumer to verify their own identity directly or confirm the agent's authority. A power of attorney under the Probate Code removes those extra steps, but a business cannot *require* one. Agents must maintain reasonable security and use the data only to fulfill the request, verify identity, or prevent fraud — [Cornell LII](https://law.cornell.edu/regulations/california/11-CCR-7063)
- Agent friction is real. CR's 2021 test found problems with agent-sent opt-outs at nearly every one of the 21 companies tested — [CR report (PDF)](https://innovation.consumerreports.org/CR_AuthorizedAgentCCPA_022021_VF_.pdf). Cornell research on Permission Slip data found widely inconsistent company handling — [Cornell Tech](https://www.pi.tech.cornell.edu/spotlight/pegah)
- **Delete Act / DROP:** A free state platform run by the CPPA, open to residents since January 1, 2026. Identity is verified via the California Identity Gateway or Login.gov. Since August 1, 2026, registered brokers must check DROP every 45 days and process deletions, with penalties of $200 per request per day of noncompliance. Brokers registered January 1–31, 2026 ($6,000 fee). Estimates of the registry size range from 500 to 600+ brokers — [CPPA](https://www.cppa.ca.gov/data_brokers/); [Malwarebytes](https://www.malwarebytes.com/blog/news/2026/08/californians-can-tell-data-brokers-to-drop-their-information); [CyberInsider](https://cyberinsider.com/california-launches-tool-enabling-mass-opt-out-from-data-brokers/). Note that DROP covers *data brokers* only, not first-party platforms like Google or Meta.
- Other US states (VA, CO, CT, TX, OR, etc.) grant access, deletion and portability rights, and several also recognize authorized agents for opt-outs (e.g., Colorado's universal opt-out mechanism) — **[background, not researched this pass]**

**South Korea**
- PIPA Art. 35-2 (from the 2023 amendment) lets data subjects request transmission of their personal information to themselves or to a qualified third party. Controllers must respond within a reasonable time, at reasonable cost and by reasonable means, and may refuse if identity is unverified — [Mondaq](https://www.mondaq.com/data-protection/1295960/south-korea-passes-major-overhaul-of-data-protection-law)
- Phase-in: telecom guidelines (December 2024–January 2025 consultation) allow transmission only via authorized institutions — [Digital Policy Alert](https://digitalpolicyalert.org/event/25665-opened-consultation-for-guidelines-on-personal-information-transmission-in-telecommunications). In June 2025 the PIPC proposed extending the right to controllers with more than ₩150bn in revenue and more than 1M data subjects (consultation June 23 – August 4, 2025) — [MLex/Law360](https://www.law360.com/mlex/data-privacy-security/articles/2356026/south-korea-aims-to-expand-data-portability-right-with-proposed-amendment)
- PIPA Art. 37-2 (in force from March 2024) gives a right to refuse, or to request an explanation of, fully automated decisions — **[background, not re-verified]** [Chambers 2026 Korea guide](https://practiceguides.chambers.com/practice-guides/data-protection-privacy-2026/south-korea)

### Inferences
- An app can lawfully act as a CCPA authorized agent, following the Permission Slip model, but must expect companies to demand direct consumer verification. Storing a signed authorization per user and per request is essential.
- The DMA 6(9) APIs are the best technical rail for "copy everything" in the EU. Outside the EU, the app likely depends on Takeout-style bulk exports or scraping. That fragmentation is the case for Doctorow's "adversarial interoperability."
- GDPR Art. 21 is the legal hook for AI-training opt-outs in the EU, but Meta's "before training began" position means *timing* matters. Prompt, automated objection filing is a real value proposition.
- In Korea, third-party portability recipients must meet security standards or be "authorized institutions," so an app would likely need certification to act as a recipient rather than just help users download.

### Gaps
- Whether Korea's 2025 expansion decree was finalized and its effective date (check pipc.go.kr).
- Meta's specific DMA 6(9) API implementation details.
- Up-to-date summary of which non-California US states explicitly allow authorized agents for deletion (versus opt-out only).

---

## 3. AI-training opt-outs (what users can actually toggle, 2025–26)

### Takeaway
Most platforms now train on consumer data by default, with buried opt-outs that apply only going forward and do not cover public posts or data already used. The controls are fragmented across a dozen settings pages. This is exactly what an app could inventory and toggle or monitor.

### Cited Findings
- **Google Gemini:** The control is "Gemini Apps Activity," renamed "Keep Activity." Even when it is off, Google may retain conversations for up to 72 hours for safety. Workspace settings are controlled by the admin — [humandatarights.org guide](https://www.humandatarights.org/guides/how-to-opt-out-of-ai-training/); [trustscan.dev](https://trustscan.dev/blog/opt-out-llm-training-data-2026)
- **Meta:** EU/UK users get an Art. 21 objection form (see section 2). Outside the EU there is no equivalent opt-out for public posts — [The Hacker News](https://thehackernews.com/2025/05/meta-to-train-ai-on-eu-user-data-from.html)
- **LinkedIn:** Settings & Privacy → Data privacy → "Data for Generative AI Improvement." Training reportedly expanded to include Microsoft affiliates in November 2025 — [humandatarights.org](https://www.humandatarights.org/guides/how-to-opt-out-of-ai-training/)
- **X/Grok:** On by default (some EU accounts tested were off). The toggle is under Privacy & safety → Grok & third-party collaborators. Opting out does not remove past data, and public posts remain crawlable regardless — [humandatarights.org](https://www.humandatarights.org/guides/how-to-opt-out-of-ai-training/); [pixeldefence](https://pixeldefence.com/how-to-opt-out-of-ai-training/)
- **Anthropic (consumer Free/Pro/Max, including Claude Code):** Announced August 28, 2025. New or resumed chats are used for training unless the user opts out, with a deadline of September 28, 2025. Opting in extends retention to 5 years (versus 30 days). Commercial and API customers are excluded. The setting can be changed anytime, and deleted chats are excluded from future training — [Goldfarb](https://www.goldfarb.com/updates-to-anthropics-claude-ai-terms-and-privacy-policy-what-you-need-to-know/); [Gigazine](https://www.gigazine.net/gsc_news/en/20250901-anthropic-claude-updates-consumer-terms-privacy-policy)
- **OpenAI (ChatGPT):** Settings → Data Controls → "Improve the model for everyone." The guides also mention Temporary Chats, which are not used for training — [trustscan.dev](https://trustscan.dev/blog/opt-out-llm-training-data-2026)
- **Reddit (licensing, no user opt-out):** Google reportedly pays about $60M per year (confirmed by Reuters). The OpenAI deal is estimated at about $70M per year. AI licensing was about 10% of Reddit revenue. In 2026 the WSJ reported Reddit weighing cutting Google's access as the deal neared renewal — [The Decoder](https://the-decoder.com/reddit-signs-60-million-annual-training-data-deal-with-google/); [Slashdot/Adweek](https://tech.slashdot.org/story/25/02/14/0019213/); [AI Weekly](https://aiweekly.co/alerts/reddit-weighs-cutting-google-ai-access-as-60m-deal-expires)
- **Slack, Adobe, Microsoft consumer:** No sources retrieved this session (the EFF opt-out guide was unreachable: [EFF](https://www.eff.org/pages/i-want-opt-out-ai-tools-or-training-made-big-tech)). From background: Slack's global models opt-out requires a workspace admin to email Slack (May 2024 controversy), and Adobe clarified in 2024 that it does not train Firefly on customer cloud content — **[background, not re-verified]**

### Inferences
- An "AI exposure audit" feature (which platforms train on you, current toggle state, one-tap deep links) is low-cost and high-value. Many toggles can only be deep-linked, not set via API, so expect browser automation or guided flows.
- Opt-outs are prospective. Pairing them with *deletion* of historical content is the only way to reduce future scraping of public posts, and even that cannot unlearn trained weights.

### Gaps
- Primary-source verification of each company's current toggle names (they change often). Slack, Adobe and Microsoft Copilot consumer settings were not verified.

---

## 4. Deletion mechanics and whether deletion is honored

### Takeaway
Deletion is a multi-stage process. Data leaves active systems, then backups expire over months, and legal holds or regulatory retention can override deletion. There is FTC precedent showing companies have *not* honored deletion (Amazon Alexa). The app should present "delete" as "request + verify + re-check," not as a guarantee.

### Cited Findings
- Google's published deletion pipeline: deleted data is removed from active systems, and backups are retired on a rolling basis. A 2018 Google whitepaper cited about 2 months on average to delete from active systems and about 6 months for backups to expire (Cloud context) — [Google Cloud deletion docs](https://docs.cloud.google.com/security/deletion); [VentureBeat](https://venturebeat.com/business/google-whitepaper-explains-gcp-data-deletion-policies)
- Google consumer controls: My Activity offers auto-delete at 3, 18 or 36 months, and new accounts default to 18 months for Web & App Activity (2020 change). Takeout supports bulk export. Bulk deletion of Gmail, Drive and Photos uses search plus select-all or the API, and Trash empties after 30 days — **[background, not re-verified]** [Google My Activity help](https://support.google.com/accounts/answer/465)
- **FTC v. Amazon (Alexa, 2023):** $25M civil penalty under COPPA. Amazon told parents it deleted children's voice recordings but kept transcripts and did not fully honor deletion requests, retaining the data to improve voice recognition. The order requires deletion and bars use of that data to train algorithms (the FTC's "algorithmic disgorgement" remedy) — [MediaPost](https://www.mediapost.com/publications/article/385888/ftc-fines-amazon-25m-over-childrens-voice-record.html); [AP via ABC17](https://abc17news.com/news/ap-national-news/2023/05/31/ftc-hits-amazon-with-25-million-fine-for-violating-child-privacy-with-alexa-voice-assistant/). There was also a separate $5.8M Ring settlement — same sources.
- Meta account deletion: Meta says deletion can take up to 90 days, with copies possibly remaining in backups and retained for legal reasons — **[background, not re-verified]** [Meta Help Center](https://www.facebook.com/help/224562897555674)
- Anthropic example of retention changing with training consent (30 days versus 5 years) — [Goldfarb](https://www.goldfarb.com/updates-to-anthropics-claude-ai-terms-and-privacy-policy-what-you-need-to-know/)

### Inferences
- The product should log each deletion request with a timestamp, then re-run an access/export request (GDPR Art. 15 / CCPA "right to know") 90 to 180 days later to verify deletion. This turns the access right into a deletion-audit tool.
- GDPR Art. 17 and CCPA §1798.105 both contain exceptions (legal obligations, security, internal uses), so partial deletion is lawful. The UX must set expectations.

### Gaps
- No primary 2025–26 data on how quickly Google or Meta actually purge consumer data, or independent audits of deletion.
- Did not verify whether Gmail, Drive and Photos APIs support programmatic bulk permanent deletion at scale under current quota and scope policies.

---

## 5. Demand signals

### Takeaway
Concern about AI and personal data is a majority position in the US and is rising. Pew found 50% more concerned than excited in 2025 (up from 37% in 2021), 57% feel little control, and 61% want more. Cultural momentum (Doctorow's best-selling *Enshittification*, Recall backlash, de-Googling) supports the narrative. Hard numbers on de-Google behavior are thin.

### Cited Findings
- Pew (June 9–15, 2025, n=5,023): 50% are more concerned than excited about AI (37% in 2021). 57% say they have little or no control over AI in their lives, and 61% want more control — [Engadget](https://www.engadget.com/americans-growing-anxious-as-ai-adoption-expands-pew-research-finds-204500137.html); [Inside Radio](https://www.insideradio.com/free/pew-americans-weigh-ai-s-promise-and-risks/article_2ea8af3a-a720-43a8-9c3b-df614dd4c8c3.html)
- Pew (February 2026, n=5,119) via a secondary summary: 71% say AI will make personal data less secure — [UGA AgTech Data](https://agtechdata.uga.edu/pew-study-finds-americans-fear-ais-societal-impact/) (secondary; verify against Pew)
- Earlier Pew (2023): 53% said AI hurts more than helps in keeping personal information private, and 10% said it helps — [Pew topic page](https://pewresearch.org/topic/internet-technology/emerging-technology/page/2)
- Lifelogging demand: Plaud has more than 1M devices sold and more than 2M users, and targets $500M in 2026 sales — [Forbes](https://www.forbes.com/sites/iainmartin/2025/09/02/how-an-ai-notetaker-became-one-of-the-few-profitable-ai-startups/); [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-16/plaud-plans-new-wearable-as-ai-note-taking-startup-eyes-500-million-in-sales). Big Tech acquiring Limitless and Bee also signals that incumbents see value in personal-memory data.
- Recall backlash, with Signal, Brave and AdGuard shipping blocks, shows that a visible segment rejects third-party "record everything" — [Engadget](https://engadget.com/ai/brave-and-adguard-now-block-microsoft-recall-by-default-152601475.html)
- De-Google: only anecdotal blog evidence was found — [blog](https://blog.ahmednsane.com/why-im-de%E2%80%91googleing-my-life-and-you-should-too/)

### Inferences
- The demand is split. People want AI memory and second-brain tools (Plaud, Limitless) *and* don't trust Big Tech to hold that data (Recall backlash, Pew control numbers). "Your second brain, built from data you reclaimed, stored by you" bridges both.

### Gaps
- r/degoogle subscriber counts and growth, Google Trends data for "delete Google account" and "opt out AI training," and DeleteMe/Incogni customer counts were not found.

---

## 6. Ideology and framing

### Takeaway
The app sits where several established intellectual currents meet: data dignity (Lanier/Weyl), adversarial interoperability and anti-enshittification (Doctorow), personal data stores (Solid/MyData), and credible exit (Bluesky/AT Protocol). Each has public critiques worth anticipating.

### Cited Findings
- **Enshittification (Doctorow):** The term was coined in 2022 and was the American Dialect Society's 2023 Word of the Year. The book *Enshittification: Why Everything Suddenly Got Worse and What to Do About It* (Verso/MCD, October 2025) was longlisted for the FT Business Book of the Year 2025 — [Wikipedia](https://en.wikipedia.org/wiki/Enshittification); [Verso](https://www.versobooks.com/products/3341-enshittification); [Washington Monthly](https://washingtonmonthly.com/2025/10/30/the-cory-doctorow-doctrine-enshittification/); [Slate](https://slate.com/technology/2025/10/cory-doctorow-enshittification-internet-tech-silicon-valley.html)
- **Adversarial interoperability / "competitive compatibility":** Doctorow's EFF-era concept of building interoperating tools without permission (scrapers, exporters). It underpins the "data liberation" framing — **[background, not re-verified]** [EFF](https://www.eff.org/deeplinks/2019/10/adversarial-interoperability)
- **Data dignity (Jaron Lanier & E. Glen Weyl):** People should be recognized and paid for the data they generate, possibly via "mediators of individual data" (collective bargaining bodies). Lanier has applied the idea to generative AI provenance — **[background, not re-verified]** [HBR 2018 "A Blueprint for a Better Digital Society"](https://hbr.org/2018/09/a-blueprint-for-a-better-digital-society). Vana's DataDAOs are effectively a crypto implementation of these "mediators" — [Vana](https://vana.org/posts/vana-raises-funding-to-build-user-owned-ai-and-overcome-the-data-wall)
- **Bluesky/AT Protocol:** Account data lives in a Personal Data Server (PDS) that can be self-hosted, and portable DID identity survives moving hosts — [Educative](https://www.educative.io/blog/bluesky-social-network-system-design). Critics note that almost all users stay on Bluesky's servers in practice, and that migration only helps if done before restrictions appear — [kevinak.se (opinion, February 2026)](https://kevinak.se/blog/be-wary-of-bluesky)
- **Solid** (Berners-Lee, ODI stewardship since October 2024) — [Wikipedia](https://en.wikipedia.org/wiki/Solid_(web_decentralization_project))

### Inferences
- There is a tension to resolve in positioning. Data dignity and Vana imply "your data is valuable, so get paid." Purge and opt-out imply "your data shouldn't be used at all." The app can stay neutral by focusing on the user's control and copy, and leaving monetization as a downstream choice.
- The Bluesky critique ("ownership in theory, centralization in practice") applies to this app too. If reclaimed data lands in the app's own cloud, it becomes the next Limitless. Local or user-chosen storage and open formats are what make the claim credible.

### Gaps
- MyData Global's current activity was not researched. Bluesky's 2025–26 user count was not verified. Lanier's recent (2023–26) writing on AI and data dignity was not retrieved.
