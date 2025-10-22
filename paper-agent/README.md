# ArXiv Scraper Agent

An automated agent that monitors arXiv for papers on specified topics, summarizes findings using LLMs, and updates a Notion database.

If you find this useful, give me a star ⭐ Thank you!!!

## 🚀 Features

- **Automated Monitoring**: Discover new arXiv papers on your topics daily.
- **LLM Summarization**: Generate summaries, tags, and insights (e.g., with Google Gemini).
- **Notion Integration**: Automatically update structured paper information.
- **Flexible Scheduling**: Run daily, weekly, or on custom intervals.
- **Logging & Error Handling**: Detailed logs with rotation and robust error recovery.


## 📋 Quick Start

### 1. Enviroment Setup
```bash
git clone https://github.com/hosytuyen/awesome-AI-agents-scalable-oversight
cd paper-agent
```
```
conda create -n paper-agent python-3.10
conda activate paper-agent
python setup.py
touch .env
```


### 2. Configure your experiment at `.env`. 

We provide an example below for the experiment with Gemini and the Scalable Oversight topic

```
# Google Gemini API Configuration
GOOGLE_API_KEY=YOUR_GEMINI_API

# Notion API Configuration
NOTION_API_KEY=YOUR_NOTION_API
NOTION_DATABASE_ID=YOUR_NOTION_DATABASE_ID

# arXiv Configuration
ARXIV_QUERY='abs:"scalable oversight" OR abs:"AI oversight" OR abs:"Multi-agent oversight" OR abs:"Automation of oversight" OR abs:"Scalable alignment"'
MAIN_QUERY='scalable oversight'

# Scheduling Configuration
CHECK_FREQUENCY=daily
CHECK_TIME=09:00

# Logging Configuration
LOG_LEVEL=INFO
```


## 📊 Usage

### Paper Check (For one-time comprehensive check)
```bash
# Check last 365 days
python main.py --mode manual --days 365
```

### Scheduled Monitoring
```bash
# Start daily monitoring at 9 AM
python main.py --mode scheduled
```


