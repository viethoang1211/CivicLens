"""Generate sample PDF documents for Quick Scan demo testing.

Creates realistic Vietnamese government document PDFs using DejaVu Sans
font for proper Vietnamese diacritic rendering.

Usage:
    pip install reportlab
    python generate_samples.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Register Vietnamese-capable fonts
pdfmetrics.registerFont(TTFont("VN", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("VN-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))


def _draw_quoc_hieu(c, y):
    """Draw Vietnamese national title header."""
    c.setFont("VN-Bold", 11)
    c.drawCentredString(A4[0] / 2, y, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    c.setFont("VN-Bold", 10)
    c.drawCentredString(A4[0] / 2, y - 16, "Độc lập - Tự do - Hạnh phúc")
    c.line(A4[0] / 2 - 60, y - 20, A4[0] / 2 + 60, y - 20)
    return y - 40


def _field_line(c, x, y, label, value, width=460):
    """Draw a labeled field with dotted underline."""
    c.setFont("VN", 10)
    c.drawString(x, y, f"{label}: ")
    label_width = c.stringWidth(f"{label}: ", "VN", 10)
    c.setFont("VN-Bold", 10)
    c.drawString(x + label_width, y, value)
    c.setDash(1, 2)
    end_x = x + label_width + c.stringWidth(value, "VN-Bold", 10) + 5
    if end_x < x + width:
        c.line(end_x, y - 2, x + width, y - 2)
    c.setDash()
    return y - 22


# 1. TỜ KHAI XÁC NHẬN TÌNH TRẠNG HÔN NHÂN
def generate_marital_status_form():
    filepath = os.path.join(OUTPUT_DIR, "01_to_khai_hon_nhan.pdf")
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4

    y = _draw_quoc_hieu(c, h - 40)

    y -= 10
    c.setFont("VN-Bold", 14)
    c.drawCentredString(w / 2, y, "TỜ KHAI CẤP GIẤY XÁC NHẬN TÌNH TRẠNG HÔN NHÂN")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(60, y, "Kính gửi: ỦY BAN NHÂN DÂN TP.HCM")
    y -= 30

    y = _field_line(c, 60, y, "Họ, chữ đệm, tên người yêu cầu", "TRƯƠNG THỊ NGỌC LAN")
    y = _field_line(c, 60, y, "Ngày, tháng, năm sinh", "01/04/1990")
    y = _field_line(c, 60, y, "Nơi cư trú", "333 Nguyễn Thiện Thuật, P. Bàn Cờ, TP.HCM")
    y = _field_line(c, 60, y, "Giấy tờ tùy thân: CCCD", "079101010001")
    y -= 10

    y = _field_line(c, 60, y, "Quan hệ với người được cấp Giấy xác nhận", "Vợ")
    y -= 10

    c.setFont("VN", 10)
    c.drawString(60, y, "Đề nghị cấp Giấy xác nhận tình trạng hôn nhân cho người có tên dưới đây:")
    y -= 25

    y = _field_line(c, 60, y, "Họ, chữ đệm, tên", "NGUYỄN VĂN ANH")
    y = _field_line(c, 60, y, "Ngày, tháng, năm sinh", "02/04/1990")
    y = _field_line(c, 60, y, "Giới tính", "Nam")
    y = _field_line(c, 60, y, "Dân tộc", "Kinh")
    y = _field_line(c, 60, y, "Quốc tịch", "Việt Nam")
    y = _field_line(c, 60, y, "Nơi cư trú", "42 Hòa Hưng, P. Vườn Lài")
    y = _field_line(c, 60, y, "Giấy tờ tùy thân: CCCD", "079201010082")
    y -= 10

    y = _field_line(c, 60, y, "Tình trạng hôn nhân", "Chưa đăng ký kết hôn")
    y = _field_line(c, 60, y, "Mục đích sử dụng", "Kết hôn")
    y -= 15

    c.setFont("VN", 9)
    c.drawString(60, y, "Tôi cam đoan những nội dung khai trên đây là đúng sự thật và chịu trách nhiệm")
    y -= 14
    c.drawString(60, y, "trước pháp luật về cam đoan của mình.")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(300, y, "Làm tại: TP.HCM, ngày 01/01/2026")
    y -= 20
    c.drawCentredString(400, y, "Người yêu cầu")
    c.setFont("VN", 8)
    y -= 12
    c.drawCentredString(400, y, "(Ký, ghi rõ họ, chữ đệm, tên)")
    y -= 30
    c.setFont("VN-Bold", 11)
    c.drawCentredString(400, y, "Trương Thị Ngọc Lan")

    c.save()
    print(f"  ✅ {filepath}")


# 2. TỜ KHAI ĐĂNG KÝ KHAI SINH (matches official BTP form)
def generate_birth_reg_form():
    filepath = os.path.join(OUTPUT_DIR, "02_to_khai_khai_sinh.pdf")
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4

    y = _draw_quoc_hieu(c, h - 40)
    y -= 10
    c.setFont("VN-Bold", 14)
    c.drawCentredString(w / 2, y, "Tờ Khai Đăng Ký Khai Sinh")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(60, y, "Kính gửi: Ủy ban nhân dân xã Háng Lia, huyện Điện Biên Đông, tỉnh Điện Biên")
    y -= 25

    # --- Người yêu cầu ---
    y = _field_line(c, 60, y, "Họ, chữ đệm, tên người yêu cầu", "GIÀNG THỊ PÀ")
    # Two-line field for long CCCD info
    c.setFont("VN", 10)
    c.drawString(60, y, "Giấy tờ tùy thân: ")
    c.setFont("VN-Bold", 10)
    c.drawString(60 + c.stringWidth("Giấy tờ tùy thân: ", "VN", 10), y, "Căn cước công dân số 011167000556")
    y -= 16
    c.setFont("VN-Bold", 10)
    c.drawString(76, y, "do Công an tỉnh Điện Biên cấp ngày 15/06/2022")
    c.setDash(1, 2)
    end_x = 76 + c.stringWidth("do Công an tỉnh Điện Biên cấp ngày 15/06/2022", "VN-Bold", 10) + 5
    c.line(end_x, y - 2, 520, y - 2)
    c.setDash()
    y -= 22
    y = _field_line(c, 60, y, "Nơi cư trú",
                    "Bản Huổi Va A, xã Háng Lia, huyện Điện Biên Đông, tỉnh Điện Biên")
    y = _field_line(c, 60, y, "Quan hệ với người được khai sinh", "mẹ")
    y -= 10

    c.setFont("VN", 10)
    c.drawString(60, y, "Đề nghị cơ quan đăng ký khai sinh cho người dưới đây:")
    y -= 22

    # --- Thông tin trẻ ---
    y = _field_line(c, 60, y, "Họ, chữ đệm, tên", "SÙNG THỊ MỶ")
    # Two-line field for date + spelled-out date
    c.setFont("VN", 10)
    c.drawString(60, y, "Ngày, tháng, năm sinh: ")
    c.setFont("VN-Bold", 10)
    c.drawString(60 + c.stringWidth("Ngày, tháng, năm sinh: ", "VN", 10), y, "10/03/2026")
    c.setFont("VN", 10)
    c.drawString(60 + c.stringWidth("Ngày, tháng, năm sinh: ", "VN", 10) + c.stringWidth("10/03/2026", "VN-Bold", 10) + 5, y, "  ghi bằng chữ:")
    y -= 16
    c.setFont("VN-Bold", 10)
    c.drawString(76, y, "Ngày mười, Tháng ba, Năm hai nghìn không trăm hai mươi sáu.")
    c.setDash(1, 2)
    end_x = 76 + c.stringWidth("Ngày mười, Tháng ba, Năm hai nghìn không trăm hai mươi sáu.", "VN-Bold", 10) + 5
    if end_x < 520:
        c.line(end_x, y - 2, 520, y - 2)
    c.setDash()
    y -= 22
    y = _field_line(c, 60, y, "Nơi sinh", "Trạm Y tế xã Háng Lia, huyện Điện Biên Đông, tỉnh Điện Biên")
    c.setFont("VN", 10)
    c.drawString(60, y, "Giới tính: ")
    c.setFont("VN-Bold", 10)
    c.drawString(120, y, "Nữ")
    c.setFont("VN", 10)
    c.drawString(200, y, "Dân tộc: ")
    c.setFont("VN-Bold", 10)
    c.drawString(255, y, "H'Mông")
    c.setFont("VN", 10)
    c.drawString(350, y, "Quốc tịch: ")
    c.setFont("VN-Bold", 10)
    c.drawString(415, y, "Việt Nam")
    y -= 22
    y = _field_line(c, 60, y, "Quê quán", "xã Háng Lia, huyện Điện Biên Đông, tỉnh Điện Biên")
    y -= 8

    # --- Cha ---
    y = _field_line(c, 60, y, "Họ, chữ đệm, tên cha", "SÙNG A TỦA")
    c.setFont("VN", 10)
    c.drawString(60, y, "Năm sinh: ")
    c.setFont("VN-Bold", 10)
    c.drawString(120, y, "1965")
    c.setFont("VN", 10)
    c.drawString(200, y, "Dân tộc: ")
    c.setFont("VN-Bold", 10)
    c.drawString(255, y, "H'Mông")
    c.setFont("VN", 10)
    c.drawString(350, y, "Quốc tịch: ")
    c.setFont("VN-Bold", 10)
    c.drawString(415, y, "Việt Nam")
    y -= 22
    y = _field_line(c, 60, y, "Nơi cư trú",
                    "Bản Huổi Va A, xã Háng Lia, huyện Điện Biên Đông, tỉnh Điện Biên")
    y -= 8

    # --- Mẹ ---
    y = _field_line(c, 60, y, "Họ, chữ đệm, tên mẹ", "GIÀNG THỊ PÀ")
    c.setFont("VN", 10)
    c.drawString(60, y, "Năm sinh: ")
    c.setFont("VN-Bold", 10)
    c.drawString(120, y, "1967")
    c.setFont("VN", 10)
    c.drawString(200, y, "Dân tộc: ")
    c.setFont("VN-Bold", 10)
    c.drawString(255, y, "H'Mông")
    c.setFont("VN", 10)
    c.drawString(350, y, "Quốc tịch: ")
    c.setFont("VN-Bold", 10)
    c.drawString(415, y, "Việt Nam")
    y -= 22
    y = _field_line(c, 60, y, "Nơi cư trú",
                    "Bản Huổi Va A, xã Háng Lia, huyện Điện Biên Đông, tỉnh Điện Biên")
    y -= 12

    # --- Cam đoan ---
    c.setFont("VN", 9)
    c.drawString(60, y, "Tôi cam đoan nội dung để nghị đăng ký khai sinh trên đây là đúng sự thật, được sự thỏa")
    y -= 14
    c.drawString(60, y, "thuận nhất trí của các bên liên quan theo quy định pháp luật.")
    y -= 14
    c.drawString(60, y, "Tôi chịu hoàn toàn trách nhiệm trước pháp luật về nội dung cam đoan của mình.")
    y -= 25

    c.setFont("VN", 10)
    c.drawString(250, y, "Làm tại: Háng Lia, ngày 15 tháng 03 năm 2026")
    y -= 20
    c.drawCentredString(400, y, "Người yêu cầu")
    c.setFont("VN", 8)
    y -= 12
    c.drawCentredString(400, y, "(Ký, ghi rõ họ, chữ đệm, tên)")
    y -= 30
    c.setFont("VN-Bold", 11)
    c.drawCentredString(400, y, "Giàng Thị Pà")
    y -= 30

    # --- Đề nghị bản sao ---
    c.setFont("VN", 9)
    c.drawString(60, y, "Đề nghị cấp bản sao:  ☑ Có      ☐ Không          Số lượng: 02 bản")

    c.save()
    print(f"  ✅ {filepath}")


# 3. GIẤY ĐỀ NGHỊ ĐĂNG KÝ HỘ KINH DOANH
def generate_biz_reg_form():
    filepath = os.path.join(OUTPUT_DIR, "03_dang_ky_ho_kinh_doanh.pdf")
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4

    y = _draw_quoc_hieu(c, h - 40)
    y -= 10
    c.setFont("VN-Bold", 13)
    c.drawCentredString(w / 2, y, "GIẤY ĐỀ NGHỊ ĐĂNG KÝ HỘ KINH DOANH")
    c.setFont("VN", 9)
    y -= 16
    c.drawCentredString(w / 2, y, "(Phụ lục III-1, Thông tư 01/2021/TT-BKHĐT)")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(60, y, "Kính gửi: Phòng Tài chính - Kế hoạch UBND Quận 1, TP.HCM")
    y -= 30

    y = _field_line(c, 60, y, "Tên hộ kinh doanh", "HỘ KINH DOANH GIÀNG THỊ PÀ")
    y = _field_line(c, 60, y, "Địa điểm kinh doanh", "45 Nguyễn Huệ, P. Bến Nghé, Q.1, TP.HCM")
    y = _field_line(c, 60, y, "Ngành nghề kinh doanh", "Bán lẻ hàng thủ công mỹ nghệ dân tộc")
    y = _field_line(c, 60, y, "Mã ngành VSIC", "4773")
    y = _field_line(c, 60, y, "Vốn kinh doanh", "200.000.000 đồng (Hai trăm triệu đồng)")
    y = _field_line(c, 60, y, "Số lượng lao động", "3")
    y -= 15

    c.setFont("VN-Bold", 11)
    c.drawString(60, y, "THÔNG TIN CHỦ HỘ KINH DOANH")
    y -= 22

    y = _field_line(c, 60, y, "Họ và tên", "GIÀNG THỊ PÀ")
    y = _field_line(c, 60, y, "Giới tính", "Nữ")
    y = _field_line(c, 60, y, "Ngày sinh", "01/01/1967")
    y = _field_line(c, 60, y, "Dân tộc", "H'Mông")
    y = _field_line(c, 60, y, "Số CCCD", "011167000556")
    y = _field_line(c, 60, y, "Ngày cấp", "15/06/2022")
    y = _field_line(c, 60, y, "Nơi cư trú", "Bản Huổi Va A, Háng Lia, Điện Biên Đông, Điện Biên")
    y = _field_line(c, 60, y, "Điện thoại", "0987654321")
    y -= 20

    c.setFont("VN", 9)
    c.drawString(60, y, "Tôi cam kết chịu trách nhiệm trước pháp luật về tính hợp pháp, chính xác,")
    y -= 14
    c.drawString(60, y, "trung thực của nội dung đăng ký trên.")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(300, y, "TP.HCM, ngày 16 tháng 04 năm 2026")
    y -= 20
    c.drawCentredString(400, y, "Chủ hộ kinh doanh")
    y -= 30
    c.setFont("VN-Bold", 11)
    c.drawCentredString(400, y, "Giàng Thị Pà")

    c.save()
    print(f"  ✅ {filepath}")


# 4. ĐƠN KHIẾU NẠI
def generate_complaint():
    filepath = os.path.join(OUTPUT_DIR, "04_don_khieu_nai.pdf")
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4

    y = _draw_quoc_hieu(c, h - 40)
    y -= 10
    c.setFont("VN-Bold", 14)
    c.drawCentredString(w / 2, y, "ĐƠN KHIẾU NẠI")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(60, y, "Kính gửi: Chủ tịch UBND Quận 3, TP.HCM")
    y -= 30

    y = _field_line(c, 60, y, "Họ và tên người khiếu nại", "TRẦN VĂN HÙNG")
    y = _field_line(c, 60, y, "Số CCCD", "012345678903")
    y = _field_line(c, 60, y, "Ngày sinh", "15/06/1985")
    y = _field_line(c, 60, y, "Nơi cư trú", "78 Trần Quốc Toản, P.8, Q.3, TP.HCM")
    y = _field_line(c, 60, y, "Điện thoại", "0923456789")
    y -= 15

    c.setFont("VN-Bold", 11)
    c.drawString(60, y, "NỘI DUNG KHIẾU NẠI")
    y -= 22

    c.setFont("VN", 10)
    lines = [
        "Tôi khiếu nại về việc UBND Phường 8 thu hồi quyền sử dụng đất tại",
        "địa chỉ 78 Trần Quốc Toản, P.8, Q.3, TP.HCM theo Quyết định số",
        "123/QĐ-UBND ngày 01/03/2026 mà không thông báo trước 30 ngày",
        "theo quy định.",
        "",
        "Quyết định trên vi phạm Điều 67 Luật Đất đai 2024 về trình tự thu",
        "hồi đất. Tôi đề nghị hủy bỏ Quyết định số 123/QĐ-UBND và thực",
        "hiện đúng trình tự thông báo theo quy định pháp luật.",
    ]
    for line in lines:
        c.drawString(60, y, line)
        y -= 16

    y -= 20
    c.setFont("VN", 10)
    c.drawString(300, y, "TP.HCM, ngày 16 tháng 04 năm 2026")
    y -= 20
    c.drawCentredString(400, y, "Người khiếu nại")
    c.setFont("VN", 8)
    y -= 12
    c.drawCentredString(400, y, "(Ký, ghi rõ họ tên)")
    y -= 30
    c.setFont("VN-Bold", 11)
    c.drawCentredString(400, y, "Trần Văn Hùng")

    c.save()
    print(f"  ✅ {filepath}")


# 5. GIẤY ĐỀ NGHỊ ĐĂNG KÝ DOANH NGHIỆP
def generate_company_reg_form():
    filepath = os.path.join(OUTPUT_DIR, "05_dang_ky_doanh_nghiep.pdf")
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4

    y = _draw_quoc_hieu(c, h - 40)
    y -= 10
    c.setFont("VN-Bold", 13)
    c.drawCentredString(w / 2, y, "GIẤY ĐỀ NGHỊ ĐĂNG KÝ DOANH NGHIỆP")
    c.setFont("VN", 9)
    y -= 16
    c.drawCentredString(w / 2, y, "(Phụ lục I-1, Thông tư 01/2021/TT-BKHĐT)")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(60, y, "Kính gửi: Phòng Đăng ký kinh doanh, Sở KHĐT TP.HCM")
    y -= 30

    y = _field_line(c, 60, y, "Tên doanh nghiệp", "CÔNG TY TNHH THƯƠNG MẠI ĐIỆN BIÊN XANH")
    y = _field_line(c, 60, y, "Tên viết tắt", "ĐIỆN BIÊN XANH CO., LTD")
    y = _field_line(c, 60, y, "Loại hình", "Công ty TNHH một thành viên")
    y = _field_line(c, 60, y, "Địa chỉ trụ sở chính", "45 Nguyễn Huệ, P. Bến Nghé, Q.1, TP.HCM")
    y = _field_line(c, 60, y, "Ngành nghề kinh doanh chính", "Bán buôn nông, lâm sản (4620)")
    y = _field_line(c, 60, y, "Vốn điều lệ", "500.000.000 đồng (Năm trăm triệu đồng)")
    y -= 15

    c.setFont("VN-Bold", 11)
    c.drawString(60, y, "THÔNG TIN NGƯỜI ĐẠI DIỆN THEO PHÁP LUẬT")
    y -= 22

    y = _field_line(c, 60, y, "Họ và tên", "GIÀNG THỊ PÀ")
    y = _field_line(c, 60, y, "Chức danh", "Giám đốc")
    y = _field_line(c, 60, y, "Giới tính", "Nữ")
    y = _field_line(c, 60, y, "Ngày sinh", "01/01/1967")
    y = _field_line(c, 60, y, "Dân tộc", "H'Mông")
    y = _field_line(c, 60, y, "Quốc tịch", "Việt Nam")
    y = _field_line(c, 60, y, "Số CCCD", "011167000556")
    y = _field_line(c, 60, y, "Ngày cấp", "15/06/2022")
    y = _field_line(c, 60, y, "Nơi thường trú", "Bản Huổi Va A, Háng Lia, Điện Biên Đông, Điện Biên")
    y = _field_line(c, 60, y, "Điện thoại", "0987654321")
    y -= 20

    c.setFont("VN", 9)
    c.drawString(60, y, "Tôi cam kết chịu trách nhiệm trước pháp luật về tính hợp pháp, chính xác,")
    y -= 14
    c.drawString(60, y, "trung thực của nội dung đăng ký trên.")
    y -= 30

    c.setFont("VN", 10)
    c.drawString(300, y, "TP.HCM, ngày 16 tháng 04 năm 2026")
    y -= 20
    c.drawCentredString(400, y, "Người đại diện theo pháp luật")
    y -= 30
    c.setFont("VN-Bold", 11)
    c.drawCentredString(400, y, "Giàng Thị Pà")

    c.save()
    print(f"  ✅ {filepath}")


if __name__ == "__main__":
    # Clean up old files
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".pdf"):
            os.remove(os.path.join(OUTPUT_DIR, f))

    print("Generating sample PDF documents for Quick Scan demo...\n")
    print("   (Using DejaVu Sans font for Vietnamese diacritics)\n")
    generate_marital_status_form()
    generate_birth_reg_form()
    generate_biz_reg_form()
    generate_complaint()
    generate_company_reg_form()
    print(f"\nAll PDFs generated in: {OUTPUT_DIR}")
    print("\nLuu y: Khong can PDF cho CCCD -- dung truc tiep anh chup CCCD that.")
    print("   In cac file PDF nay ra A4 hoac hien thi tren man hinh de test Quick Scan.")
