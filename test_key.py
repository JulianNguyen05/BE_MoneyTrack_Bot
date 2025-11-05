import google.generativeai as genai
import os

# !!! THAY KEY CỦA BẠN VÀO ĐÂY !!!
MY_API_KEY = "AIzaSyBnbrgg4z6gUH6-ALdYivejIF_GHI6Ksqg"

try:
    # Cấu hình key
    genai.configure(api_key=MY_API_KEY)

    # Tạo model (dùng 'gemini-pro' là đủ để test)
    model = genai.GenerativeModel('models/gemini-2.5-flash')

    print("Đang kết nối đến Gemini...")

    # Gửi một yêu cầu đơn giản
    response = model.generate_content("Hãy nói 'Xin chào' bằng tiếng Việt.")

    # In kết quả
    print("\n--- KẾT QUẢ ---")
    print(response.text)
    print("\n✅ [THÀNH CÔNG] API Key của bạn hoạt động bình thường!")

except Exception as e:
    print(f"\n❌ [THẤT BẠI] Đã xảy ra lỗi:")
    print(e)
    print("\n---")
    print(
        "Gợi ý: Kiểm tra lại API key. Nếu key đúng, có thể bạn chưa bật 'Generative AI API' trong Google Cloud Console hoặc chưa liên kết thanh toán (billing).")