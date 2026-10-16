# Device-to-device (P2P) sync and personal networking: state as of October 2026

Research date: 2026-10-16. Method: web search (about 18 queries). Direct fetches of tailscale.com and iroh.computer failed with DNS errors in this environment, so some facts about those projects come from search snippets and third-party write-ups and are marked as such. Older information is labeled with its date.

---

## 1. File sync tools: Syncthing, Resilio, LocalSend, KDE Connect, AirDrop/Quick Share, Möbius Sync

### Takeaway
Syncthing is still the main open-source P2P sync engine. Version 2.0 (August 2025) moved its database to SQLite and is on 2.0.x point releases. The official Android app was retired in December 2024, and the community fork by Catfriend1 (Syncthing-Fork) now fills that role. iOS has no official client; Möbius Sync is the paid third-party option and is limited by iOS background rules. The biggest interop change is Google's own AirDrop implementation in Quick Share (Pixel 10, November 2025). It is direct P2P, but it only works when the Apple device is set to "Everyone for 10 minutes".

### Cited Findings
**Syncthing 2.x**
- Syncthing 2.0 (August 2025) moved its database from LevelDB to SQLite, for easier maintenance and fewer bugs. The first launch runs a migration that can take a long time on large setups. — [Neowin](https://www.neowin.net/news/syncthing-20-released-with-major-changes-switching-from-leveldb-to-sqlite/); [AlternativeTo, Aug 2025](https://alternativeto.net/news/2025/8/syncthing-2-0-debuts-with-sqlite-migration-new-logs-platform-changes-and-much-more); [Linuxiac](https://linuxiac.com/?p=182750)
- Other 2.0 changes:
  - Records of deleted items expire after a retention window. Launch coverage said six months, adjustable with `--db-delete-retention-interval`. Later v2.0.13 release notes reportedly say fifteen months, so the default may have changed. This is a conflict between sources.
  - A WARNING log level was added and per-package log levels are supported.
  - The CLI was reworked.
  - A default folder is no longer created on first start.
  - Rolling-hash detection of shifted data was removed.
  - Prebuilt binaries were dropped for some BSDs, Solaris/Illumos, PPC64 and Windows-on-ARM because of SQLite cross-compilation problems.
  — [Neowin](https://www.neowin.net/news/syncthing-20-released-with-major-changes-switching-from-leveldb-to-sqlite/); [GitHub v2.0.13 release](https://github.com/syncthing/syncthing/releases/tag/v2.0.13)
- The 2.0.x line continues: linuxserver.io Docker images track v2.0.16. — [newreleases.io linuxserver/docker-syncthing v2.0.16](https://newreleases.io/project/github/linuxserver/docker-syncthing/release/v2.0.16-ls216)

**Android app discontinued, and forks**
- Maintainer Simon Frei announced on the Syncthing forum (October 2024) that he was retiring syncthing-android. The last GitHub/F-Droid release shipped with the December 2024 Syncthing version. His reason was that Google Play publishing had become "something between hard and impossible", combined with no active maintenance. — [Syncthing forum: Discontinuing syncthing-android](https://forum.syncthing.net/t/discontinuing-syncthing-android/23002); [AlternativeTo, Oct 2024](https://alternativeto.net/news/2024/10/the-syncthing-android-app-is-being-discontinued-but-alternatives-remain-available)
- The syncthing/syncthing-android GitHub repo was archived (read-only) on December 3, 2024. — [GitHub syncthing-android](https://github.com/syncthing/syncthing-android)
- Users say the Play problem was the "all files access" permission, which the app needed to reach SD cards and which Google restricts. This is a user explanation, not an official statement. — [Privacy Guides forum](https://discuss.privacyguides.net/t/syncthing-for-android-discontinued/21644)
- Syncthing-Fork (Catfriend1/syncthing-android, distributed via F-Droid and GitHub) is the de facto successor. Community posts say it was updated to Syncthing 2.0. Running Syncthing in Termux is another option. — [Techlore discussion](https://discuss.techlore.tech/t/the-syncthing-android-app-is-being-discontinued-but-alternatives-remain-available/10427); [Lemmy thread on 2.0](https://lemmy.linuxuserspace.show/post/822420)
- Catfriend1 also publishes "Syncthing-Lite" (com.github.catfriend1.syncthinglite). It is a separate, early-stage client that accesses remote shares rather than syncing full folders. — [F-Droid Syncthing-Lite](https://f-droid.org/es/packages/com.github.catfriend1.syncthinglite)

**iOS: Möbius Sync**
- No official Syncthing iOS app exists, which forum members attribute to iOS technical and security restrictions. — [Syncthing forum: Syncthing on iOS/iPadOS](https://forum.syncthing.net/t/syncthing-on-ios-ipados/24610)
- Möbius Sync FAQ: "No iOS app can run continuously in the background." The app syncs only while it is open, briefly after it closes, or when iOS wakes it opportunistically. Photos are not synced as ordinary files, and files must be moved in and out through the Files app. — [Möbius Sync FAQ](https://mobiussync.com/faq/)
- User reports say background sync can take up to 24 hours to start. A common workaround is an iOS Shortcut that opens Möbius, waits about 15 seconds, then opens the target app. Users also recommend an always-on desktop or server as the hub. These reports are anecdotal. — [Obsidian forum](https://forum.obsidian.md/t/sync-mac-pc-and-ios-using-syncthing-mobius-sync/72022); [Syncthing forum: Mobius & Background Refresh](https://forum.syncthing.net/t/mobius-sync-background-refresh/16372)

**KDE Connect**
- KDE Connect desktop is on the KDE Gear cadence: 26.04.0 (April 16, 2026) and 26.04.2 (June 17, 2026). — [apps.kde.org/kdeconnect](https://apps.kde.org/en/kdeconnect/)
- Android: v1.35.13, uploaded August 7, 2026. — [APKMirror](https://www.apkmirror.com/?p=1106512)
- iOS: v0.5.5 (May 7, 2026) added an OpenSSL upgrade, a pairing-protocol version check and clipboard sync tweaks. This comes from an aggregator. — [Releasebot KDE Connect iOS](https://releasebot.io/updates/kde/kde-connect-ios)

**Quick Share and AirDrop interop**
- On November 20, 2025, Google announced that Quick Share works with Apple AirDrop, starting with the Pixel 10 family. It works in both directions.
  - It is Google's own implementation, with no partnership with Apple.
  - The Apple device must have AirDrop set to "Everyone for 10 minutes", and the receiver must accept.
  - The connection is direct P2P with no server relay, and shared content is not logged.
  - NetSPI ran a penetration test.
  - It is enabled through a "Quick Share Extension" system update plus a reboot.
  - Google said it wants to work with Apple on a "Contacts Only" mode.
  — [9to5Google](https://9to5google.com/2025/11/20/android-quick-share-airdrop-pixel-10/); [Android Authority](https://www.androidauthority.com/quick-share-works-with-airdrop-3618023); [BetaNews](https://betanews.com/2025/11/21/google-updates-android-quick-share-for-compatibility-with-apple-airdrop/)

### Inferences
- The Syncthing Android episode shows a structural risk: a tool can be technically sound and still be pushed off a platform by app-store policy, such as Google Play's storage-permission rules. Sideloading channels like F-Droid and GitHub become the lifeline.
- Syncthing 2.x is not wire-compatible with the archived official Android app in a way users trust. Anyone on Android who upgrades desktops to 2.x should use the maintained fork.
- AirDrop interop is significant but narrow. It is ad-hoc file push, not continuous sync, and "Everyone for 10 minutes" is a usability and security compromise.

### Gaps
- **Resilio Sync:** I found no 2025–2026 release information or ownership news in this session. Resilio has been a proprietary, BitTorrent-derived P2P sync tool, but this is not re-verified here.
- **LocalSend:** I found no 2025–2026 release data. The only hit was a 2024 v1.16 news item, so current version and status are unverified.
- **Quick Share AirDrop beyond Pixel 10:** I could not confirm whether the interop expanded to other Android devices (for example Pixel 9 or Samsung) by October 2026, or whether Apple responded.
- **Syncthing default retention:** The six-months vs fifteen-months conflict is unresolved.
- **The "BasicSync" fork:** The name in the brief was not found in search results and is unverified.
- **Syncthing-Fork on Google Play:** Whether the fork is on Google Play as of 2026 is unverified.

---

## 2. Networking: WireGuard, Tailscale, Headscale, NetBird, ZeroTier, Cloudflare Tunnel, Pangolin; NAT traversal, CGNAT and relays

### Takeaway
WireGuard-based mesh overlays are the standard way to make personal devices reachable anywhere. Tailscale leads. Its free Personal plan covers 3 users and 100 devices (per third-party sources). Peer Relays went GA in February 2026 and let users run their own relay nodes alongside Tailscale's DERP servers. Self-hosted options are Headscale (a Tailscale control server), NetBird (a full mesh with SSO and access control) and Pangolin (an identity-aware reverse-proxy tunnel, closer to Cloudflare Tunnel). Relays remain necessary because some NATs, including symmetric NAT, CGNAT and strict firewalls, defeat hole punching.

### Cited Findings
**Tailscale basics and free tier**
- The Personal plan is free for 3 users and up to 100 devices. One aggregator lists $0.50 per extra device, which is unconfirmed. The free tier omits features such as network flow logging. — [Toolradar pricing](https://toolradar.com/tools/tailscale/pricing); [TechRadar review](https://www.techradar.com/reviews/tailscale-vpn); [botmonster](https://botmonster.com/self-hosting/set-up-tailscale-zero-config-mesh-networking/)

**How connections work**
- Each connection is a WireGuard tunnel. The coordination server distributes only public keys and endpoint information, not traffic. Peers try direct NAT-traversed paths first, using STUN plus Tailscale's "disco" protocol. One third-party source cites over 90% direct-connection success from Tailscale metrics; this figure is secondary and not verified on tailscale.com. — [fullmetalbrackets guide](https://fullmetalbrackets.com/blog/comprehensive-guide-tailscale-securely-access-home-network); [Starmorph reference](https://blog.starmorph.com/blog/tailscale-complete-developer-reference-guide)
- DERP (Designated Encrypted Relay for Packets) is the fallback when direct links fail, typically because of symmetric NAT, strict firewalls or CGNAT.
  - It runs over TCP/TLS on port 443.
  - Relayed packets stay end-to-end WireGuard-encrypted.
  - Connections start via DERP and upgrade to direct when possible.
  - Path preference is direct, then a user peer relay, then DERP.
  — [Starmorph reference](https://blog.starmorph.com/blog/tailscale-complete-developer-reference-guide); [fullmetalbrackets](https://fullmetalbrackets.com/blog/tailscale)

**Tailscale Peer Relays**
- Beta announced October 29, 2025. That announcement said all customers can use two peer relays "for free, forever". — [Tailscale blog: peer relays beta](https://tailscale.com/blog/peer-relays-beta)
- General availability came around February 18, 2026, and includes the free Personal plan.
  - Requires Tailscale 1.86 or later.
  - The relay node cannot run on iOS, tvOS or Android, though clients on any platform can use relays.
  - GA added `tailscale ping` visibility into relay use and Prometheus/Grafana-exportable client metrics.
  — [Tailscale blog: peer-relays-ga](https://tailscale.com/blog/peer-relays-ga); [sesamedisk summary](https://sesamedisk.com/tailscale-peer-relays-available/); [groundy](https://groundy.com/articles/tailscale-peer-relays-missing-piece-true-p2p/)

**Self-hosted alternatives**
- **Headscale:** A self-hosted Tailscale control server that works with standard Tailscale clients. It has no web UI by default. — [bitdoze comparison](https://www.bitdoze.com/netbird-vs-headscale-vs-tailscale/)
- **NetBird:** A WireGuard mesh with SSO, MFA and granular access control, offered as a managed cloud service or self-hosted. Per bitdoze, it does not support hybrid setups that combine the cloud control plane with self-run relays. Users report some client battery-drain complaints (anecdotal). — [bitdoze](https://www.bitdoze.com/netbird-vs-headscale-vs-tailscale/); [Lemmy selfhosted thread](https://piefed.nullspace.lol/post/51584)
- **Pangolin:** A self-hosted "tunneled reverse proxy with identity and context aware access control". In practice it is a self-hostable alternative to Cloudflare Tunnel. Its vendor positions NetBird for device-to-device connectivity and Pangolin for publishing specific apps. This is a vendor's own comparison. — [Pangolin vs NetBird](https://pangolin.net/news/pangolin-v-netbird)
- A 2026 review says self-hosted options all cost about the same (a VPS) and differ mainly in management overhead. — [bitdoze](https://www.bitdoze.com/netbird-vs-headscale-vs-tailscale/)

### Inferences
- Every "P2P" overlay still needs two kinds of infrastructure:
  - A rendezvous or coordination service, to exchange keys and endpoints.
  - A relay for the minority of paths where hole punching fails.

  "No Big Tech cloud" therefore means either trusting a smaller vendor (Tailscale, NetBird cloud, ZeroTier) or running a VPS yourself (Headscale, NetBird self-hosted, Pangolin, or your own DERP or peer relay).
- Peer Relays reduce dependence on Tailscale-run DERP, and they work well with a home server or NAS. The phone itself cannot be a relay.
- Cloudflare Tunnel and Pangolin solve a different problem from mesh VPNs. They publish services through an inbound proxy instead of connecting devices to each other. With Cloudflare Tunnel, TLS terminates at Cloudflare, so Cloudflare can see the traffic.

### Gaps
- **ZeroTier and Cloudflare Tunnel:** No 2026-specific information was gathered for either: ZeroTier's pricing, its 1.14/2.x status or the shrinking of its free tier (unverified); Cloudflare Tunnel's free-tier terms.
- **Tailscale iOS client:** No 2026 updates were gathered, for example on battery behavior or always-on VPN.
- **Direct-connection rates:** I could not fetch tailscale.com to confirm the >90% figure or the current free-plan terms (DNS failure in this environment).
- **Free relay limit at GA:** It is unconfirmed whether the "two free peer relays" limit still holds after GA.
- **Headscale and NetBird versions:** Current versions as of October 2026 were not retrieved.

---

## 3. P2P stacks for app builders: Iroh, libp2p, Holepunch/Pear, Veilid, Willow/Earthstar, p2panda, Braid

### Takeaway
Iroh (n0) is the notable 2026 milestone. After four years and several pivots, it reached 1.0, reportedly mid-June 2026, followed by 1.0.x patches. It offers QUIC-based dial-by-public-key connections, hole punching and relay fallback. Holepunch's Pear/Hypercore stack is mature and powers Keet, but no 2026 milestone was found. Willow/Earthstar, p2panda and Veilid are still research-grade, grant-funded projects (mostly NLnet).

### Cited Findings
**Iroh**
- The n0 team states: "after four years of work and various pivots we have released iroh 1.0." An rc.1 was billed as the last release candidate. Version 0.35 was the last release before a breaking wire-protocol change, which was followed by a "0.90 canary series". — [iroh blog: The road to iroh 1.0](https://iroh.computer/blog/the-road-to-iroh-1-0); [iroh 1.0.0-rc.1](https://iroh.computer/blog/iroh-1-0-0-rc-1); [iroh 0.35](https://www.iroh.computer/blog/iroh-0-35-prepping-for-1-0); [iroh 0.90 canary](https://iroh.computer/blog/iroh-0-90-the-canary-series)
- Releases:
  - v1.0.0: about June 15, 2026.
  - v1.0.1: about June 29, 2026; fixed iroh-dns fallback nameservers and a connection-teardown race.
  - v1.0.3: updated its dependency on "noq" (n0's QUIC implementation) to 1.1.0.

  The dates come from a third-party aggregator and have not been checked against GitHub. — [instagit release notes](https://instagit.com/n0-computer/iroh/release-notes-for-iroh/); [newreleases v1.0.1](https://newreleases.io/project/github/n0-computer/iroh/release/v1.0.1); [newreleases v1.0.3](https://newreleases.io/project/github/n0-computer/iroh/release/v1.0.3)

**Holepunch / Pear / Hypercore**
- Pear Runtime is Holepunch's open-source P2P app platform. Holepunch is Tether-backed. — [pears.com launch announcement](https://pears.com/news/holepunch-unveils-groundbreaking-open-source-peer-to-peer-app-development-platform-pear-runtime/)
- The core building blocks are Hypercore, Hyperbee, Hyperdrive, Autobase, HyperDHT and Hyperswarm. Keet, a serverless P2P chat and video app, is the flagship. — [docs.pears.com](https://docs.pears.com/apps)
- In an August 2025 interview, Mathias Buus said the team had spent about a year making Hypercore faster and more robust, and was preparing a major new release focused on performance across devices. — [Semaphore podcast, Aug 29 2025](https://semaphore.io/blog/mathias-buus-madsen)

**Willow / Earthstar**
- Willow is a family of protocols (data model, Meadowcap access control, and a sync protocol) that names data explicitly, unlike hash-addressed systems. Earthstar's next version is to be built on Willow. — [Willow announcement (SSB)](https://viewer.scuttlebot.io/%25aSkAO63pHVdSFYT1xNS9PuJjjw2AbJQ%2FkBHGm4UGAT8%3D.sha256); [willow-utils](https://github.com/earthstar-project/willow-utils)
- An NLnet grant funded a Rust implementation of Willow Sync from October 2023 to September 2025. — [NLnet WillowSync](https://nlnet.nl/project/WillowSync/)

**Veilid**
- Veilid is noted only in a comparison as hash-addressed (contrasted with Willow). No current status was found. — [Autonomi forum](https://forum.autonomi.community/t/willow-a-p2p-decentralization-protocol/39093)

### Inferences
- Iroh 1.0 is arguably the first "boring, stable" Rust P2P transport with a stability commitment. It lowers the barrier for local-first apps that need device-to-device connections without building their own NAT traversal. Like Tailscale, it still relies on relays (n0-hosted by default, or self-hosted).
- Holepunch is the most production-proven fully serverless stack in consumer apps (Keet), but it is tied to its JavaScript/Bare runtime ecosystem.

### Gaps
- **libp2p:** No 2026 status was gathered (rust-libp2p and go-libp2p releases, Protocol Labs funding changes).
- **p2panda:** No current status was found (versions, NLnet funding).
- **Veilid:** No 2026 status was found (VeilidChat and similar).
- **Braid:** The IETF Braid HTTP sync extension was not researched.
- **Iroh 1.0 details:** Exact changes and guarantees could not be fetched (iroh.computer DNS failure), nor were hole-punch success rates or adoption figures.
- **Pear/Holepunch:** Whether the major release was shipped in late 2025 or 2026 is unknown.

---

## 4. iOS and Android background execution limits

### Takeaway
Phones are poor always-on sync peers. iOS does not allow continuous background execution for general apps, so Syncthing-style clients like Möbius Sync sync only when opened or opportunistically woken. Android is more permissive but has its own frictions: Doze, battery optimization, and Play policy on storage permissions. The practical pattern is phone plus an always-on hub (a NAS, home server or VPS), with the phone syncing opportunistically.

### Cited Findings
- iOS: "No iOS app can run continuously in the background." Möbius Sync syncs only while open, for a short period afterward, or on iOS background wake-ups. — [Möbius Sync FAQ](https://mobiussync.com/faq/)
- Users report the app being frozen after about a day in the background, and background sync taking up to 24 hours to start. Workarounds include iOS Shortcuts and an always-on hub. These reports are anecdotal. — [Obsidian forum](https://forum.obsidian.md/t/sync-mac-pc-and-ios-using-syncthing-mobius-sync/72022); [Syncthing forum](https://forum.syncthing.net/t/mobius-sync-background-refresh/16372)
- Forum consensus is that there is no official Syncthing iOS app because of iOS technical and security restrictions. — [Syncthing forum](https://forum.syncthing.net/t/syncthing-on-ios-ipados/24610)
- Android: Google Play policy (storage and all-files access) contributed to the official Syncthing app's retirement. — [Syncthing forum](https://forum.syncthing.net/t/discontinuing-syncthing-android/23002)
- Android users report battery drain in NetBird and earlier Syncthing clients, which reflects the cost of keeping P2P connections alive. These reports are anecdotal. — [Lemmy selfhosted](https://piefed.nullspace.lol/post/51584); [Lemmy LUS](https://lemmy.linuxuserspace.show/post/822420)
- Tailscale Peer Relay nodes cannot run on iOS or Android. — [sesamedisk](https://sesamedisk.com/tailscale-peer-relays-available/)

### Inferences
- VPN-type apps (Tailscale, WireGuard) are a partial exception on iOS. The Network Extension keeps the tunnel up, but other apps still cannot serve sync in the background. "Reachable" is not the same as "syncing".
- Push notifications, the main reliable iOS wake mechanism, typically require Apple's APNs. This reintroduces a Big Tech dependency for timely P2P sync on iPhones. (This is general platform knowledge, not sourced this session.)

### Gaps
- No primary Apple or Google documentation was fetched on BGTaskScheduler limits, Android Doze and standby buckets, or Android 15/16 foreground-service-type restrictions. These should be cited from developer.apple.com and developer.android.com if the report needs specifics.

---

## 5. Browser sync alternatives

### Takeaway
Chrome sync is not end-to-end encrypted by default. An optional custom passphrase encrypts most data so Google cannot read it, at the cost of features, and payment and address data are excluded. Firefox Sync is E2EE by design and the server is self-hostable (syncstorage-rs), but there is no official self-host Docker image and the docs are weak. xBrowserSync appears stagnant, with no updates since around 2020.

### Cited Findings
**Chrome**
- Google says synced data is always encrypted in transit and the passphrase is optional. With a custom passphrase:
  - Passwords cannot be viewed at passwords.google.com.
  - Only URLs typed into the address bar are synced as history.
  - Google Pay payment methods and addresses are not covered by the passphrase.
  - Resetting a forgotten passphrase deletes the encrypted sync data.
  — [Google Chrome Help](https://support.google.com:443/chrome/answer/1181035); [Android Central](https://androidcentral.com/how-use-custom-passphrase-securely-sync-your-chrome-passwords-and-data)
- Security researcher Wladimir Palant (2023) argued that under default Chrome sync, Google can read your data: "Whatever encryption there might be, we get to see your data whenever we want it." This is dated 2023. — [palant.info, Aug 2023](https://palant.info/2023/08/29/chrome-sync-privacy-is-still-very-bad/)

**Firefox Sync self-hosting**
- The old Python syncserver is unmaintained, replaced by the Rust syncstorage-rs. — [syncserver README archive](https://git.blob42.xyz/Archives/syncserver/src/branch/master/README.rst)
- There is no official self-host Docker image. The official syncstorage-rs image targets Google Spanner, which is what Mozilla itself uses. The docs are described as poor and outdated.
- Community docker-compose projects exist. They support multi-user and single-user modes, but syncstorage-rs has no account allowlisting.

— [porelli/firefox-sync](https://proxy-ga.blitzz.co/proxy/123456/github.com/porelli/firefox-sync); [jeena/fxsync-docker](https://github.com/jeena/fxsync-docker); [Mozilla Connect thread](https://connect.mozilla.org/t5/ideas/self-host-firefox-sync/idc-p/52511); [Ben Tasker guide](https://www.bentasker.co.uk/posts/documentation/linux/selfhosting-a-firefox-sync-server.html)

**xBrowserSync**
- AMO reviews note no updates since 2020, and users ask whether it is maintained. The default service deletes data after 21 days of inactivity. Third-party hosts such as nixnet still list it. — [AMO reviews](https://addons.mozilla.org/en-US/firefox/addon/xbs/reviews/1966109/); [nixnet.services](https://nixnet.services/xbrowsersync/)

### Inferences
- For a "no Big Tech" browser setup, the realistic options are:
  - Firefox Sync, which is E2EE but uses Mozilla's servers unless you self-host.
  - Floccus, for bookmarks only, over your own WebDAV/Nextcloud/Git.

  Chrome sync with a passphrase still runs on Google's servers and leaks metadata.

### Gaps
- **Brave Sync:** The v2 "sync chain" model (E2EE, a 24-word code, Brave-hosted server) was not verified this session.
- **Vivaldi Sync:** Its E2EE model (separate encryption password) was not verified this session.
- **Floccus:** No 2026 status or version was found.
- **xBrowserSync:** No official confirmation of archival or shutdown was found.
- **Firefox Sync E2EE:** Mozilla's E2EE design (keys derived from the account password) was not re-cited from Mozilla docs this session.
