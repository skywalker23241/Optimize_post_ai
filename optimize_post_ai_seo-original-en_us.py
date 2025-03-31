import json
import re
from bs4 import BeautifulSoup
from openai import OpenAI

def extract_and_optimize_html(html_content):
    """
    Extract and optimize the HTML content.

    Args:
        html_content (str): The HTML content to be processed.

    Returns:
        str: The optimized HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Precise extraction of the main content of product-main
    
    product_main = soup.select_one('div.product-main') 
    # important, this is the main content of your post, make sure your main content inside this div
    if not product_main:
        raise ValueError("❌ No <div class='product-main'> found in the HTML")

    # Use CSS selectors to exclude product-content, product-div and their child elements
    main_content = product_main.select(
        '''
        :not(div.product-div):not(div.product-div *):not(div.product-content):not(div.product-content *),
        h2,
        h3,
        p:not(:has(img))
        '''
    )
    
    print("======== Actual processing element statistics ========")
    print(f'Total number of elements: {len(main_content)}')
    print('Element type distribution:', {tag.name: len(list(product_main.find_all(tag.name))) for tag in main_content})
    print('Sample content:', [str(tag)[:100] for tag in main_content[:3]] if main_content else 'Empty')

    # Extract structured content
    extracted_text = {"h2": [], "h3": [], "p": []}
    for tag in main_content:
        if tag.name in ['h2', 'h3']:
            extracted_text[tag.name].append(tag.get_text(strip=True))
        elif tag.name == 'p':
            # Keep images but remove other irrelevant elements
            text = ''.join([str(t) for t in tag.contents 
                           if (not hasattr(t, 'name')) 
                           or t.name not in ['script']])
            extracted_text['p'].append(text)

    print("======== Extracted main content ========")
    print(extracted_text)  # Check if the main content is really extracted

    # If the extracted main content is empty, return the original HTML directly
    if not any(extracted_text.values()):
        print("❌ The extracted main content is empty. There may be a problem with HTML parsing!")
        return str(soup)

    cleaned_text = json.dumps(extracted_text, ensure_ascii=False, indent=2)

    # Generate the original element quantity statistics
    original_counts = {k: len(v) for k, v in extracted_text.items()}

    # Call the OpenAI API
    client = OpenAI(
        api_key="important_api_key",  # Replace with your actual API key
        base_url="https://api.chatanywhere.tech/v1"  # Replace with your actual base URL
        )
    
    response = client.chat.completions.create(
        model="deepseek-r1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that optimizes text."},
            {"role": "user", "content": f"Strictly follow the following requirements to optimize the text:\n1. Keep the original number and order of h2/h3/p tags. Do not merge tags randomly. Only optimize the tag content.\n2. Role: SEO Optimization Specialist | Language: English | Expertise: SEO strategies & best practices | Skills: Technical SEO (audit, schema, sitemaps, speed), Content Optimization (keywords, on-page, quality, internal linking) | Rules: Ethical SEO, transparency, continuous learning, user experience focus | Workflows: Audit, keyword research, content optimization, performance monitoring | Goal: Improve website visibility & organic traffic.\n3. Return in JSON format: {{'h2': [...], 'h3': [...], 'p': [...]}}\n4. Do not add any explanatory text.\n5. Ensure that the number of elements in each array is exactly the same as the original data.\n\nOriginal content structure statistics:\n{original_counts}\n\nContent to be optimized:\n{cleaned_text}"}
        ], 
        # The second instruction n2 inside is for the AI and can be modified as needed.
        temperature=1,  # Control the randomness of the generated text
        max_tokens=4000,  # Control the length of the generated text
    )

    # Strengthen the data verification logic
    ai_response_text = response.choices[0].message.content.strip()
    print("======== Original data returned by AI ========")
    print(ai_response_text)

    try:
        optimized_text = json.loads(ai_response_text)
        
        # Structure integrity verification
        required_keys = ['h2', 'h3', 'p']
        if not all(k in optimized_text for k in required_keys):
            raise ValueError("The data returned by AI is missing necessary fields.")
        
        # Type verification
        for key in required_keys:
            if not isinstance(optimized_text[key], list):
                raise ValueError(f"The type of the {key} field is incorrect. It should be a list.")
            
            # Check if the element types match
            for item in optimized_text[key]:
                if not isinstance(item, str):
                    raise ValueError(f"The {key} list contains non-string elements.")

        # Strict quantity matching verification
        original_counts = {k: len(v) for k, v in extracted_text.items()}
        optimized_counts = {k: len(v) for k, v in optimized_text.items()}
        
        print("======== Data verification results ========")
        print(f"Original quantity: {original_counts}")
        print(f"Optimized quantity: {optimized_counts}")
        
        if optimized_counts != original_counts:
            mismatch_details = {k: f"{optimized_counts[k]}/{original_counts[k]}" 
                              for k in original_counts if optimized_counts[k] != original_counts[k]}
            raise ValueError(f"Element quantity mismatch: {mismatch_details}")
            
    except Exception as e:
        print(f"❌ Data verification failed: {str(e)}")
        with open("error_backup.json", "w", encoding="utf-8") as f:
            json.dump({
                "error": str(e), 
                "original_counts": original_counts,
                "optimized_counts": optimized_counts,
                "response": ai_response_text
            }, f, indent=2)
        print("⚠️ Detailed error log has been saved to error_backup.json")
        return str(soup)

    # Precise content replacement
    # Use indices to ensure order consistency
    replacement_index = {k: 0 for k in ['h2', 'h3', 'p']}
    content_order = [(i, tag.name) for i, tag in enumerate(main_content)]  # Record the original order index
    
    print("======== Start content replacement ========")
    for tag in main_content:
        tag_type = tag.name
        if tag_type in ['h2', 'h3', 'p']:
            if tag_type == 'p':
                target_key = 'p'
            else:
                target_key = tag_type
            
            if replacement_index[target_key] >= len(optimized_text[target_key]):
                print(f"⚠️ Replacement index for {target_key} is out of bounds. Skipping this tag.")
                continue
                
            new_text = optimized_text[target_key][replacement_index[target_key]]
            replacement_index[target_key] += 1
            
            # Perform replacement
            if tag_type in ['h2', 'h3']:
                original = tag.get_text(strip=True)
                print(f"Replace {tag_type}: {original[:50]}... ⇒ {new_text[:50]}...")
                tag.string = new_text
            else:
                print(f"Replace p tag: Original length {len(''.join(tag.strings))} ⇒ New length {len(new_text)}")
                tag.clear()
                tag.append(BeautifulSoup(new_text, 'html.parser'))

    return str(soup)

# Example usage
if __name__ == "__main__":
    import os
    from tkinter import Tk
    from tkinter.filedialog import askdirectory

    # Create a file selection dialog
    Tk().withdraw()
    folder_path = askdirectory(title='Select a folder containing HTML files')
    if not folder_path:
        print("❌ No folder selected. The program exits.")
        exit()

    # Add an output directory selection
    output_dir = askdirectory(title='Select an output folder (canceling will use the default directory)')
    if not output_dir:
        import datetime
        current_time = datetime.datetime.now().strftime('%y%m%d_%H%M')
        output_dir = os.path.join(folder_path, f'optimized_{current_time}')
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Record error logs
    error_log = os.path.join(output_dir, 'error_log.txt')
    processed = 0
    success_count = 0
    error_files = []
    processing_round = 0  # Add a processing round counter

    while processing_round < 1:  # Control to execute only one round
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()

                        print(f"\n🔍 Processing: {file}")
                        optimized_html = extract_and_optimize_html(html_content)

                        # Generate the output path
                        rel_path = os.path.relpath(root, folder_path)
                        output_path = os.path.join(output_dir, rel_path, 
                                                f"{os.path.splitext(file)[0]}_optimized.html")
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(optimized_html)
                        
                        success_count += 1
                        print(f"✅ Successfully saved to: {os.path.relpath(output_path, folder_path)}")
                    except Exception as e:
                        print(f"❌ Processing failed: {file} - {str(e)}")
                        error_files.append(file_path)
                    
                    processed += 1
                    print(f"Progress: {processed} files processed ({success_count} succeeded, {len(error_files)} failed)")
        processing_round += 1  # Increment after completing one round of processing

    # Output the statistical report
    print(f"\n{'='*30}\nProcessing completion statistics:\n"
          f"• Total processed files: {processed}\n"
          f"• Number of successful files: {success_count}\n"
          f"• Number of failed files: {len(error_files)}\n"
          f"Output directory: {output_dir}")

    # Record error logs
    if error_files:
        error_log = os.path.join(output_dir, 'error_log.txt')
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write('\n'.join(error_files))
        print(f"⚠️ The list of failed files has been saved to: {error_log}")
