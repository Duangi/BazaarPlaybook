"""
卡牌图片下载工具
用于补充缺失的卡牌图片，支持从URL下载并转换为webp格式
"""
import os
import sys
import requests
from PIL import Image
from io import BytesIO

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def download_and_convert_image(url: str, item_id: str, output_dir: str = "assets/images/card") -> bool:
    """
    从URL下载图片并转换为webp格式保存
    
    Args:
        url: 图片URL
        item_id: 物品ID（用作文件名）
        output_dir: 输出目录
        
    Returns:
        bool: 是否成功
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 下载图片
        print(f"[下载] 正在从 {url[:50]}... 下载图片")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 加载图片
        print(f"[转换] 正在转换为 WebP 格式...")
        image = Image.open(BytesIO(response.content))
        
        # 如果是RGBA模式，保留透明通道
        if image.mode in ('RGBA', 'LA'):
            pass  # 保持原样
        elif image.mode == 'P' and 'transparency' in image.info:
            image = image.convert('RGBA')
        else:
            # 转换为RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
        
        # 保存为webp
        output_path = os.path.join(output_dir, f"{item_id}.webp")
        image.save(output_path, 'WebP', quality=90)
        
        file_size = os.path.getsize(output_path) / 1024  # KB
        print(f"[成功] 图片已保存到: {output_path} ({file_size:.1f} KB)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[错误] 下载失败: {e}")
        return False
    except Exception as e:
        print(f"[错误] 处理失败: {e}")
        return False

def check_image_exists(item_id: str, image_dir: str = "assets/images/card") -> bool:
    """检查图片是否已存在"""
    image_path = os.path.join(image_dir, f"{item_id}.webp")
    return os.path.exists(image_path)

def main():
    """主函数"""
    print("=" * 60)
    print("卡牌图片下载工具")
    print("=" * 60)
    print("说明：")
    print("  - 输入物品ID和图片URL来下载卡牌图片")
    print("  - 图片会自动转换为WebP格式并保存到 assets/images/card/")
    print("  - 输入 'q' 或 'quit' 退出程序")
    print("=" * 60)
    print()
    
    success_count = 0
    fail_count = 0
    
    while True:
        # 询问物品ID
        print("\n" + "-" * 60)
        item_id = input("请输入物品ID (或输入 q 退出): ").strip()
        
        if item_id.lower() in ('q', 'quit', 'exit', '退出'):
            break
        
        if not item_id:
            print("[提示] 物品ID不能为空，请重新输入")
            continue
        
        # 检查图片是否已存在
        if check_image_exists(item_id):
            print(f"[警告] 图片已存在: assets/images/card/{item_id}.webp")
            overwrite = input("是否覆盖? (y/n): ").strip().lower()
            if overwrite not in ('y', 'yes', '是'):
                print("[跳过] 已取消操作")
                continue
        
        # 询问图片URL
        url = input("请输入图片URL: ").strip()
        
        if not url:
            print("[提示] URL不能为空，请重新输入")
            continue
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            print("[提示] URL格式不正确，请输入完整的URL (以 http:// 或 https:// 开头)")
            continue
        
        # 下载并转换图片
        print()
        if download_and_convert_image(url, item_id):
            success_count += 1
        else:
            fail_count += 1
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print(f"下载完成！")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {fail_count} 个")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[退出] 用户中断操作")
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
