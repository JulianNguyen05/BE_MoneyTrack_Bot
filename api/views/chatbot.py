import datetime
import json
from decimal import Decimal

# Import thư viện Google AI
import google.generativeai as genai

# --- Django imports ---
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

# --- Models ---
from ..models.wallet import Wallet
from ..models.category import Category
from ..models.transaction import Transaction

# --- (C) CẤU HÌNH API KEY ---
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')  # Dùng mô hình Flash cho tốc độ
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
            wallets = list(Wallet.objects.filter(user=user).values('id', 'name'))
            categories = list(Category.objects.filter(user=user).values('id', 'name', 'type'))

            # --- (2) Xây dựng Câu lệnh (Prompt) cho AI ---
            prompt = self.build_prompt(message, wallets, categories)

            # --- (3) Gọi API Google AI ---
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
            response = model.generate_content(prompt, generation_config=generation_config)

            print("--- AI Raw Response ---")
            print(response.text)
            print("-----------------------")

            # --- (4) Xử lý JSON trả về ---
            ai_data = json.loads(response.text)
            action = ai_data.get("action")
            reply_message = ai_data.get("reply", "Tôi đã xử lý xong.")

            # --- (A) TẠO GIAO DỊCH ---
            if action == "create_transaction":
                data = ai_data.get("data")
                self.create_transaction_from_ai(user, data)
                return Response({"reply": reply_message})

            # --- (B) LỖI VALIDATION (PHẦN BỔ SUNG HOÀN THIỆN) ---
            # Xử lý KỊCH BẢN 4: Không tạo giao dịch và báo lỗi cho người dùng.
            elif action == "error_validation":
                return Response({"reply": reply_message}, status=status.HTTP_400_BAD_REQUEST)

            # --- (C) TRẢ LỜI CÂU HỎI ---
            elif action == "answer_question":
                query_type = ai_data.get("query_type")
                data = ai_data.get("data", {})
                final_reply = ""

                # --- 1. Tổng chi tháng này ---
                if query_type == "total_expense_current_month":
                    now = timezone.now()
                    total = Transaction.objects.filter(
                        user=user,
                        category__type='expense',
                        date__year=now.year,
                        date__month=now.month
                    ).aggregate(total_sum=Sum('amount'))['total_sum'] or Decimal(0)
                    final_reply = f"Tổng chi tháng này của bạn là {total:,.0f}đ."

                # --- 2. Số dư ví ---
                elif query_type == "get_wallet_balance":
                    wallet_id = data.get("wallet_id")
                    if wallet_id is None:
                        final_reply = "Xin lỗi, tôi không rõ bạn muốn hỏi số dư của ví nào."
                    else:
                        try:
                            wallet = Wallet.objects.get(id=wallet_id, user=user)
                            final_reply = f"Số dư trong ví '{wallet.name}' của bạn là {wallet.balance:,.0f}đ."
                        except Wallet.DoesNotExist:
                            final_reply = "Xin lỗi, tôi không tìm thấy ví đó trong tài khoản của bạn."

                # --- 3. Tổng chi của tháng cụ thể ---
                elif query_type == "total_expense_specific_month":
                    month = data.get("month")
                    if month is None:
                        final_reply = "Bạn vui lòng nói rõ tháng nào nhé (ví dụ: 'tháng 10')."
                    else:
                        now = timezone.now()
                        total = Transaction.objects.filter(
                            user=user,
                            category__type='expense',
                            date__year=now.year,  # (Giả định user hỏi năm hiện tại)
                            date__month=month
                        ).aggregate(total_sum=Sum('amount'))['total_sum'] or Decimal(0)
                        final_reply = f"Tổng chi tháng {month} của bạn là {total:,.0f}đ."

                # --- Không biết xử lý ---
                else:
                    final_reply = "Tôi đã nhận được câu hỏi, nhưng hiện tại tôi chưa được lập trình để tính điều này."

                return Response({"reply": final_reply})

            # --- (D) KHÔNG HIỂU ---
            else:
                return Response({"reply": ai_data.get("reply", "Xin lỗi, tôi chưa hiểu ý bạn.")})

        except Exception as e:
            print(f"--- AI API Error --- \n{e}\n------------------")
            return Response({"reply": f"Xin lỗi, Bot AI đang gặp lỗi: {str(e)}"})

    # ==========================================================
    # 🧠 Hàm "Dạy" AI cách hiểu câu hỏi và yêu cầu JSON
    # ==========================================================
    def build_prompt(self, message, wallets, categories):
        wallets_str = json.dumps(wallets)
        categories_str = json.dumps(categories)
        today_str = datetime.date.today().strftime('%Y-%m-%d')

        prompt = f"""
        Bạn là một trợ lý tài chính thông minh cho người dùng Việt Nam.
        Ngày hôm nay là: {today_str}.

        Kiến thức của bạn:
        1. Danh sách Ví của user: {wallets_str}
        2. Danh sách Danh mục của user: {categories_str}

        Nhiệm vụ:
        Phân tích tin nhắn và phản hồi bằng JSON duy nhất.

        ---
        KỊCH BẢN 1: TẠO GIAO DỊCH (Nếu có số tiền)
        Ví dụ user: "ăn trưa 50k bằng tiền mặt"
        => Trả về JSON:
        {{
          "action": "create_transaction",
          "reply": "✅ Đã lưu: Ăn trưa (-50.000đ) vào 'Ăn uống' từ 'Tiền mặt' nhé!",
          "data": {{
            "amount": 50000,
            "date": "{today_str}",
            "description": "Ăn trưa",
            "wallet_id": (id ví),
            "category_id": (id danh mục)
          }}
        }}

        ---
        KỊCH BẢN 2: HỎI ĐÁP (Nếu không có số tiền)
        Nhiệm vụ là nhận diện ý định và yêu cầu server truy vấn.

        Ví dụ 1: "tổng chi tháng này?"
        =>
        {{
          "action": "answer_question",
          "reply": "Bạn đợi chút, tôi đang tính tổng chi tháng này...",
          "query_type": "total_expense_current_month",
          "data": {{}}
        }}

        Ví dụ 2: "số dư ví tiền mặt?"
        =>
        {{
          "action": "answer_question",
          "reply": "Đang kiểm tra số dư 'Tiền mặt'...",
          "query_type": "get_wallet_balance",
          "data": {{"wallet_id": (id ví tiền mặt)}}
        }}

        Ví dụ 3: "tháng 10 tiêu bao nhiêu?"
        =>
        {{
          "action": "answer_question",
          "reply": "Đang kiểm tra chi tiêu tháng 10...",
          "query_type": "total_expense_specific_month",
          "data": {{"month": 10}}
        }}

        ---
        KỊCH BẢN 3: KHÔNG HIỂU
        {{
          "action": "unknown",
          "reply": "Xin lỗi, tôi chỉ là trợ lý tài chính. Tôi không hiểu câu hỏi này."
        }}

        ---
        KỊCH BẢN 4: LỖI VALIDATION (RẤT QUAN TRỌNG)
        Nếu user muốn TẠO GIAO DỊCH nhưng bạn KHÔNG tìm thấy 'wallet_id' hoặc 'category_id'
        khớp với Kiến thức hiện tại → TUYỆT ĐỐI KHÔNG tạo giao dịch.

        Ví dụ 1: User nói "ăn trưa 50k bằng ví 'thẻ'" (không có ví 'thẻ')
        {{
          "action": "error_validation",
          "reply": "Xin lỗi, tôi không tìm thấy ví nào tên 'thẻ'. Vui lòng kiểm tra lại."
        }}

        Ví dụ 2: User nói "chi 100k cho 'xe cộ'" (không có danh mục 'xe cộ')
        {{
          "action": "error_validation",
          "reply": "Xin lỗi, tôi không tìm thấy danh mục nào tên 'xe cộ'. Vui lòng kiểm tra lại."
        }}

        ---
        Bây giờ, xử lý tin nhắn người dùng:
        "{message}"
        """
        return prompt

    # ==========================================================
    # 🧾 Hàm tạo giao dịch thực tế
    # ==========================================================
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
            # Bạn có thể ném lỗi (raise e) để chatbot báo lỗi ngược lại cho user
            raise Exception(f"Lỗi server khi lưu giao dịch: {e}")