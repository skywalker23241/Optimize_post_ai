import json
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag
from openai import OpenAI


@dataclass
class ProcessorConfig:
    api_key: str = ""
    base_url: str = "https://api.chatanywhere.tech/v1"
    model: str = "deepseek-r1"
    temperature: float = 1.0
    max_tokens: int = 4000
    content_selector: str = "div.product-main"
    exclude_rules: str = (
        ":not(div.product-div):not(div.product-div *):"
        ":not(div.product-content):not(div.product-content *),"
        "h2, h3, p:not(:has(img))"
    )
    system_prompt: str = "You are a helpful assistant that optimizes text."
    user_prompt: str = (
        "Strictly follow the requirements below to optimize the text:\n"
        "1. Keep the original number and order of h2/h3/p tags. "
        "Do not merge tags randomly. Only optimize the tag content.\n"
        "2. Role: SEO Optimization Specialist | Language: English | "
        "Expertise: SEO strategies & best practices | "
        "Skills: Technical SEO (audit, schema, sitemaps, speed), "
        "Content Optimization (keywords, on-page, quality, internal linking) | "
        "Rules: Ethical SEO, transparency, continuous learning, user experience focus | "
        "Workflows: Audit, keyword research, content optimization, performance monitoring | "
        "Goal: Improve website visibility & organic traffic.\n"
        "3. Return in JSON format: {{'h2': [...], 'h3': [...], 'p': [...]}}\n"
        "4. Do not add any explanatory text.\n"
        "5. Ensure that the number of elements in each array is exactly the same as the original data.\n\n"
        "Original content structure statistics:\n{original_counts}\n\n"
        "Content to be optimized:\n{cleaned_text}"
    )


@dataclass
class ProcessResult:
    success: bool
    message: str
    file_path: str = ""
    original_counts: dict = field(default_factory=dict)
    optimized_counts: dict = field(default_factory=dict)
    optimized_html: str = ""


class SEOProcessor:
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None or self._client.api_key != self.config.api_key:
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client

    def parse_html(self, html_content: str) -> tuple[list[Tag], dict]:
        soup = BeautifulSoup(html_content, "html.parser")

        product_main = soup.select_one(self.config.content_selector)
        if not product_main:
            raise ValueError(
                f"No element matching '{self.config.content_selector}' found in HTML"
            )

        # Select h2, h3, p tags, excluding p tags that contain images
        all_tags = product_main.find_all(["h2", "h3", "p"])
        main_content = [tag for tag in all_tags if not (tag.name == "p" and tag.find("img"))]

        extracted_text: dict[str, list[str]] = {"h2": [], "h3": [], "p": []}
        for tag in main_content:
            if tag.name in ("h2", "h3"):
                extracted_text[tag.name].append(tag.get_text(strip=True))
            elif tag.name == "p":
                text = "".join(
                    str(t)
                    for t in tag.contents
                    if (not hasattr(t, "name")) or t.name not in ["script"]
                )
                extracted_text["p"].append(text)

        if not any(extracted_text.values()):
            raise ValueError("Extracted main content is empty — HTML parsing may have failed")

        return main_content, extracted_text

    def call_ai(self, extracted_text: dict, original_counts: dict) -> tuple[dict, str]:
        cleaned_text = json.dumps(extracted_text, ensure_ascii=False, indent=2)

        user_content = self.config.user_prompt.format(
            original_counts=original_counts,
            cleaned_text=cleaned_text,
        )

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Handle different response formats (some proxies return non-standard responses)
        if isinstance(response, str):
            raise ValueError(
                f"API returned a string instead of a response object. "
                f"This usually means the API key is invalid or the Base URL is incorrect. "
                f"Response: {response[:500]}"
            )

        if not hasattr(response, "choices") or not response.choices:
            raise ValueError(
                f"API response has no 'choices' field. "
                f"Response type: {type(response).__name__}, "
                f"Content: {str(response)[:500]}"
            )

        raw_response = response.choices[0].message.content.strip()

        # Strip <think>...</think> blocks from reasoning models like DeepSeek R1
        think_pattern = re.compile(r"<think>.*?</think>", re.DOTALL)
        ai_response_text = think_pattern.sub("", raw_response).strip()

        # If stripping left nothing, try to find JSON inside <think> blocks as fallback
        if not ai_response_text:
            think_contents = re.findall(r"<think>(.*?)</think>", raw_response, re.DOTALL)
            for block in think_contents:
                block = block.strip()
                json_match = re.search(r'\{[\s\S]*"h2"[\s\S]*"p"[\s\S]*\}', block)
                if json_match:
                    ai_response_text = json_match.group(0)
                    break

        # If still empty, try to extract JSON from the full raw response
        if not ai_response_text:
            json_match = re.search(r'\{[\s\S]*"h2"[\s\S]*"p"[\s\S]*\}', raw_response)
            if json_match:
                ai_response_text = json_match.group(0)

        # Strip markdown code fences (```json ... ```) from models like Gemini
        if ai_response_text:
            code_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', ai_response_text, re.DOTALL)
            if code_block:
                ai_response_text = code_block.group(1).strip()

        if not ai_response_text:
            raise ValueError(
                f"AI response is empty or contains no extractable JSON. "
                f"Raw response:\n{raw_response[:1000]}"
            )

        optimized_text = json.loads(ai_response_text)
        return optimized_text, raw_response

    def validate_response(
        self, optimized_text: dict, original_counts: dict
    ) -> tuple[bool, str]:
        required_keys = ["h2", "h3", "p"]

        if not all(k in optimized_text for k in required_keys):
            return False, "AI response is missing required fields (h2/h3/p)"

        for key in required_keys:
            if not isinstance(optimized_text[key], list):
                return False, f"Field '{key}' should be a list, got {type(optimized_text[key]).__name__}"
            for item in optimized_text[key]:
                if not isinstance(item, str):
                    return False, f"Field '{key}' contains non-string element: {type(item).__name__}"

        optimized_counts = {k: len(v) for k, v in optimized_text.items()}

        if optimized_counts != original_counts:
            mismatch = {
                k: f"{optimized_counts[k]}/{original_counts[k]}"
                for k in original_counts
                if optimized_counts.get(k, 0) != original_counts[k]
            }
            return False, f"Element count mismatch: {mismatch}"

        return True, "Validation passed"

    def replace_content(
        self, html_content: str, main_content: list[Tag], optimized_text: dict
    ) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        product_main = soup.select_one(self.config.content_selector)
        if not product_main:
            return html_content

        # Re-select tags using the same filtering logic as parse_html
        all_tags = product_main.find_all(["h2", "h3", "p"])
        fresh_main_content = [
            tag for tag in all_tags if not (tag.name == "p" and tag.find("img"))
        ]

        replacement_index = {"h2": 0, "h3": 0, "p": 0}

        for tag in fresh_main_content:
            tag_type = tag.name
            if tag_type not in ("h2", "h3", "p"):
                continue

            target_key = tag_type
            if replacement_index[target_key] >= len(optimized_text[target_key]):
                continue

            new_text = optimized_text[target_key][replacement_index[target_key]]
            replacement_index[target_key] += 1

            if tag_type in ("h2", "h3"):
                tag.string = new_text
            else:
                tag.clear()
                tag.append(BeautifulSoup(new_text, "html.parser"))

        return str(soup)

    def process_file(self, file_path: str) -> ProcessResult:
        try:
            raw_response = ""
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            main_content, extracted_text = self.parse_html(html_content)
            original_counts = {k: len(v) for k, v in extracted_text.items()}

            optimized_text, raw_response = self.call_ai(extracted_text, original_counts)

            valid, msg = self.validate_response(optimized_text, original_counts)
            if not valid:
                return ProcessResult(
                    success=False,
                    message=f"Validation failed: {msg}",
                    file_path=file_path,
                    original_counts=original_counts,
                    optimized_counts={k: len(v) for k, v in optimized_text.items()},
                )

            optimized_html = self.replace_content(html_content, main_content, optimized_text)

            return ProcessResult(
                success=True,
                message="Processed successfully",
                file_path=file_path,
                original_counts=original_counts,
                optimized_counts={k: len(v) for k, v in optimized_text.items()},
                optimized_html=optimized_html,
            )

        except json.JSONDecodeError as e:
            return ProcessResult(
                success=False,
                message=f"AI response is not valid JSON: {e}\nRaw response preview:\n{raw_response[:800]}",
                file_path=file_path,
            )
        except Exception as e:
            return ProcessResult(
                success=False,
                message=f"Error: {e}",
                file_path=file_path,
            )
