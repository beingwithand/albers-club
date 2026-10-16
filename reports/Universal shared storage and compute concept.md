# Product concept: Mycel (working name)

**One line:** your own encrypted cloud that captures your digital life automatically, lives on your devices first, is backed up by people you trust, and borrows spare space from a wider pool, with no one, including us, able to read it.

## Problem

People's digital lives are scattered across Chrome, Google Drive and Photos, Instagram saves, Reddit, and laptops that are never fully backed up. The companies holding that data can lock people out, scan it, change its price, or shut down. Pocket, Rewind/Limitless and Google Photos' backup API all disappeared or closed in 2024–25. Self-hosting fixes ownership but demands sysadmin skills. Earlier "trade your disk space" products (Wuala, CrashPlan friend backup, Symform) proved the idea appealing but failed to make it reliable or profitable.

## Who it's for

The first users are privacy-minded "prosumers" and families with a spare always-on machine (old laptop, mini PC, NAS) who want Google-level convenience without Google holding the keys. Next come their friends and relatives, who join a circle. Developers and self-hosters are early advocates, not the revenue base.

## How it works: three tiers

**Tier 1: your devices.** A desktop agent, browser extension and phone app capture Chrome tabs, history and bookmarks, Google Drive, scheduled Google Takeout and platform export files, links shared from Instagram and other apps via the share sheet, and whole-computer snapshots. Everything is chunked and encrypted on-device with post-quantum-ready keys, then synced across your devices through an always-on "hub". Phones capture and cache; the hub holds the full copy. An optional encrypted anchor copy sits in a cheap bucket.

**Tier 2: your trusted circle.** Invite family and friends. Each hub stores erasure-coded, unreadable fragments of the others' data, so any 10 of 20 pieces rebuild a file. Circle members also hold shares of your recovery key: three of five can help you back in if you lose everything. A simple ledger shows what you give and take.

**Tier 3: the open pool.** Vetted, always-on hosts anywhere contribute disk in exchange for storage credits weighted by uptime. Your cold data is spread in wide stripes, one fragment per household and network, audited continuously and repaired automatically. The pool starts as extra redundancy and becomes the primary cold tier only once it proves itself.

**Compute** stays on your own devices: indexing, OCR, thumbnails, search embeddings and local AI run on whichever of your machines is plugged in and idle. Sharing compute beyond that waits until private computation on strangers' hardware is actually safe. As of 2026 it is not.

## What's different

Ente and Proton offer encrypted clouds, but they hold your only copy and capture nothing. Immich and Nextcloud are powerful but technical and single-location. Storj, Sia and Filecoin are wholesale infrastructure for developers. Mycel combines automatic capture, device-first storage, social backup and recovery, and a pool, and it is designed to keep working if the company disappears: tiers 1–2 need no company servers, and the coordinator and relays are open source and self-hostable.

## Business model

The software is free for tiers 1–2. Revenue comes from three sources:

- A subscription for the encrypted anchor backup, hosted relay and premium connectors (roughly the price of Google One, sold on control rather than cost).
- Pool storage for people with no spare disk, paid in cash or earned with credits.
- An optional pre-configured "hub" box sold at a margin.

Credits are non-transferable and non-cashable, so there are no tokens and no securities or MiCA exposure. Cash payouts to large hosts may come later, with KYC.

## MVP (first 6 months)

A desktop agent (macOS and Windows), Chrome extension, phone share-sheet app, and a hub mode for any always-on computer. It captures Chrome data, Drive, Takeout and Instagram/Reddit/X exports plus restic-based laptop snapshots; syncs encrypted through the hub with an anchor backup to a bucket; and ships a printed recovery kit, passkey unlock and one-click restore tests. No pool yet; circle backup comes in v2.

## Key risks

**Reliability:** home uptime, repair bandwidth and NAT (about 30% of connections need relays); mitigated by always-on hosts only plus the anchor copy. **Abuse and law:** CSAM, UK Online Safety Act and Korean filtering duties attach to public sharing; stay private by default, hash-scan shared links, take down at the coordinator. **Key loss:** layered recovery. **Closing APIs:** rely on exports and on-device capture. **Demand:** unproven; run a small paid beta measuring retention and restores before building the pool. **Seeding:** the first multi-terabyte upload takes days to weeks.
