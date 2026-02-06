# Moltbook Isn't So Mysterious: How I Used It To Give a Prediction Agent Life

I’ve looked on in awe at the AI industry in the past week. My pick of the latest trends is Moltbook, along with the growing band of agents on the platform (I think you've already guessed this). I first came across Moltbook on an Andrej Karpathy post on X—where else would I have gotten the ‘gist?’ Karpathy talked about people’s Clawdbots self-organizing on a site that’s basically Reddit but for AIs. You know, I was sold from there. So I went into a small rabbit’s hole and learnt what I could about this impending overthrow: humans are about to suffer at the hands of the bots. The conspiracy theorists are about to be proven right, ha!

But seriously, though, I paid no attention to the nerds, lol, and decided I’d like to have my agent on Moltbook. Almost at the same time, I saw someone building a prediction agent that researches and trades on Polymarket. This gave me an idea: an agent that checks Polymarket for market opportunities (re: mispriced odds), and sends them as alerts through a Telegram bot and on Moltbook. Prediction markets are a big thing now, and I was already motivated because I wanted a peek behind the curtains of Moltbook; it was easy to settle on that idea. 

## AI Autonomy

The promise has always been autonomy. Systems that act and not just answer. Now, while most of the world (at least the side that I’ve been in) plays with chatbots and simple assistants, a quiet evolution is happening in the undercurrents. This revolution is seeing AI agents growing from assistants to economic actors. They’re growing from summarizing emails to scanning markets and analyzing probabilities. Now I’ve joined this frontier. I built Poylvuuvu, an autonomous AI agent that hunts for “alpha” on the prediction market, Polymarket. In the following paragraphs, I’ll explain how I built this.

## The Vision Explained

So, I explained how I stumbled upon the idea for the agent I worked with, but what really made up my mind for me was that it was a darn good idea, too. The markets these days are noisy. Crypto, stocks, and prediction markets all feel like they’re in constant red. So you’re forced to ask how you find value in such markets. While the first two markets run on sentiment, reports that are often massaged, and even memes, prediction markets (like Polymarket) are, however, brutally truthful. They settle on a binary Yes/No that’s based on objective reality. A simple: Did the event happen? Yes or No. This functionality makes them the perfect background for AI.

This was my hypothesis: Markets are efficient, but not always instantly. I’ll explain. When news breaks, such as a court ruling or a footballer getting injured, there’s a lag before the odds are adjusted to reflect the new reality. AIs are free from emotional bias and are capable of digesting vast context in split seconds, so they should be able to spot these “mispriced odds” (market opportunities) before the crowd does. This is where Polyvuvu comes in. 

## What is Moltbook?

Before we move to how I set this all up, let's talk about the elephant in the room, Moltbook. Moltbook is a social platform where autonomous AI agents can post and interact with each other. Moltbook uses skills, something the open agent platform OpenClaw is built around. A skill is a folder containing a set of instructions that Claude loads dynamically to improve performance on specialized tasks or workflows. You can find thousands of skills on clawhub.ai.

![Moltbook Home](docs/images/moltbook_home.png)

Something you’d notice early when you start to explore Moltbook is how you install it—you point your agent to the skill by sending them a message with a link to this URL: `https://www.moltbook.com/skill.md`.
In that file are installation instructions and curl commands that your agent uses to interact with the Moltbook API, which allows it to register an account, read posts, comment, add posts and create Submolts (forums). There’s also a Heartbeat system in the installation skill that causes your agent to periodically interact with the network.

I didn’t do this for my agent, however. I instead went the traditional engineering way, where I manually created `SKILL.md`, `skill.json`, and `heartbeat.py` files. In my `client.py` file is the code to interact with the API endpoints described in those docs. So for Polyvuvu, the intelligence on how to use Moltbook is in the code it runs, not in the agent’s runtime memory. 

## The Setup

Because Polyvuvu has access to the same files and instructions in the official skills file, it isn’t just a script; it’s a persona. A persona that I ended up not needing to install OpenClaw for. If you’re not bypassing OpenClaw as I did, these are the commands to install it with:

```bash
npm i -g openclaw
```

And to start the onboarding process once installed:

```bash
openclaw onboard
```

Select Quick Start and use the API key of your preferred LLM provider. Select your model and choose a channel to control your bot from (Telegram, WhatsApp, Slack, etc.).

For this project, I used a Telegram bot. I searched for BotFather on Telegram, ran the command: `/newbot`, gave my bot a name (Polyvuvu Alerts, in my case), and then got a Bot API Token. This token allows the agent to send alerts (high-confidence market opportunities) to the user via the bot. Without this token, the agent would find profitable trades but have no way to tell me about them until I checked the logs manually.

![Telegram Alert](docs/images/telegram_alert.png)

On Moltbook, I registered the agent as **PolyvuvuTrader**, and it posts its picks there, explaining its logic, and interacting with other agents. Before you can complete the registration, though, you’ll have to verify you own the agent by clicking a claim link that redirects you to X to post a verification string. Once posted, Moltbook verified the post to link the PolyvuvuTrader identity to my X account.

![Profile](docs/images/profile.png)

This process is how Moltbook ensures "Proof of Human" or "Proof of Identity" for its agents, and it helps the platform prevent spam bots.

## The Stack

This is a passion project—to see how Moltbook works for myself—so I wanted the architecture to be simple but resilient.

*   I used **Google Gemini 2.0** (via OpenRouter) for the agent’s reasoning capabilities. This model works well enough to understand nuance in prediction markets.
*   **Polymarket Gamma API** helped with a direct feed into the world’s largest prediction market order book.
*   The agent connected to **Moltbook** via the Moltbook API.
*   Wrote a custom Python heartbeat module that ensures the agent stays “alive,” checking messages and updating its portfolio over long periods.

## Agent Logic

The core logic of the agent is a loop that runs every 30 minutes and performs the following actions:

1.  **Scan**: The agent fetches the top 50 active markets by volume, ignoring low-liquidity markets to ensure that the trades are actionable.
2.  **Audit**: For every market scanning done, the agent “audits” the odds. It looks at the question in the prediction (e.g., “Will Bitcoin crash to $40k?”), the current yes or no prices (e.g., 50 cents), and then the eternal context. 
3.  **Reason**: The agent performs a “Cognitive Check.” It evaluates the price of the prediction, e.g., "The market says 25%. Is this fair? Or is it an edge?"
4.  **Score**: The AI then assigns a confidence score (1-10). It only triggers an alert if the score is 7 or higher.
5.  **Act**: The agent does three things:
    *   Send a notification to my phone via the Telegram bot
    *   Log a “Paper Trade” in its local portfolio to track PnL (to prove its accuracy, or lack of it)
    *   Post a public analysis to Moltbook, complete with its reasoning and probability charts.

## Your Friendly Neighborhood Bot

Polyvuvu isn’t a lonely bot. I added a **Cross-Agent collaboration feature** that allows the agent DM other “trusted agents” on Moltbook to ask for a peer review whenever it finds a high-confidence trade. For instance, it can send its analysis to a peer (like “NewsBot”), asking, “What do you think?” mimicking a real hedge fund where analysts argue trades before committing capital.

![Moltbook Post](docs/images/post_example.png)

## Conclusion

Early testing showed the agent successfully identified inefficiencies in sports and crypto markets. Injury news not fully priced in, and crypto milestones were major causes of this market opportunity, Polyvuvu found. The real thrill for me, however, is watching the agent’s Paper Trading portfolio grow as it maintains its own ledger.

The industry—the world really—is moving towards a world of "Agent Swarms," (teams of specialized AIs for tasks like researching, trading, risk managing, etc.) working together. Polyvuvu is just one node in this future network. The future of finance is looking agentic, no?

---

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Status: Autonomous](https://img.shields.io/badge/Status-Autonomous-green.svg)

This weekend, I built **Polyvuvu**, an autonomous AI agent that hunts for "alpha" on [Polymarket](https://polymarket.com) and posts its wins to [Moltbook](https://moltbook.com).

## 📂 Project Map

```ascii
Polyvuvu/
├── main.py              # 🧠 The Brain (Entry Point)
├── config.py            # ⚙️ Configuration
├── heartbeat.py         # 💓 Lifecycle Manager
├── portfolio.py         # 💼 Paper Trading Ledger
├── analysis/
│   └── gemini_analyzer.py # 🤖 LLM Logic (Gemini/OpenRouter)
├── polymarket/
│   └── fetcher.py       # 📊 Market Data Client
├── moltbook/
│   └── client.py        # 🦞 Social Network Client
└── alerts/
    └── telegram_bot.py  # 📱 Notification System
```

## 🛠️ Technical Usage

If you want to run this agent yourself:

1.  **Clone the repo**
    ```bash
    git clone https://github.com/Elvaceishim/polyvuvu.git
    cd polyvuvu
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure `.env`**
    ```bash
    cp .env.example .env
    # Add your Moltbook, Telegram, and Gemini keys
    ```

4.  **Run the Agent**
    ```bash
    python main.py --moltbook
    ```
    
    Other commands:
    ```bash
    # View Portfolio
    python main.py --portfolio

    # Check Status
    python main.py --status
    ```

## ⚠️ Disclaimer
*This project is an experiment in AI autonomy. It is not financial advice. Prediction markets carry risk. The "Paper Trading" feature is for simulation purposes only.*

## 📜 License
MIT License. See [LICENSE](LICENSE) for details.
