# OptimizePostAI

Batch SEO optimization for HTML articles powered by AI. Now with a modern desktop GUI.

## Features

- **Batch processing** — optimize an entire folder of HTML files in one click
- **AI-powered SEO** — uses OpenAI-compatible APIs (DeepSeek, Gemini, etc.) to rewrite headings and paragraphs
- **Data validation** — ensures optimized content preserves original tag counts (h2/h3/p) before writing
- **Configurable prompts** — edit System Prompt and User Prompt directly in the UI
- **Non-blocking UI** — processing runs on a background thread, interface stays responsive
- **Real-time console** — colored logs show progress, errors, and validation details

## Requirements

- Python 3.10+
- PyQt6
- BeautifulSoup4
- OpenAI (Python SDK)

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

## How It Works

### 1. HTML Parsing

The app extracts article content from a configurable CSS selector (default: `div.product-main`), collecting all `<h2>`, `<h3>`, and `<p>` tags (excluding `<p>` tags that contain images).

### 2. AI Optimization

Extracted text is sent to the AI model as a JSON structure:

```json
{
  "h2": ["heading 1", "heading 2", ...],
  "h3": [],
  "p": ["paragraph 1", "paragraph 2", ...]
}
```

The model returns an optimized version with the same structure and element counts.

### 3. Data Validation

Before writing, the app verifies:
- Response contains `h2`, `h3`, `p` keys
- All values are lists of strings
- Array lengths exactly match the original counts

If validation fails, the file is skipped and the error is logged.

### 4. Content Replacement

Optimized text is precisely mapped back to original HTML tags by index, preserving all non-text elements (images, links, formatting).

## UI Tabs

| Tab | Contents |
|-----|----------|
| **Files** | Input/output folder selection, CSS selector, exclude rules |
| **API** | API Key, Base URL, Model, Temperature, Max Tokens |
| **Prompts** | System Prompt and User Prompt editors |

## Project Structure

```
Optimize_post_ai/
├── app.py                  # Entry point
├── requirements.txt
├── core/
│   ├── processor.py        # SEOProcessor — parsing, API calls, validation, replacement
│   └── worker.py           # WorkerThread — QThread for background batch processing
└── ui/
    ├── main_window.py      # Main window with tabbed layout
    ├── styles.py           # QSS stylesheet (Japanese minimalist aesthetic)
    └── console_widget.py   # Terminal-style log console
```

## Configuration

All settings are configurable through the GUI:

| Setting | Default | Description |
|---------|---------|-------------|
| Content CSS Selector | `div.product-main` | CSS selector for the article container |
| Model | `deepseek-r1` | AI model name |
| Temperature | `1.0` | Controls randomness (lower = more focused) |
| Max Tokens | `4000` | Maximum response length |
| Base URL | `https://api.chatanywhere.tech/v1` | OpenAI-compatible API endpoint |

## Troubleshooting

**"AI response is not valid JSON"**
- The model may return content wrapped in `<think>` blocks or markdown fences. The app tries to extract JSON automatically. Check the Console's `Raw response preview` to see what the model returned.

**"Element count mismatch"**
- The model merged or removed tags. Lower the Temperature (e.g. 0.5) to reduce this.

**"No element matching selector"**
- Your HTML structure differs from the default. Inspect your HTML and update the CSS Selector in the Files tab.

## Legacy Scripts

The original CLI scripts are kept for reference:

- `optimize_post_ai_seo-original-en_us.py` — English version
- `optimize_post_ai_seo-original-zh_cn.py` — Chinese version
