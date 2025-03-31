import json
import re
from bs4 import BeautifulSoup
from openai import OpenAI

def extract_and_optimize_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 精确提取 product-main 主要内容
    product_main = soup.select_one('div.product-main') # 使用 CSS 选择器精确提取 product-main,文章的主要内容div
    if not product_main:
        raise ValueError("❌ No <div class='product-main'> found in the HTML")

    # 使用CSS选择器排除product-content、product-div及其子元素

    main_content = product_main.select(
        '''
        :not(div.product-div):not(div.product-div *):not(div.product-content):not(div.product-content *),
        h2,
        h3,
        p:not(:has(img))
        '''
    )

    
    print("======== 实际处理元素统计 ========")
    print(f'总元素数: {len(main_content)}')
    print('元素类型分布:', {tag.name: len(list(product_main.find_all(tag.name))) for tag in main_content})
    print('样例内容:', [str(tag)[:100] for tag in main_content[:3]] if main_content else '空')

    # 提取结构化内容
    extracted_text = {"h2": [], "h3": [], "p": []}
    for tag in main_content:
        if tag.name in ['h2', 'h3']:
            extracted_text[tag.name].append(tag.get_text(strip=True))
        elif tag.name == 'p':
            # 保留图片但移除其他无关元素
            text = ''.join([str(t) for t in tag.contents 
                           if (not hasattr(t, 'name')) 
                           or t.name not in ['script']])
            extracted_text['p'].append(text)

    print("======== 提取的正文内容 ========")
    print(extracted_text)  # 检查是否真的提取到正文

    # 如果提取的正文为空，直接返回原 HTML
    if not any(extracted_text.values()):
        print("❌ 提取的正文内容为空，可能 HTML 解析有问题！")
        return str(soup)

    cleaned_text = json.dumps(extracted_text, ensure_ascii=False, indent=2)

    # 生成原始元素数量统计
    original_counts = {k: len(v) for k, v in extracted_text.items()}

    # 调用 OpenAI API
    client = OpenAI(
        api_key="# 你的api_key", 
        base_url="https://api.chatanywhere.tech/v1" # 调用api的地址
        )
    
    response = client.chat.completions.create(
        model="deepseek-r1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that optimizes text."},
            {"role": "user", "content": f"严格遵循以下要求优化文本:\n1. 保持原始h2/h3/p标签的数量和顺序,不要随意的合并标签,只是对标签内容进行优化\n2. Role: SEO Optimization Specialist | Language: English | Expertise: SEO strategies & best practices | Skills: Technical SEO (audit, schema, sitemaps, speed), Content Optimization (keywords, on-page, quality, internal linking) | Rules: Ethical SEO, transparency, continuous learning, user experience focus | Workflows: Audit, keyword research, content optimization, performance monitoring | Goal: Improve website visibility & organic traffic.\n3. 返回JSON格式: {{'h2': [...], 'h3': [...], 'p': [...]}}\n4. 不要添加任何解释性文字\n5. 确保每个数组元素数量与原始数据完全一致\n\n原始内容结构统计:\n{original_counts}\n\n待优化内容:\n{cleaned_text}"}
        ], #里面的第二条指令n2是给AI的指令,可以根据需要修改.
        temperature=1,  # 控制生成文本的随机性
        max_tokens=4000,  # 控制生成文本的长度
    )

    # 强化数据校验逻辑
    ai_response_text = response.choices[0].message.content.strip()
    print("======== AI 返回的原始数据 ========")
    print(ai_response_text)

    try:
        optimized_text = json.loads(ai_response_text)
        
        # 结构完整性校验
        required_keys = ['h2', 'h3', 'p']
        if not all(k in optimized_text for k in required_keys):
            raise ValueError("AI返回缺少必要字段")
        
        # 类型校验
        for key in required_keys:
            if not isinstance(optimized_text[key], list):
                raise ValueError(f"{key} 字段类型错误，应为列表")
            
            # 检查元素类型是否匹配
            for item in optimized_text[key]:
                if not isinstance(item, str):
                    raise ValueError(f"{key} 列表包含非字符串元素")

        # 数量严格匹配校验
        original_counts = {k: len(v) for k, v in extracted_text.items()}
        optimized_counts = {k: len(v) for k, v in optimized_text.items()}
        
        print("======== 数据校验结果 ========")
        print(f"原始数量: {original_counts}")
        print(f"优化数量: {optimized_counts}")
        
        if optimized_counts != original_counts:
            mismatch_details = {k: f"{optimized_counts[k]}/{original_counts[k]}" 
                              for k in original_counts if optimized_counts[k] != original_counts[k]}
            raise ValueError(f"元素数量不匹配: {mismatch_details}")
            
    except Exception as e:
        print(f"❌ 数据校验失败: {str(e)}")
        with open("error_backup.json", "w", encoding="utf-8") as f:
            json.dump({
                "error": str(e), 
                "original_counts": original_counts,
                "optimized_counts": optimized_counts,
                "response": ai_response_text
            }, f, indent=2)
        print("⚠️ 已保存详细错误日志到 error_backup.json")
        return str(soup)

    # 精准替换内容
    # 使用索引保证顺序一致性
    replacement_index = {k: 0 for k in ['h2', 'h3', 'p']}
    content_order = [(i, tag.name) for i, tag in enumerate(main_content)]  # 记录原始顺序索引
    
    print("======== 开始内容替换 ========")
    for tag in main_content:
        tag_type = tag.name
        if tag_type in ['h2', 'h3', 'p']:
            if tag_type == 'p':
                target_key = 'p'
            else:
                target_key = tag_type
            
            if replacement_index[target_key] >= len(optimized_text[target_key]):
                print(f"⚠️ {target_key} 替换索引越界，跳过该标签")
                continue
                
            new_text = optimized_text[target_key][replacement_index[target_key]]
            replacement_index[target_key] += 1
            
            # 执行替换
            if tag_type in ['h2', 'h3']:
                original = tag.get_text(strip=True)
                print(f"替换 {tag_type}: {original[:50]}... ⇒ {new_text[:50]}...")
                tag.string = new_text
            else:
                print(f"替换 p标签: 原长度{len(''.join(tag.strings))} ⇒ 新长度{len(new_text)}")
                tag.clear()
                tag.append(BeautifulSoup(new_text, 'html.parser'))

    return str(soup)

# 示例用法
if __name__ == "__main__":
    import os
    from tkinter import Tk
    from tkinter.filedialog import askdirectory

    # 创建文件选择对话框
    Tk().withdraw()
    folder_path = askdirectory(title='选择包含HTML文件的文件夹')
    if not folder_path:
        print("❌ 未选择文件夹，程序退出")
        exit()

    # 添加输出目录选择
    output_dir = askdirectory(title='选择输出文件夹（取消将使用默认目录）')
    if not output_dir:
        import datetime
        current_time = datetime.datetime.now().strftime('%y%m%d_%H%M')
        output_dir = os.path.join(folder_path, f'optimized_{current_time}')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 记录错误日志
    error_log = os.path.join(output_dir, 'error_log.txt')
    processed = 0
    success_count = 0
    error_files = []
    processing_round = 0  # 添加处理轮次计数器

    while processing_round < 1:  # 控制只执行一轮
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()

                        print(f"\n🔍 正在处理: {file}")
                        optimized_html = extract_and_optimize_html(html_content)

                        # 生成输出路径
                        rel_path = os.path.relpath(root, folder_path)
                        output_path = os.path.join(output_dir, rel_path, 
                                                f"{os.path.splitext(file)[0]}_optimized.html")
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(optimized_html)
                        
                        success_count += 1
                        print(f"✅ 成功保存到: {os.path.relpath(output_path, folder_path)}")
                    except Exception as e:
                        print(f"❌ 处理失败: {file} - {str(e)}")
                        error_files.append(file_path)
                    
                    processed += 1
                    print(f"进度: {processed}文件处理完成 ({success_count}成功 {len(error_files)}失败)")
        processing_round += 1  # 完成一轮处理后递增

    # 输出统计报告
    print(f"\n{'='*30}\n处理完成统计:\n"
          f"• 总处理文件: {processed}\n"
          f"• 成功数量: {success_count}\n"
          f"• 失败文件: {len(error_files)}\n"
          f"输出目录: {output_dir}")

    # 记录错误日志
    if error_files:
        error_log = os.path.join(output_dir, 'error_log.txt')
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write('\n'.join(error_files))
        print(f"⚠️ 失败文件列表已保存至: {error_log}")