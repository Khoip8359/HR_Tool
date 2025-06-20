#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
JWT Token 獲取工具
專門為 Postman 測試生成 Token
"""
import requests
import json


def get_jwt_token():
    """獲取 JWT Token 用於 Postman 測試"""
    print("🔑 JWT Token 獲取工具")
    print("=" * 40)
    
    # API 端點
    base_url = "http://localhost:5000"
    login_url = f"{base_url}/auth/login"
    
    # 獲取用戶憑據
    print("請輸入登入憑據:")
    username = input("用戶名: ").strip()
    password = input("密碼: ").strip()
    
    # 可選的伺服器配置
    server = input("AD 伺服器 (預設: 192.168.1.245): ").strip() or "192.168.1.245"
    domain = input("AD 網域 (預設: FULINVN_TN): ").strip() or "FULINVN_TN"
    
    # 準備登入請求
    login_data = {
        "username": username,
        "password": password,
        "server": server,
        "domain": domain
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"\n🔄 正在向 {login_url} 發送登入請求...")
    
    try:
        # 發送登入請求
        response = requests.post(login_url, json=login_data, headers=headers, timeout=10)
        
        print(f"響應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                # 提取用戶信息和 Token
                user_info = data['data']['user']
                tokens = data['data']['tokens']
                access_token = tokens['access_token']
                
                print("\n✅ 登入成功!")
                print("=" * 50)
                print("👤 用戶信息:")
                print(f"   用戶名: {user_info.get('username')}")
                print(f"   顯示名稱: {user_info.get('display_name')}")
                print(f"   是否主管: {user_info.get('is_manager')}")
                print(f"   部門: {user_info.get('department')}")
                print(f"   權限: {user_info.get('permissions')}")
                
                print("\n🔑 Token 信息:")
                print(f"   Token 類型: {tokens.get('token_type')}")
                print(f"   有效期: {tokens.get('expires_in')} 秒")
                print(f"   會話 ID: {tokens.get('session_id')}")
                
                print("\n📋 Postman 使用說明:")
                print("=" * 50)
                print("1. 複製以下 Access Token:")
                print("-" * 30)
                print(access_token)
                print("-" * 30)
                
                print("\n2. 在 Postman 中設置 Authorization:")
                print("   - Type: Bearer Token")
                print("   - Token: [貼上上面的 Access Token]")
                
                print("\n3. 或者在 Headers 中手動添加:")
                print("   - Key: Authorization")
                print(f"   - Value: Bearer {access_token}")
                
                print("\n🧪 測試出勤查詢 API:")
                print("=" * 50)
                print("請求配置:")
                print(f"   - 方法: POST")
                print(f"   - URL: {base_url}/api/employee/attendance")
                print(f"   - Headers: Authorization: Bearer {access_token}")
                print(f"   - Body (JSON): {{'employee_id': '要查詢的員工ID'}}")
                
                # 保存到文件（可選）
                save_to_file = input("\n是否保存 Token 到文件? (y/N): ").strip().lower()
                if save_to_file == 'y':
                    save_token_to_file(access_token, user_info, tokens)
                
                return access_token
                
            else:
                print(f"\n❌ 登入失敗: {data.get('message')}")
                return None
                
        else:
            print(f"\n❌ HTTP 錯誤: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤信息: {error_data.get('message', '未知錯誤')}")
            except:
                print(f"響應內容: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 連接錯誤: 無法連接到伺服器")
        print("請確認:")
        print("   1. Flask 應用程式正在運行")
        print("   2. 端口 5001 沒有被佔用")
        print("   3. 防火牆設置允許連接")
        return None
        
    except requests.exceptions.Timeout:
        print("\n❌ 請求超時")
        return None
        
    except Exception as e:
        print(f"\n❌ 未知錯誤: {str(e)}")
        return None


def save_token_to_file(access_token, user_info, tokens):
    """保存 Token 到文件"""
    token_data = {
        "access_token": access_token,
        "user_info": user_info,
        "token_info": tokens,
        "postman_headers": {
            "Authorization": f"Bearer {access_token}"
        },
        "usage_instructions": {
            "postman_auth_type": "Bearer Token",
            "postman_token_value": access_token,
            "manual_header_key": "Authorization",
            "manual_header_value": f"Bearer {access_token}"
        }
    }
    
    filename = f"jwt_token_{user_info.get('username', 'unknown')}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Token 已保存到文件: {filename}")
        
    except Exception as e:
        print(f"❌ 保存文件失敗: {str(e)}")


def test_token_validity(access_token):
    """測試 Token 有效性"""
    print(f"\n🧪 測試 Token 有效性...")
    
    base_url = "http://localhost:5000"
    test_url = f"{base_url}/api/auth/me"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Token 有效，可以正常使用")
                return True
            else:
                print(f"❌ Token 驗證失敗: {data.get('message')}")
                return False
        else:
            print(f"❌ Token 驗證失敗，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Token 驗證錯誤: {str(e)}")
        return False


def main():
    """主程序"""
    access_token = get_jwt_token()
    
    if access_token:
        # 測試 Token 有效性
        test_token_validity(access_token)
        
        print(f"\n🎉 Token 獲取完成!")
        print(f"現在您可以在 Postman 中使用這個 Token 進行 API 測試了。")
    else:
        print(f"\n💔 Token 獲取失敗")
        print(f"請檢查:")
        print(f"   1. 用戶名和密碼是否正確")
        print(f"   2. AD 伺服器是否可訪問")
        print(f"   3. Flask 應用程式是否正常運行")


if __name__ == "__main__":
    main()