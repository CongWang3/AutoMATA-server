#!/usr/bin/env python3
"""
JWT密钥生成工具
用于生成安全的随机密钥供生产环境使用
"""
import secrets
import argparse


def generate_secret_key(length: int = 32) -> str:
    """
    生成安全的随机密钥
    
    Args:
        length: 密钥长度（字节）
        
    Returns:
        base64编码的安全密钥
    """
    return secrets.token_urlsafe(length)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成JWT密钥')
    parser.add_argument(
        '-l', '--length', 
        type=int, 
        default=32,
        help='密钥长度（默认32字节）'
    )
    
    args = parser.parse_args()
    
    secret_key = generate_secret_key(args.length)
    
    print("生成的安全密钥:")
    print("=" * 50)
    print(secret_key)
    print("=" * 50)
    print("\n使用方法:")
    print("1. 将此密钥设置为环境变量:")
    print(f"   export SECRET_KEY='{secret_key}'")
    print("2. 或在 .env 文件中添加:")
    print(f"   SECRET_KEY={secret_key}")
    print("\n⚠️  请妥善保管此密钥，不要泄露给他人!")


if __name__ == "__main__":
    main()