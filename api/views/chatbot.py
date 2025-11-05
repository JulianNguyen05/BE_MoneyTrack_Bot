# Mở file: api/views/chatbot.py

# --- (A) IMPORT CÁC THƯ VIỆN CẦN THIẾT ---
import datetime
import json
from decimal import Decimal

# Import thư viện Google AI
import google.generativeai as genai

from django.conf import settings  # (1) Import settings
from django.db import transaction
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

# (B) IMPORT TỪ CÁC GÓI CỦA BẠN
try:
    from ..models import Transaction, Wallet, Category
except ImportError:
    from ..models.core import Wallet, Category
    from ..models.transactions import Transaction

# --- (C) CẤU HÌNH API KEY ---
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Dùng mô hình Flash cho tốc độ
    print("✅ (Chatbot) Kết nối Google Gemini API thành công!")
except Exception as e:
    print(f"❌ (Chatbot) Lỗi: Không thể kết nối Gemini API. Kiểm tra API Key. Lỗi: {e}")
    model = None


# ==========================================================
# 💬 API: Chatbot (Mới - Dùng Google AI)
# ==========================================================
class ChatbotView(APIView):
    """
    API xử lý ngôn ngữ tự nhiên (dùng Google Gemini API)
    để tạo giao dịch và hỏi đáp.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        message = request.data.get('message', '').strip()

        if not message:
            return Response({"reply": "Tin nhắn rỗng"}, status=status.HTTP_400_BAD_REQUEST)
        if model is None:
            return Response({"reply": "Lỗi: Bot AI chưa sẵn sàng. Vui lòng kiểm tra API Key phía server."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            # --- (1) Lấy "Kiến thức" (Context) của User ---
            # Lấy danh sách Ví và Danh mục để "mớm" cho AI
            wallets = list(Wallet.objects.filter(user=user).values('id', 'name'))
            categories = list(Category.objects.filter(user=user).values('id', 'name', 'type'))

            # --- (2) Xây dựng Câu lệnh (Prompt) cho AI ---
            prompt = self.build_prompt(message, wallets, categories)

            # --- (3) Gọi API Google AI ---
            # Yêu cầu AI trả lời bằng JSON
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
            response = model.generate_content(prompt, generation_config=generation_config)

            # (Debug: In ra câu trả lời thô từ AI)
            print("--- AI Raw Response ---")
            print(response.text)
            print("-----------------------")

            # --- (4) Xử lý Câu trả lời JSON của AI ---
            ai_data = json.loads(response.text)
            action = ai_data.get("action")
            reply_message = ai_data.get("reply", "Tôi đã xử lý xong.")

            # (A) Nếu AI nói "Tạo giao dịch"
            if action == "create_transaction":
                data = ai_data.get("data")
                # Tạo giao dịch (dùng hàm phụ)
                self.create_transaction_from_ai(user, data)
                return Response({"reply": reply_message})

            # (B) Nếu AI nói "Trả lời câu hỏi" (ví dụ: hỏi số dư)
            elif action == "answer_question":
                return Response({"reply": reply_message})

            # (C) Nếu AI không hiểu
            else:
                return Response({"reply": ai_data.get("reply", "Xin lỗi, tôi chưa hiểu ý bạn.")})

        except Exception as e:
            # (Debug: In lỗi nếu gọi API thất bại)
            print(f"--- AI API Error --- \n{e}\n------------------")
            return Response({"reply": f"Xin lỗi, Bot AI đang gặp lỗi: {str(e)}"})

    # --- (Hàm phụ 1): Xây dựng câu lệnh (Prompt) ---
    def build_prompt(self, message, wallets, categories):
        # Chuyển danh sách (Python list) thành chuỗi (string)
        wallets_str = json.dumps(wallets)
        categories_str = json.dumps(categories)
        today_str = datetime.date.today().strftime('%Y-%m-%d')

        # Đây là "bộ não" của bot. Chúng ta "dạy" AI cách hành xử.
        prompt = f"""
        Bạn là một trợ lý tài chính thông minh cho người dùng Việt Nam.
        Ngày hôm nay là: {today_str}.

        Kiến thức của bạn:
        1. Danh sách Ví của user: {wallets_str}
        2. Danh sách Danh mục của user: {categories_str}

        Nhiệm vụ của bạn:
        Đọc tin nhắn của user và phân tích xem họ muốn (1) Tạo giao dịch hay (2) Hỏi đáp.
        Sau đó, trả lời BẮT BUỘC bằng định dạng JSON.

        ---
        KỊCH BẢN 1: TẠO GIAO DỊCH (Nếu user nhập số tiền)
        Ví dụ user: "ăn trưa 50k bằng tiền mặt"
        1. Phân tích:
           - "50k" -> amount: 50000 (Luôn là số).
           - "tiền mặt" -> tìm trong "Danh sách Ví" -> wallet_id: (id của ví 'tiền mặt').
           - "ăn trưa" -> tìm trong "Danh sách Danh mục" -> category_id: (id của danh mục 'Ăn uống').
           - "hôm qua" -> date: (ngày hôm qua, YYYY-MM-DD). Nếu không nói gì, dùng ngày hôm nay.
           - "ăn trưa" -> description: "Ăn trưa".
        2. Trả lời JSON:
           {{
             "action": "create_transaction",
             "reply": "✅ Đã lưu: Ăn trưa (-50.000đ) vào 'Ăn uống' từ 'Tiền mặt' nhé!",
             "data": {{
               "amount": 50000,
               "date": "2025-11-04",
               "description": "Ăn trưa",
               "wallet_id": (id của ví),
               "category_id": (id của danh mục)
             }}
           }}

        KỊCH BẢN 2: HỎI ĐÁP (Nếu user không nhập số tiền)
        Ví dụ user: "tổng chi tháng này?"
        1. Phân tích: User muốn biết tổng chi tiêu.
        2. Trả lời JSON:
           {{
             "action": "answer_question",
             "reply": "Bạn đợi chút, tôi đang tính tổng chi tháng này..."
           }}
        (Lưu ý: Bạn KHÔNG cần tự tính toán. Server sẽ tự tính sau. Chỉ cần nhận diện ý định.)

        KỊCH BẢN 3: KHÔNG HIỂU
        Ví dụ user: "con mèo màu gì?"
        1. Phân tích: Không liên quan đến tài chính.
        2. Trả lời JSON:
           {{
             "action": "unknown",
             "reply": "Xin lỗi, tôi chỉ là trợ lý tài chính. Tôi không biết về chủ đề này."
           }}
        ---

        BÂY GIỜ, HÃY XỬ LÝ TIN NHẮN SAU:
        "{message}"
        """
        return prompt

    # --- (Hàm phụ 2): Tạo Giao dịch từ dữ liệu AI ---
    def create_transaction_from_ai(self, user, data):
        try:
            with transaction.atomic():
                wallet = Wallet.objects.get(id=data['wallet_id'], user=user)
                category = Category.objects.get(id=data['category_id'], user=user)
                amount = Decimal(data['amount'])
                date = data.get('date', datetime.date.today())

                Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    category=category,
                    amount=amount,
                    date=date,
                    description=data.get('description', category.name).capitalize()
                )

                # Cập nhật số dư ví
                if category.type == 'income':
                    wallet.balance += amount
                else:
                    wallet.balance -= amount
                wallet.save(update_fields=['balance'])
        except Exception as e:
            print(f"Lỗi khi tạo Giao dịch từ AI: {e}")
            # (Bạn có thể ném lỗi (raise e) để gửi về cho user nếu muốn)