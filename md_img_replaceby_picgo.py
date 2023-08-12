import os
import re
import sys
import requests
import tinify

# 设置你的 tinify API Key
tinify.key = "xxx"

# 查找本地图片链接
def find_local_image_links(markdown_content):
    pattern = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(pattern, markdown_content)
    return matches


# 使用 tinify 进行图片压缩
def compress_image(input_image_path, output_image_path):
    try:
        source = tinify.from_file(input_image_path)
        source.to_file(output_image_path)
        print("Image compressed:", output_image_path)
    except tinify.AccountError as e:
        print("Tinify API key is invalid or has exceeded its usage limit.")
        sys.exit(1)
    except tinify.ClientError as e:
        print("Client error:", e.message)
        sys.exit(1)
    except tinify.ServerError as e:
        print("Server error. Please try again later.")
        sys.exit(1)
    except tinify.ConnectionError as e:
        print("A network connection error occurred.")
        sys.exit(1)
    except Exception as e:
        print("An error occurred:", str(e))
        sys.exit(1)

# 调用 PicGo 上传图片
def upload_image_to_image_host(local_image_path):
    url = "http://127.0.0.1:36677/upload"
    payload = {
        "list": [local_image_path]
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            result_urls = data.get("result", [])
            if result_urls:
                print("Image uploaded:",result_urls[0])
                return result_urls[0]
            else:
                return "No result URL found"
    else:
        return 0

# 获取文件绝对路径
def get_absolute_image_path(input_markdown_path, relative_path):
    base_path = os.path.dirname(input_markdown_path)
    absolute_path = os.path.join(base_path, relative_path)
    return absolute_path

# 替换本地图片链接为图床图片链接
def replace_local_with_image_host_and_compress(markdown_content, input_markdown_path):
    local_image_links = find_local_image_links(markdown_content)
    for local_link in local_image_links:
        absolute_local_link = get_absolute_image_path(input_markdown_path, local_link)

        # 压缩图片并保存到临时目录
        compressed_image_path = os.path.join(os.path.dirname(absolute_local_link), "compressed_images", os.path.basename(local_link))
        if not os.path.exists(os.path.dirname(compressed_image_path)):
            os.makedirs(os.path.dirname(compressed_image_path))
        compress_image(absolute_local_link, compressed_image_path)

        image_host_link = upload_image_to_image_host(compressed_image_path)
        if image_host_link:
            markdown_content = markdown_content.replace(local_link, image_host_link)
        else:
            print("Image upload failed!")
            sys.exit(1)

    return markdown_content

# 读取 Markdown 文件，转换并输出
def convert_and_output(input_markdown_path):
    with open(input_markdown_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    markdown_with_image_host = replace_local_with_image_host_and_compress(markdown_content, input_markdown_path)

    output_markdown_path = input_markdown_path.replace(".md", "_out.md")
    with open(output_markdown_path, 'w', encoding='utf-8') as file:
        file.write(markdown_with_image_host)


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py input_markdown_file")
        sys.exit(1)

    input_markdown_file = sys.argv[1]

    if os.path.isabs(input_markdown_file):
        # 如果输入的参数是绝对路径
        input_markdown_path = input_markdown_file
    else:
        # 如果输入的参数是相对路径，将其转换为绝对路径
        current_dir = os.getcwd()
        input_markdown_path = os.path.join(current_dir, input_markdown_file)
        
    convert_and_output(input_markdown_path)

if __name__ == "__main__":
    main()
