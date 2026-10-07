# Crypto Wallet Tracker Telegram Bot (Aiogram 3 + SQLite)

A feature-rich Telegram bot built with **Aiogram 3** and **SQLite** to monitor cryptocurrency wallet balances (Ethereum and Tron) in real-time, featuring automated background alerts.

## Good Points & Features
* **Full FSM Wizard:** Smooth step-by-step state machine for adding new wallets (address -> custom name -> network selection).
* **Multi-Chain Balance Tracking:** Integrates with Etherscan, Trongrid, and CoinGecko APIs to calculate exact USD values for both Ethereum (ETH) and Tron (TRX) wallets.
* **Background Monitoring & Alerts:** Includes a periodic background task (`asyncio`) that loops every 30 minutes and fires an alert if any wallet drops below $10 USD.
* **Database Management:** Complete CRUD operations via SQLite (`wallets.db`) supporting multi-user wallet storage, custom names, and deletion routines.

## Technologies Used
* **Python**
* **Aiogram 3** (modern asynchronous Telegram bot framework with FSM)
* **SQLite3** (persistent user and wallet storage)
* **Requests & Aiohttp** (external blockchain & price feeds: Etherscan, Trongrid, CoinGecko)
* **Asyncio** (for non-blocking background monitoring tasks)

---
> **Project Status:** Advanced utility bot.
---
