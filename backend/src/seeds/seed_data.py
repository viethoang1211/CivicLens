"""Seed database with comprehensive Vietnamese administrative procedure data.

Legal references:
- Luật Hộ tịch 2014 (Civil Status Law), Nghị định 123/2015/NĐ-CP, Thông tư 04/2020/TT-BTP
- Luật Cư trú 2020 (Residence Law), Nghị định 62/2021/NĐ-CP
- Luật Doanh nghiệp 2020 (Enterprise Law), Nghị định 01/2021/NĐ-CP, Thông tư 01/2021/TT-BKHĐT
- Luật Hôn nhân và Gia đình 2014
- Luật Khiếu nại 2011
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import async_session_factory
from src.models.case_type import CaseType, CaseTypeRoutingStep
from src.models.citizen import Citizen
from src.models.department import Department
from src.models.document_requirement import DocumentRequirementGroup, DocumentRequirementSlot
from src.models.document_type import DocumentType
from src.models.routing_rule import RoutingRule
from src.models.staff_member import StaffMember
from src.security.auth import hash_password

# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    {"name": "Tiếp nhận (Reception)", "code": "RECEPTION", "min_clearance_level": 0},
    {"name": "Phòng Hành chính (Administrative)", "code": "ADMIN", "min_clearance_level": 0},
    {"name": "Phòng Tư pháp (Judicial)", "code": "JUDICIAL", "min_clearance_level": 1},
    {"name": "Phòng Tài chính - Kế hoạch (Finance & Planning)", "code": "FINANCE", "min_clearance_level": 0},
    {"name": "Phòng Nội vụ (Internal Affairs)", "code": "INTERNAL", "min_clearance_level": 2},
    {"name": "Lãnh đạo (Leadership)", "code": "LEADERSHIP", "min_clearance_level": 2},
    {"name": "Công an (Police - Residence)", "code": "POLICE", "min_clearance_level": 1},
]


# ---------------------------------------------------------------------------
# Document Types — comprehensive set for Vietnamese administrative procedures
# ---------------------------------------------------------------------------

DOCUMENT_TYPES = [
    # ── Identity Documents ──
    {
        "name": "Căn cước công dân / CMND",
        "code": "ID_CCCD",
        "description": "Căn cước công dân (CCCD) gắn chip hoặc Chứng minh nhân dân (CMND). "
                       "CCCD có 12 số, CMND có 9 hoặc 12 số. "
                       "Căn cứ: Luật Căn cước 2023 (có hiệu lực 01/07/2024).",
        "retention_years": 0,
        "retention_permanent": True,
        "template_schema": {
            "type": "object",
            "properties": {
                "so_cccd": {"type": "string", "title": "Số CCCD/CMND", "pattern": "^[0-9]{9,12}$"},
                "ho_ten": {"type": "string", "title": "Họ và tên"},
                "ngay_sinh": {"type": "string", "title": "Ngày sinh", "format": "date"},
                "gioi_tinh": {"type": "string", "title": "Giới tính", "enum": ["Nam", "Nữ"]},
                "quoc_tich": {"type": "string", "title": "Quốc tịch"},
                "que_quan": {"type": "string", "title": "Quê quán"},
                "noi_thuong_tru": {"type": "string", "title": "Nơi thường trú"},
                "ngay_cap": {"type": "string", "title": "Ngày cấp", "format": "date"},
                "noi_cap": {"type": "string", "title": "Nơi cấp"},
                "ngay_het_han": {"type": "string", "title": "Có giá trị đến", "format": "date"},
            },
            "required": ["so_cccd", "ho_ten", "ngay_sinh"],
        },
        "classification_prompt": (
            "Đây là GIẤY Tờ TÙY THÂN do cơ quan công an cấp — "
            "Căn cước công dân (CCCD) hoặc Chứng minh nhân dân (CMND) của Việt Nam. "
            "Có chip NFC (CCCD mới), quốc huy Việt Nam. "
            "Đặc điểm nhận dạng: thẻ nhựa cứng có ảnh chân dung, "
            "hiển thị số CCCD 12 chữ số hoặc CMND 9/12 chữ số, "
            "thông tin: họ tên, ngày sinh, giới tính, quốc tịch, quê quán, nơi thường trú. "
            "Mặt sau có đặc điểm nhận dạng và ngày cấp."
        ),
        "route": ["RECEPTION"],
    },
    {
        "name": "Hộ chiếu Việt Nam",
        "code": "PASSPORT_VN",
        "description": "Hộ chiếu phổ thông Việt Nam. Căn cứ: Luật Xuất cảnh, nhập cảnh 2019.",
        "retention_years": 0,
        "retention_permanent": True,
        "template_schema": {
            "type": "object",
            "properties": {
                "so_ho_chieu": {"type": "string", "title": "Số hộ chiếu"},
                "ho_ten": {"type": "string", "title": "Họ và tên"},
                "ngay_sinh": {"type": "string", "title": "Ngày sinh", "format": "date"},
                "gioi_tinh": {"type": "string", "title": "Giới tính"},
                "quoc_tich": {"type": "string", "title": "Quốc tịch"},
                "noi_sinh": {"type": "string", "title": "Nơi sinh"},
                "ngay_cap": {"type": "string", "title": "Ngày cấp", "format": "date"},
                "ngay_het_han": {"type": "string", "title": "Ngày hết hạn", "format": "date"},
                "noi_cap": {"type": "string", "title": "Cơ quan cấp"},
            },
            "required": ["so_ho_chieu", "ho_ten", "ngay_sinh"],
        },
        "classification_prompt": (
            "Đây là GIẤY Tờ TÙY THÂN do cơ quan xuất nhập cảnh cấp — "
            "Hộ chiếu Việt Nam (Vietnam Passport). "
            "Đặc điểm: bìa xanh đậm hoặc xanh tím, quốc huy Việt Nam, "
            "chữ 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM' và 'HỘ CHIẾU / PASSPORT'. "
            "Bên trong có ảnh chân dung, thông tin song ngữ Việt-Anh, mã MRZ ở trang thông tin."
        ),
        "route": ["RECEPTION"],
    },

    # ── Civil Status Documents (Hộ tịch) ──
    {
        "name": "Tờ khai đăng ký khai sinh",
        "code": "BIRTH_REG_FORM",
        "description": "Tờ khai đăng ký khai sinh theo mẫu ban hành kèm Thông tư 04/2020/TT-BTP. "
                       "Căn cứ: Luật Hộ tịch 2014, Điều 16; Nghị định 123/2015/NĐ-CP, Điều 9.",
        "retention_years": 75,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ho_ten_tre": {"type": "string", "title": "Họ và tên trẻ"},
                "gioi_tinh": {"type": "string", "title": "Giới tính", "enum": ["Nam", "Nữ"]},
                "ngay_sinh": {"type": "string", "title": "Ngày, tháng, năm sinh", "format": "date"},
                "ngay_sinh_bang_chu": {"type": "string", "title": "Ngày sinh bằng chữ"},
                "noi_sinh": {"type": "string", "title": "Nơi sinh (cơ sở y tế / địa chỉ)"},
                "dan_toc": {"type": "string", "title": "Dân tộc"},
                "quoc_tich": {"type": "string", "title": "Quốc tịch"},
                "que_quan": {"type": "string", "title": "Quê quán"},
                "ho_ten_cha": {"type": "string", "title": "Họ và tên cha"},
                "nam_sinh_cha": {"type": "string", "title": "Năm sinh cha"},
                "dan_toc_cha": {"type": "string", "title": "Dân tộc cha"},
                "quoc_tich_cha": {"type": "string", "title": "Quốc tịch cha"},
                "cu_tru_cha": {"type": "string", "title": "Nơi cư trú cha"},
                "cccd_cha": {"type": "string", "title": "Số CCCD cha"},
                "ho_ten_me": {"type": "string", "title": "Họ và tên mẹ"},
                "nam_sinh_me": {"type": "string", "title": "Năm sinh mẹ"},
                "dan_toc_me": {"type": "string", "title": "Dân tộc mẹ"},
                "quoc_tich_me": {"type": "string", "title": "Quốc tịch mẹ"},
                "cu_tru_me": {"type": "string", "title": "Nơi cư trú mẹ"},
                "cccd_me": {"type": "string", "title": "Số CCCD mẹ"},
                "nguoi_di_dang_ky": {"type": "string", "title": "Người đi đăng ký"},
                "quan_he_voi_tre": {"type": "string", "title": "Quan hệ với trẻ"},
            },
            "required": ["ho_ten_tre", "gioi_tinh", "ngay_sinh", "noi_sinh", "ho_ten_me"],
        },
        "classification_prompt": (
            "Đây là TỜ KHAI / mẫu đơn do công dân tự điền — Tờ khai đăng ký khai sinh theo mẫu của Bộ Tư pháp. "
            "Thường in trắng đen trên giấy A4, có các dòng chấm/ô trống để điền thông tin. "
            "Mẫu theo Thông tư 04/2020/TT-BTP. "
            "Đặc điểm: có tiêu đề 'TỜ KHAI ĐĂNG KÝ KHAI SINH', "
            "quốc hiệu 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', "
            "các trường: họ tên trẻ, ngày sinh, giới tính, nơi sinh, dân tộc, quốc tịch, "
            "thông tin cha (họ tên, năm sinh, dân tộc, quốc tịch, cư trú), "
            "thông tin mẹ (họ tên, năm sinh, dân tộc, quốc tịch, cư trú), "
            "người đi đăng ký và quan hệ với trẻ. "
            "KHÔNG có dấu đỏ của cơ quan nhà nước (khác với Giấy khai sinh do UBND cấp)."
        ),
        "route": ["RECEPTION", "JUDICIAL"],
    },
    {
        "name": "Giấy chứng sinh",
        "code": "BIRTH_CERTIFICATE_MEDICAL",
        "description": "Giấy chứng sinh do cơ sở y tế cấp cho trẻ sơ sinh. "
                       "Căn cứ: Thông tư 17/2012/TT-BYT (mẫu giấy chứng sinh).",
        "retention_years": 75,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "so_giay_chung_sinh": {"type": "string", "title": "Số giấy chứng sinh"},
                "quyen_so": {"type": "string", "title": "Quyển số"},
                "ho_ten_me": {"type": "string", "title": "Họ tên mẹ"},
                "tuoi_me": {"type": "integer", "title": "Tuổi mẹ"},
                "cccd_me": {"type": "string", "title": "Số CCCD mẹ"},
                "noi_dang_ky_thuong_tru": {"type": "string", "title": "Nơi đăng ký thường trú"},
                "ho_ten_tre": {"type": "string", "title": "Họ tên trẻ (nếu đã đặt)"},
                "gioi_tinh": {"type": "string", "title": "Giới tính", "enum": ["Nam", "Nữ"]},
                "ngay_sinh": {"type": "string", "title": "Sinh lúc (ngày giờ)", "format": "date-time"},
                "noi_sinh": {"type": "string", "title": "Tại (cơ sở y tế)"},
                "tinh_trang_tre": {
                    "type": "string", "title": "Tình trạng trẻ khi sinh",
                    "enum": ["Khỏe mạnh", "Yếu", "Dị tật"],
                },
                "so_con_hien_song": {"type": "integer", "title": "Số con hiện sống (tính cả trẻ này)"},
                "ho_ten_cha": {"type": "string", "title": "Họ tên cha"},
                "nguoi_do_de": {"type": "string", "title": "Người đỡ đẻ"},
            },
            "required": ["ho_ten_me", "gioi_tinh", "ngay_sinh", "noi_sinh"],
        },
        "classification_prompt": (
            "Đây là GIẤY CHỨNG NHẬN / văn bản do cơ quan y tế cấp — "
            "Giấy chứng sinh do bệnh viện hoặc cơ sở y tế cấp. "
            "Có DẤU ĐỎ tròn của cơ sở y tế và chữ ký bác sĩ. "
            "Đặc điểm: có tiêu đề 'GIẤY CHỨNG SINH', logo Bộ Y tế hoặc cơ sở y tế, "
            "thông tin: họ tên mẹ, tuổi mẹ, giới tính trẻ, ngày giờ sinh, nơi sinh (tên bệnh viện), "
            "tình trạng trẻ khi sinh, họ tên cha, người đỡ đẻ."
        ),
        "route": ["RECEPTION", "JUDICIAL"],
    },
    {
        "name": "Giấy chứng nhận kết hôn",
        "code": "MARRIAGE_CERT",
        "description": "Giấy chứng nhận kết hôn do UBND cấp xã cấp. "
                       "Căn cứ: Luật Hôn nhân và Gia đình 2014, Điều 9; Luật Hộ tịch 2014, Điều 18.",
        "retention_years": 0,
        "retention_permanent": True,
        "template_schema": {
            "type": "object",
            "properties": {
                "so": {"type": "string", "title": "Số đăng ký kết hôn"},
                "quyen_so": {"type": "string", "title": "Quyển số"},
                "ho_ten_chong": {"type": "string", "title": "Họ và tên chồng"},
                "ngay_sinh_chong": {"type": "string", "title": "Ngày sinh chồng", "format": "date"},
                "dan_toc_chong": {"type": "string", "title": "Dân tộc chồng"},
                "quoc_tich_chong": {"type": "string", "title": "Quốc tịch chồng"},
                "cu_tru_chong": {"type": "string", "title": "Nơi cư trú chồng"},
                "cccd_chong": {"type": "string", "title": "Số CCCD chồng"},
                "ho_ten_vo": {"type": "string", "title": "Họ và tên vợ"},
                "ngay_sinh_vo": {"type": "string", "title": "Ngày sinh vợ", "format": "date"},
                "dan_toc_vo": {"type": "string", "title": "Dân tộc vợ"},
                "quoc_tich_vo": {"type": "string", "title": "Quốc tịch vợ"},
                "cu_tru_vo": {"type": "string", "title": "Nơi cư trú vợ"},
                "cccd_vo": {"type": "string", "title": "Số CCCD vợ"},
                "ngay_dang_ky": {"type": "string", "title": "Ngày đăng ký kết hôn", "format": "date"},
                "noi_dang_ky": {"type": "string", "title": "Nơi đăng ký (UBND xã/phường)"},
            },
            "required": ["ho_ten_chong", "ho_ten_vo", "ngay_dang_ky"],
        },
        "classification_prompt": (
            "Đây là GIẤY CHỨNG NHẬN / văn bản do cơ quan nhà nước cấp — "
            "Giấy chứng nhận kết hôn do UBND cấp xã/phường/thị trấn cấp. "
            "Có DẤU ĐỎ tròn của UBND, chữ ký Chủ tịch UBND. "
            "Đặc điểm: có tiêu đề 'GIẤY CHỨNG NHẬN KẾT HÔN', "
            "quốc hiệu 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', "
            "thông tin hai bên vợ chồng (họ tên, ngày sinh, dân tộc, quốc tịch, cư trú, CCCD), "
            "ngày đăng ký kết hôn."
        ),
        "route": ["RECEPTION", "JUDICIAL"],
    },
    {
        "name": "Tờ khai xác nhận tình trạng hôn nhân",
        "code": "MARITAL_STATUS_FORM",
        "description": "Tờ khai dùng để xin xác nhận tình trạng hôn nhân. "
                       "Căn cứ: Luật Hộ tịch 2014, Điều 21; Nghị định 123/2015/NĐ-CP, Điều 22; "
                       "Thông tư 04/2020/TT-BTP (mẫu tờ khai).",
        "retention_years": 20,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ho_ten": {"type": "string", "title": "Họ và tên"},
                "ngay_sinh": {"type": "string", "title": "Ngày sinh", "format": "date"},
                "gioi_tinh": {"type": "string", "title": "Giới tính", "enum": ["Nam", "Nữ"]},
                "dan_toc": {"type": "string", "title": "Dân tộc"},
                "quoc_tich": {"type": "string", "title": "Quốc tịch"},
                "so_cccd": {"type": "string", "title": "Số CCCD/CMND"},
                "noi_cu_tru": {"type": "string", "title": "Nơi cư trú"},
                "tinh_trang_hon_nhan": {
                    "type": "string",
                    "title": "Tình trạng hôn nhân hiện tại",
                    "enum": ["Chưa đăng ký kết hôn", "Đã ly hôn", "Vợ/chồng đã chết"],
                },
                "muc_dich_su_dung": {"type": "string", "title": "Mục đích xin xác nhận"},
                "ngay_khai": {"type": "string", "title": "Ngày khai", "format": "date"},
            },
            "required": ["ho_ten", "ngay_sinh", "so_cccd", "tinh_trang_hon_nhan"],
        },
        "classification_prompt": (
            "Đây là TỜ KHAI / mẫu đơn do công dân tự điền — Tờ khai xác nhận tình trạng hôn nhân. "
            "Thường in trắng đen trên giấy A4, có các dòng chấm/ô trống để điền thông tin. "
            "Mẫu theo Thông tư 04/2020/TT-BTP. "
            "Đặc điểm: có tiêu đề 'TỜ KHAI XÁC NHẬN TÌNH TRẠNG HÔN NHÂN', quốc hiệu, "
            "các trường: họ tên, ngày sinh, giới tính, dân tộc, quốc tịch, CCCD, nơi cư trú, "
            "tình trạng hôn nhân hiện tại (chưa kết hôn / đã ly hôn / goá), "
            "mục đích sử dụng giấy xác nhận. "
            "KHÔNG có dấu đỏ của cơ quan nhà nước (khác với Giấy xác nhận tình trạng hôn nhân do UBND cấp)."
        ),
        "route": ["RECEPTION", "JUDICIAL"],
    },

    # ── Residence Documents (Cư trú) ──
    {
        "name": "Tờ khai thay đổi thông tin cư trú (Mẫu CT01)",
        "code": "RESIDENCE_FORM_CT01",
        "description": "Tờ khai thay đổi thông tin cư trú, dùng cho đăng ký thường trú/tạm trú. "
                       "Căn cứ: Luật Cư trú 2020, Điều 20-21; Nghị định 62/2021/NĐ-CP; "
                       "Thông tư 56/2021/TT-BCA (mẫu CT01).",
        "retention_years": 10,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ho_ten": {"type": "string", "title": "Họ và tên"},
                "ngay_sinh": {"type": "string", "title": "Ngày sinh", "format": "date"},
                "gioi_tinh": {"type": "string", "title": "Giới tính", "enum": ["Nam", "Nữ"]},
                "so_cccd": {"type": "string", "title": "Số CCCD"},
                "dan_toc": {"type": "string", "title": "Dân tộc"},
                "quoc_tich": {"type": "string", "title": "Quốc tịch"},
                "ton_giao": {"type": "string", "title": "Tôn giáo"},
                "noi_sinh": {"type": "string", "title": "Nơi sinh"},
                "que_quan": {"type": "string", "title": "Quê quán"},
                "nghe_nghiep": {"type": "string", "title": "Nghề nghiệp"},
                "noi_lam_viec": {"type": "string", "title": "Nơi làm việc"},
                "noi_thuong_tru_hien_tai": {"type": "string", "title": "Nơi thường trú hiện tại"},
                "dia_chi_dang_ky_moi": {"type": "string", "title": "Địa chỉ đăng ký mới"},
                "loai_cho_o": {
                    "type": "string",
                    "title": "Loại chỗ ở",
                    "enum": ["Nhà ở thuộc sở hữu", "Nhà thuê", "Nhà ở nhờ", "Khác"],
                },
                "ly_do_thay_doi": {"type": "string", "title": "Lý do thay đổi"},
            },
            "required": ["ho_ten", "ngay_sinh", "so_cccd", "dia_chi_dang_ky_moi"],
        },
        "classification_prompt": (
            "Đây là TỜ KHAI / mẫu đơn do công dân tự điền — Tờ khai thay đổi thông tin cư trú (Mẫu CT01). "
            "Thường in trắng đen trên giấy A4, có các dòng chấm/ô trống để điền thông tin. "
            "Mẫu theo Thông tư 56/2021/TT-BCA. "
            "Đặc điểm: có tiêu đề 'TỜ KHAI THAY ĐỔI THÔNG TIN CƯ TRÚ', quốc hiệu, "
            "mã mẫu CT01, các trường: họ tên, CCCD, ngày sinh, địa chỉ cũ, địa chỉ mới, "
            "loại chỗ ở (sở hữu/thuê/ở nhờ), lý do thay đổi."
        ),
        "route": ["RECEPTION", "POLICE"],
    },
    {
        "name": "Giấy tờ chứng minh chỗ ở hợp pháp",
        "code": "RESIDENCE_PROOF",
        "description": "Giấy tờ chứng minh quyền sở hữu/sử dụng chỗ ở: Giấy chứng nhận QSDĐ (sổ đỏ), "
                       "hợp đồng mua bán nhà, hợp đồng thuê nhà có công chứng, "
                       "hoặc văn bản xác nhận của chủ sở hữu. "
                       "Căn cứ: Luật Cư trú 2020, Điều 5 (giải thích chỗ ở hợp pháp).",
        "retention_years": 10,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "loai_giay_to": {
                    "type": "string",
                    "title": "Loại giấy tờ",
                    "enum": [
                        "Giấy chứng nhận QSDĐ (Sổ đỏ)",
                        "Hợp đồng mua bán nhà ở",
                        "Hợp đồng thuê nhà",
                        "Văn bản đồng ý cho ở nhờ",
                        "Khác",
                    ],
                },
                "dia_chi": {"type": "string", "title": "Địa chỉ nhà/đất"},
                "chu_so_huu": {"type": "string", "title": "Chủ sở hữu/cho thuê"},
                "dien_tich": {"type": "string", "title": "Diện tích (m²)"},
                "thoi_han": {"type": "string", "title": "Thời hạn (nếu thuê)"},
                "so_hop_dong": {"type": "string", "title": "Số hợp đồng/giấy chứng nhận"},
                "ngay_cap": {"type": "string", "title": "Ngày cấp/ký", "format": "date"},
            },
            "required": ["loai_giay_to", "dia_chi"],
        },
        "classification_prompt": (
            "Đây là giấy tờ chứng minh chỗ ở hợp pháp, có thể là: "
            "1) Giấy chứng nhận quyền sử dụng đất (sổ đỏ/sổ hồng) — bìa đỏ, quốc huy, "
            "thông tin thửa đất, diện tích, chủ sở hữu. "
            "2) Hợp đồng mua bán nhà — có công chứng, hai bên, giá, địa chỉ. "
            "3) Hợp đồng thuê nhà — có bên thuê, bên cho thuê, thời hạn, giá thuê, địa chỉ. "
            "4) Văn bản đồng ý cho ở nhờ — xác nhận từ chủ nhà."
        ),
        "route": ["RECEPTION", "ADMIN"],
    },

    # ── Business Registration Documents ──
    {
        "name": "Giấy đề nghị đăng ký hộ kinh doanh",
        "code": "BIZ_REG_FORM",
        "description": "Giấy đề nghị đăng ký hộ kinh doanh theo Phụ lục III-1 Thông tư 01/2021/TT-BKHĐT. "
                       "Căn cứ: Nghị định 01/2021/NĐ-CP, Điều 82-87.",
        "retention_years": 10,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ten_ho_kinh_doanh": {"type": "string", "title": "Tên hộ kinh doanh"},
                "dia_diem_kinh_doanh": {"type": "string", "title": "Địa điểm kinh doanh"},
                "nganh_nghe": {"type": "string", "title": "Ngành, nghề kinh doanh"},
                "ma_nganh_vsic": {"type": "string", "title": "Mã ngành VSIC (nếu có)"},
                "von_kinh_doanh": {"type": "string", "title": "Vốn kinh doanh (VNĐ)"},
                "so_lao_dong": {"type": "integer", "title": "Số lượng lao động"},
                "ho_ten_chu_ho": {"type": "string", "title": "Họ và tên chủ hộ kinh doanh"},
                "gioi_tinh_chu_ho": {"type": "string", "title": "Giới tính", "enum": ["Nam", "Nữ"]},
                "ngay_sinh_chu_ho": {"type": "string", "title": "Ngày sinh chủ hộ", "format": "date"},
                "so_cccd_chu_ho": {"type": "string", "title": "Số CCCD chủ hộ"},
                "noi_cu_tru_chu_ho": {"type": "string", "title": "Nơi cư trú chủ hộ"},
                "dien_thoai": {"type": "string", "title": "Số điện thoại"},
                "email": {"type": "string", "title": "Email (nếu có)", "format": "email"},
            },
            "required": ["ten_ho_kinh_doanh", "dia_diem_kinh_doanh", "nganh_nghe", "ho_ten_chu_ho", "so_cccd_chu_ho"],
        },
        "classification_prompt": (
            "Đây là TỜ KHAI / mẫu đơn do công dân tự điền — Giấy đề nghị đăng ký hộ kinh doanh (Phụ lục III-1). "
            "Thường in trắng đen trên giấy A4, có các dòng chấm/ô trống để điền thông tin. "
            "Mẫu theo Nghị định 01/2021/NĐ-CP. "
            "Đặc điểm: có tiêu đề 'GIẤY ĐỀ NGHỊ ĐĂNG KÝ HỘ KINH DOANH', quốc hiệu, "
            "kính gửi Phòng Tài chính - Kế hoạch, "
            "các trường: tên hộ kinh doanh, địa điểm, ngành nghề, vốn kinh doanh, "
            "thông tin chủ hộ (họ tên, CCCD, cư trú), số lao động. "
            "KHÔNG có dấu đỏ — đây là đơn đề nghị, chưa phải giấy chứng nhận."
        ),
        "route": ["RECEPTION", "FINANCE"],
    },
    {
        "name": "Giấy đề nghị đăng ký doanh nghiệp",
        "code": "COMPANY_REG_FORM",
        "description": "Giấy đề nghị đăng ký thành lập doanh nghiệp (Công ty TNHH/CP/Hợp danh). "
                       "Căn cứ: Luật Doanh nghiệp 2020, Điều 21-27; "
                       "Nghị định 01/2021/NĐ-CP; Thông tư 01/2021/TT-BKHĐT (Phụ lục I-3, I-4, I-5).",
        "retention_years": 20,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ten_doanh_nghiep": {"type": "string", "title": "Tên doanh nghiệp"},
                "ten_viet_tat": {"type": "string", "title": "Tên viết tắt"},
                "ten_tieng_anh": {"type": "string", "title": "Tên tiếng Anh (nếu có)"},
                "loai_hinh": {
                    "type": "string",
                    "title": "Loại hình doanh nghiệp",
                    "enum": [
                        "Công ty TNHH một thành viên",
                        "Công ty TNHH hai thành viên trở lên",
                        "Công ty cổ phần",
                        "Công ty hợp danh",
                    ],
                },
                "dia_chi_tru_so": {"type": "string", "title": "Địa chỉ trụ sở chính"},
                "dien_thoai": {"type": "string", "title": "Số điện thoại"},
                "email": {"type": "string", "title": "Email", "format": "email"},
                "website": {"type": "string", "title": "Website (nếu có)"},
                "von_dieu_le": {"type": "string", "title": "Vốn điều lệ (VNĐ)"},
                "nganh_nghe_chinh": {"type": "string", "title": "Ngành, nghề kinh doanh chính"},
                "ma_nganh_vsic": {"type": "string", "title": "Mã ngành VSIC"},
                "ho_ten_nguoi_dai_dien": {"type": "string", "title": "Họ tên người đại diện pháp luật"},
                "chuc_danh": {"type": "string", "title": "Chức danh (Giám đốc/Tổng giám đốc)"},
                "so_cccd_nguoi_dai_dien": {"type": "string", "title": "Số CCCD người đại diện"},
                "ngay_sinh_nguoi_dai_dien": {"type": "string", "title": "Ngày sinh NDD", "format": "date"},
            },
            "required": ["ten_doanh_nghiep", "loai_hinh", "dia_chi_tru_so", "von_dieu_le", "ho_ten_nguoi_dai_dien"],
        },
        "classification_prompt": (
            "Đây là TỜ KHAI / mẫu đơn do công dân tự điền — Giấy đề nghị đăng ký doanh nghiệp (thành lập công ty). "
            "Thường in trắng đen trên giấy A4, có các dòng chấm/ô trống để điền thông tin. "
            "Mẫu theo Thông tư 01/2021/TT-BKHĐT (Phụ lục I-3, I-4, I-5). "
            "Đặc điểm: có tiêu đề 'GIẤY ĐỀ NGHỊ ĐĂNG KÝ DOANH NGHIỆP', quốc hiệu, "
            "kính gửi Phòng Đăng ký kinh doanh, "
            "các trường: tên doanh nghiệp (VN + tiếng Anh), loại hình (TNHH/CP/Hợp danh), "
            "địa chỉ trụ sở, vốn điều lệ, ngành nghề + mã VSIC, "
            "thông tin người đại diện pháp luật (họ tên, CCCD, chức danh). "
            "KHÔNG có dấu đỏ — đây là đơn đề nghị, chưa phải giấy chứng nhận."
        ),
        "route": ["RECEPTION", "FINANCE", "JUDICIAL"],
    },
    {
        "name": "Điều lệ công ty",
        "code": "COMPANY_CHARTER",
        "description": "Điều lệ công ty theo quy định tại Luật Doanh nghiệp 2020, Điều 24. "
                       "Nội dung bắt buộc: tên, địa chỉ, ngành nghề, vốn điều lệ, "
                       "cơ cấu tổ chức quản lý, người đại diện, quyền/nghĩa vụ thành viên.",
        "retention_years": 20,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ten_doanh_nghiep": {"type": "string", "title": "Tên doanh nghiệp"},
                "dia_chi_tru_so": {"type": "string", "title": "Địa chỉ trụ sở chính"},
                "nganh_nghe": {"type": "string", "title": "Ngành, nghề kinh doanh"},
                "von_dieu_le": {"type": "string", "title": "Vốn điều lệ"},
                "co_cau_to_chuc": {"type": "string", "title": "Cơ cấu tổ chức quản lý"},
                "nguoi_dai_dien": {"type": "string", "title": "Người đại diện pháp luật"},
                "so_thanh_vien": {"type": "integer", "title": "Số thành viên/cổ đông sáng lập"},
                "ngay_thong_qua": {"type": "string", "title": "Ngày thông qua điều lệ", "format": "date"},
            },
            "required": ["ten_doanh_nghiep", "von_dieu_le"],
        },
        "classification_prompt": (
            "Đây là Điều lệ công ty (Company Charter/Articles of Association). "
            "Đặc điểm: văn bản nhiều trang, có tiêu đề 'ĐIỀU LỆ CÔNG TY' hoặc 'ĐIỀU LỆ', "
            "chia thành các chương/điều, nội dung: tên công ty, vốn điều lệ, "
            "cơ cấu tổ chức, quyền và nghĩa vụ thành viên, phân chia lợi nhuận, "
            "có chữ ký các thành viên/cổ đông sáng lập ở trang cuối."
        ),
        "route": ["RECEPTION", "JUDICIAL"],
    },
    {
        "name": "Danh sách thành viên / cổ đông sáng lập",
        "code": "MEMBER_LIST",
        "description": "Danh sách thành viên (Công ty TNHH) hoặc cổ đông sáng lập (Công ty CP). "
                       "Căn cứ: Luật Doanh nghiệp 2020, Điều 22(2)(c), 23(2)(c).",
        "retention_years": 20,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ten_doanh_nghiep": {"type": "string", "title": "Tên doanh nghiệp"},
                "loai_danh_sach": {
                    "type": "string",
                    "title": "Loại danh sách",
                    "enum": ["Thành viên công ty TNHH", "Cổ đông sáng lập công ty CP", "Thành viên hợp danh"],
                },
                "tong_so_thanh_vien": {"type": "integer", "title": "Tổng số thành viên/cổ đông"},
                "tong_von_dieu_le": {"type": "string", "title": "Tổng vốn điều lệ"},
                "ngay_lap": {"type": "string", "title": "Ngày lập", "format": "date"},
            },
            "required": ["ten_doanh_nghiep", "loai_danh_sach"],
        },
        "classification_prompt": (
            "Đây là Danh sách thành viên hoặc cổ đông sáng lập công ty. "
            "Đặc điểm: bảng danh sách có các cột: STT, họ tên, ngày sinh, CCCD, "
            "địa chỉ, tỷ lệ vốn góp (%), giá trị vốn góp (VNĐ), ngày góp vốn. "
            "Có tiêu đề 'DANH SÁCH THÀNH VIÊN' hoặc 'DANH SÁCH CỔ ĐÔNG SÁNG LẬP', "
            "chữ ký từng thành viên."
        ),
        "route": ["RECEPTION", "FINANCE"],
    },

    # ── Complaints ──
    {
        "name": "Đơn khiếu nại / tố cáo",
        "code": "COMPLAINT",
        "description": "Đơn khiếu nại hoặc đơn tố cáo của công dân. "
                       "Căn cứ: Luật Khiếu nại 2011, Điều 8; Luật Tố cáo 2018, Điều 23.",
        "retention_years": 5,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "loai_don": {
                    "type": "string",
                    "title": "Loại đơn",
                    "enum": ["Khiếu nại", "Tố cáo"],
                },
                "ho_ten_nguoi_gui": {"type": "string", "title": "Họ tên người gửi"},
                "so_cccd": {"type": "string", "title": "Số CCCD"},
                "dia_chi": {"type": "string", "title": "Địa chỉ"},
                "dien_thoai": {"type": "string", "title": "Số điện thoại"},
                "doi_tuong_khieu_nai": {"type": "string", "title": "Đối tượng bị khiếu nại / tố cáo"},
                "quyet_dinh_bi_khieu_nai": {"type": "string", "title": "Quyết định / hành vi bị khiếu nại"},
                "noi_dung": {"type": "string", "title": "Nội dung khiếu nại / tố cáo"},
                "yeu_cau": {"type": "string", "title": "Yêu cầu giải quyết"},
                "tai_lieu_kem_theo": {"type": "string", "title": "Tài liệu, chứng cứ kèm theo"},
                "ngay_gui": {"type": "string", "title": "Ngày gửi đơn", "format": "date"},
            },
            "required": ["ho_ten_nguoi_gui", "noi_dung", "yeu_cau"],
        },
        "classification_prompt": (
            "Đây là Đơn khiếu nại hoặc Đơn tố cáo của công dân. "
            "Đặc điểm: có tiêu đề 'ĐƠN KHIẾU NẠI' hoặc 'ĐƠN TỐ CÁO', quốc hiệu, "
            "kính gửi cơ quan hành chính (UBND, Chủ tịch UBND), "
            "nội dung: người gửi tự trình bày sự việc, quyết định/hành vi bị khiếu nại, "
            "yêu cầu giải quyết, cam kết trung thực, chữ ký người gửi."
        ),
        "route": ["RECEPTION", "ADMIN", "LEADERSHIP"],
    },

    # ── Classified / Internal ──
    {
        "name": "Báo cáo mật",
        "code": "CLASSIFIED_RPT",
        "description": "Báo cáo nội bộ có độ mật. Căn cứ: Luật Bảo vệ bí mật nhà nước 2018.",
        "retention_years": 0,
        "retention_permanent": True,
        "template_schema": {
            "type": "object",
            "properties": {
                "tieu_de": {"type": "string", "title": "Tiêu đề báo cáo"},
                "do_mat": {"type": "string", "title": "Độ mật", "enum": ["Mật", "Tối mật", "Tuyệt mật"]},
                "co_quan_ban_hanh": {"type": "string", "title": "Cơ quan ban hành"},
                "nguoi_ky": {"type": "string", "title": "Người ký"},
                "ngay_ban_hanh": {"type": "string", "title": "Ngày ban hành", "format": "date"},
                "tom_tat": {"type": "string", "title": "Tóm tắt nội dung"},
            },
            "required": ["tieu_de", "do_mat", "co_quan_ban_hanh"],
        },
        "classification_prompt": (
            "Đây là báo cáo nội bộ có độ mật của cơ quan nhà nước. "
            "Đặc điểm: có đóng dấu 'MẬT', 'TỐI MẬT' hoặc 'TUYỆT MẬT' ở góc phải trên, "
            "tiêu đề báo cáo, cơ quan ban hành, người ký (có chức danh), "
            "dấu đỏ cơ quan, thường có số hiệu văn bản."
        ),
        "route": ["RECEPTION", "INTERNAL", "LEADERSHIP"],
    },

    # ── Supporting Documents ──
    {
        "name": "Giấy xác nhận thông tin cư trú",
        "code": "RESIDENCE_CONFIRM",
        "description": "Giấy xác nhận thông tin về cư trú do Công an cấp xã/phường cấp. "
                       "Thay thế Sổ hộ khẩu giấy từ 01/01/2023. "
                       "Căn cứ: Luật Cư trú 2020, Điều 17.",
        "retention_years": 5,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "ho_ten": {"type": "string", "title": "Họ và tên"},
                "so_cccd": {"type": "string", "title": "Số CCCD"},
                "noi_thuong_tru": {"type": "string", "title": "Nơi thường trú"},
                "noi_tam_tru": {"type": "string", "title": "Nơi tạm trú (nếu có)"},
                "ngay_dang_ky": {"type": "string", "title": "Ngày đăng ký cư trú gần nhất", "format": "date"},
                "so_thanh_vien_ho": {"type": "integer", "title": "Số thành viên trong hộ"},
                "ngay_xac_nhan": {"type": "string", "title": "Ngày xác nhận", "format": "date"},
                "co_quan_xac_nhan": {"type": "string", "title": "Cơ quan xác nhận (Công an xã/phường)"},
            },
            "required": ["ho_ten", "so_cccd", "noi_thuong_tru"],
        },
        "classification_prompt": (
            "Đây là Giấy xác nhận thông tin về cư trú do Công an cấp xã/phường cấp. "
            "Thay thế Sổ hộ khẩu giấy từ 01/01/2023. "
            "Đặc điểm: có tiêu đề 'GIẤY XÁC NHẬN THÔNG TIN VỀ CƯ TRÚ', "
            "logo Công an, nội dung: họ tên, CCCD, nơi thường trú, danh sách thành viên hộ, "
            "dấu đỏ Công an xã/phường."
        ),
        "route": ["RECEPTION"],
    },
]


async def seed(db: AsyncSession) -> dict:
    """Insert seed data. Skips existing records by code."""
    created_depts = 0
    created_types = 0
    created_rules = 0

    # Seed departments
    dept_map = {}
    for dept_data in DEPARTMENTS:
        existing = await db.execute(select(Department).where(Department.code == dept_data["code"]))
        dept = existing.scalar_one_or_none()
        if dept is None:
            dept = Department(**dept_data)
            db.add(dept)
            await db.flush()
            created_depts += 1
        dept_map[dept_data["code"]] = dept.id

    # Seed document types and routing rules
    for dt_data in DOCUMENT_TYPES:
        route_codes = dt_data.pop("route")
        existing = await db.execute(select(DocumentType).where(DocumentType.code == dt_data["code"]))
        doc_type = existing.scalar_one_or_none()
        if doc_type is None:
            doc_type = DocumentType(**dt_data)
            db.add(doc_type)
            await db.flush()
            created_types += 1

            # Create routing rules
            for i, dept_code in enumerate(route_codes, start=1):
                rule = RoutingRule(
                    document_type_id=doc_type.id,
                    department_id=dept_map[dept_code],
                    step_order=i,
                    expected_duration_hours=48 if i == 1 else 72,
                    required_clearance_level=0,
                )
                db.add(rule)
                created_rules += 1

    await db.commit()

    case_types_result = await seed_case_types(db, dept_map)

    return {
        "departments_created": created_depts,
        "document_types_created": created_types,
        "routing_rules_created": created_rules,
        **case_types_result,
    }


# ---------------------------------------------------------------------------
# Case type seed data
# ---------------------------------------------------------------------------

CASE_TYPES = [
    # ── 1. Đăng ký khai sinh ──
    # Căn cứ: Luật Hộ tịch 2014, Đ.16; NĐ 123/2015, Đ.9; TT 04/2020/TT-BTP
    {
        "name": "Đăng ký khai sinh",
        "code": "BIRTH_REG",
        "description": (
            "Thủ tục đăng ký khai sinh tại UBND cấp xã. "
            "Thời hạn: 60 ngày kể từ ngày sinh. Nếu quá hạn, phải đăng ký lại. "
            "Căn cứ: Luật Hộ tịch 2014, Điều 16; NĐ 123/2015/NĐ-CP, Điều 9."
        ),
        "retention_years": 75,
        "retention_permanent": False,
        "routing": ["RECEPTION", "JUDICIAL"],
        "groups": [
            {
                "group_order": 1,
                "label": "Tờ khai đăng ký khai sinh",
                "is_mandatory": True,
                "slots": [{"doc_code": "BIRTH_REG_FORM", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "Giấy chứng sinh",
                "is_mandatory": True,
                "slots": [{"doc_code": "BIRTH_CERTIFICATE_MEDICAL", "label_override": None}],
            },
            {
                "group_order": 3,
                "label": "CCCD/CMND của người đi đăng ký (cha hoặc mẹ)",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "ID_CCCD", "label_override": "CCCD/CMND cha hoặc mẹ"},
                    {"doc_code": "PASSPORT_VN", "label_override": "Hộ chiếu (nếu không có CCCD)"},
                ],
            },
            {
                "group_order": 4,
                "label": "Giấy chứng nhận kết hôn (nếu cha mẹ đã đăng ký kết hôn)",
                "is_mandatory": False,
                "slots": [{"doc_code": "MARRIAGE_CERT", "label_override": None}],
            },
        ],
    },

    # ── 2. Xác nhận tình trạng hôn nhân ──
    # Căn cứ: Luật Hộ tịch 2014, Đ.21; NĐ 123/2015, Đ.22; TT 04/2020/TT-BTP
    {
        "name": "Xác nhận tình trạng hôn nhân",
        "code": "MARITAL_STATUS_CONFIRM",
        "description": (
            "Thủ tục xin xác nhận tình trạng hôn nhân tại UBND cấp xã nơi cư trú. "
            "Giấy xác nhận có giá trị 6 tháng kể từ ngày cấp. "
            "Căn cứ: Luật Hộ tịch 2014, Điều 21; NĐ 123/2015/NĐ-CP, Điều 22."
        ),
        "retention_years": 20,
        "retention_permanent": False,
        "routing": ["RECEPTION", "JUDICIAL"],
        "groups": [
            {
                "group_order": 1,
                "label": "Tờ khai xác nhận tình trạng hôn nhân",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS_FORM", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "CCCD/CMND hoặc Hộ chiếu còn hiệu lực",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "ID_CCCD", "label_override": "CCCD/CMND còn hiệu lực"},
                    {"doc_code": "PASSPORT_VN", "label_override": "Hộ chiếu còn hiệu lực"},
                ],
            },
            {
                "group_order": 3,
                "label": "Giấy xác nhận thông tin cư trú",
                "is_mandatory": True,
                "slots": [{"doc_code": "RESIDENCE_CONFIRM", "label_override": None}],
            },
        ],
    },

    # ── 3. Đăng ký thường trú ──
    # Căn cứ: Luật Cư trú 2020, Đ.20-21; NĐ 62/2021/NĐ-CP; TT 56/2021/TT-BCA
    {
        "name": "Đăng ký thường trú",
        "code": "RESIDENCE_REG",
        "description": (
            "Thủ tục đăng ký thường trú tại Công an cấp xã/phường. "
            "Từ 01/07/2021 bỏ sổ hộ khẩu giấy, quản lý qua Cơ sở dữ liệu quốc gia về dân cư. "
            "Căn cứ: Luật Cư trú 2020, Điều 20; NĐ 62/2021/NĐ-CP."
        ),
        "retention_years": 10,
        "retention_permanent": False,
        "routing": ["RECEPTION", "POLICE"],
        "groups": [
            {
                "group_order": 1,
                "label": "Tờ khai thay đổi thông tin cư trú (Mẫu CT01)",
                "is_mandatory": True,
                "slots": [{"doc_code": "RESIDENCE_FORM_CT01", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "CCCD/CMND hoặc Hộ chiếu",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "ID_CCCD", "label_override": "CCCD/CMND"},
                    {"doc_code": "PASSPORT_VN", "label_override": "Hộ chiếu"},
                ],
            },
            {
                "group_order": 3,
                "label": "Giấy tờ chứng minh chỗ ở hợp pháp",
                "is_mandatory": True,
                "slots": [{"doc_code": "RESIDENCE_PROOF", "label_override": None}],
            },
        ],
    },

    # ── 4. Đăng ký hộ kinh doanh ──
    # Căn cứ: NĐ 01/2021/NĐ-CP, Đ.82-87; TT 01/2021/TT-BKHĐT (Phụ lục III-1)
    {
        "name": "Đăng ký hộ kinh doanh cá thể",
        "code": "HOUSEHOLD_BIZ_REG",
        "description": (
            "Thủ tục đăng ký hộ kinh doanh tại Phòng Tài chính - Kế hoạch cấp huyện/quận. "
            "Thời hạn giải quyết: 3 ngày làm việc. "
            "Căn cứ: NĐ 01/2021/NĐ-CP, Điều 82-87; TT 01/2021/TT-BKHĐT."
        ),
        "retention_years": 10,
        "retention_permanent": False,
        "routing": ["RECEPTION", "FINANCE"],
        "groups": [
            {
                "group_order": 1,
                "label": "Giấy đề nghị đăng ký hộ kinh doanh",
                "is_mandatory": True,
                "slots": [{"doc_code": "BIZ_REG_FORM", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "CCCD/CMND chủ hộ kinh doanh",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "ID_CCCD", "label_override": "CCCD/CMND chủ hộ kinh doanh"},
                    {"doc_code": "PASSPORT_VN", "label_override": "Hộ chiếu chủ hộ kinh doanh"},
                ],
            },
            {
                "group_order": 3,
                "label": "Giấy tờ chứng minh địa điểm kinh doanh",
                "is_mandatory": True,
                "slots": [{"doc_code": "RESIDENCE_PROOF", "label_override": "Hợp đồng thuê/Sổ đỏ địa điểm kinh doanh"}],
            },
        ],
    },

    # ── 5. Đăng ký doanh nghiệp ──
    # Căn cứ: Luật DN 2020, Đ.21-27; NĐ 01/2021/NĐ-CP; TT 01/2021/TT-BKHĐT
    {
        "name": "Đăng ký doanh nghiệp (Công ty TNHH/Cổ phần/Hợp danh)",
        "code": "COMPANY_REG",
        "description": (
            "Thủ tục đăng ký thành lập doanh nghiệp tại Phòng Đăng ký kinh doanh. "
            "Thời hạn giải quyết: 3 ngày làm việc kể từ khi nhận đủ hồ sơ hợp lệ. "
            "Căn cứ: Luật Doanh nghiệp 2020, Điều 21-27; NĐ 01/2021/NĐ-CP."
        ),
        "retention_years": 20,
        "retention_permanent": False,
        "routing": ["RECEPTION", "FINANCE", "JUDICIAL"],
        "groups": [
            {
                "group_order": 1,
                "label": "Giấy đề nghị đăng ký doanh nghiệp",
                "is_mandatory": True,
                "slots": [{"doc_code": "COMPANY_REG_FORM", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "Điều lệ công ty",
                "is_mandatory": True,
                "slots": [{"doc_code": "COMPANY_CHARTER", "label_override": None}],
            },
            {
                "group_order": 3,
                "label": "Danh sách thành viên / cổ đông sáng lập",
                "is_mandatory": True,
                "slots": [{"doc_code": "MEMBER_LIST", "label_override": None}],
            },
            {
                "group_order": 4,
                "label": "CCCD/CMND người đại diện pháp luật và các thành viên",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "ID_CCCD", "label_override": "CCCD/CMND người đại diện & thành viên"},
                    {"doc_code": "PASSPORT_VN", "label_override": "Hộ chiếu (nếu không có CCCD)"},
                ],
            },
            {
                "group_order": 5,
                "label": "Giấy tờ chứng minh trụ sở chính",
                "is_mandatory": True,
                "slots": [{"doc_code": "RESIDENCE_PROOF", "label_override": "Hợp đồng thuê/Sổ đỏ trụ sở"}],
            },
        ],
    },

    # ── 6. Khiếu nại / Tố cáo ──
    # Căn cứ: Luật Khiếu nại 2011, Đ.8; Luật Tố cáo 2018, Đ.23
    {
        "name": "Khiếu nại / Tố cáo",
        "code": "COMPLAINT_CASE",
        "description": (
            "Thủ tục tiếp nhận đơn khiếu nại, tố cáo của công dân. "
            "Thời hạn thụ lý: 10 ngày (khiếu nại), 7 ngày (tố cáo). "
            "Căn cứ: Luật Khiếu nại 2011, Điều 8; Luật Tố cáo 2018, Điều 23."
        ),
        "retention_years": 5,
        "retention_permanent": False,
        "routing": ["RECEPTION", "ADMIN", "LEADERSHIP"],
        "groups": [
            {
                "group_order": 1,
                "label": "Đơn khiếu nại / tố cáo",
                "is_mandatory": True,
                "slots": [{"doc_code": "COMPLAINT", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "CCCD/CMND người khiếu nại / tố cáo",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "ID_CCCD", "label_override": "CCCD/CMND người gửi đơn"},
                    {"doc_code": "PASSPORT_VN", "label_override": "Hộ chiếu người gửi đơn"},
                ],
            },
        ],
    },
    # ── 6. Hồ sơ quét nhanh (Quick Scan) ──
    {
        "name": "Hồ sơ quét nhanh",
        "code": "QUICK_SCAN",
        "description": (
            "Hồ sơ được tạo tự động khi nhân viên thực hiện quét nhanh tài liệu. "
            "Dùng cho các trường hợp tiếp nhận hồ sơ nhanh tại quầy."
        ),
        "retention_years": 5,
        "retention_permanent": False,
        "routing": ["RECEPTION"],
        "groups": [],
    },
]


async def seed_case_types(db: AsyncSession, dept_map: dict | None = None) -> dict:
    """Seed CaseType, DocumentRequirementGroup, DocumentRequirementSlot, CaseTypeRoutingStep.

    Idempotent: skips any case type whose code already exists.
    dept_map: optional dict of dept_code -> dept_id; fetched fresh if not provided.
    """
    if dept_map is None:
        result = await db.execute(select(Department))
        dept_map = {d.code: d.id for d in result.scalars().all()}

    # Build doc_type code -> id map
    dt_result = await db.execute(select(DocumentType))
    dt_map = {dt.code: dt.id for dt in dt_result.scalars().all()}

    created_case_types = 0
    created_groups = 0
    created_slots = 0
    created_routing_steps = 0

    for ct_data in CASE_TYPES:
        existing = await db.execute(select(CaseType).where(CaseType.code == ct_data["code"]))
        if existing.scalar_one_or_none() is not None:
            continue

        case_type = CaseType(
            name=ct_data["name"],
            code=ct_data["code"],
            description=ct_data.get("description"),
            retention_years=ct_data["retention_years"],
            retention_permanent=ct_data["retention_permanent"],
        )
        db.add(case_type)
        await db.flush()
        created_case_types += 1

        # Requirement groups + slots
        for group_data in ct_data["groups"]:
            group = DocumentRequirementGroup(
                case_type_id=case_type.id,
                group_order=group_data["group_order"],
                label=group_data["label"],
                is_mandatory=group_data["is_mandatory"],
            )
            db.add(group)
            await db.flush()
            created_groups += 1

            for slot_data in group_data["slots"]:
                doc_type_id = dt_map.get(slot_data["doc_code"])
                if doc_type_id is None:
                    continue  # doc type not yet seeded, skip
                slot = DocumentRequirementSlot(
                    group_id=group.id,
                    document_type_id=doc_type_id,
                    label_override=slot_data.get("label_override"),
                )
                db.add(slot)
                created_slots += 1

        # Routing steps
        for i, dept_code in enumerate(ct_data["routing"], start=1):
            dept_id = dept_map.get(dept_code)
            if dept_id is None:
                continue
            step = CaseTypeRoutingStep(
                case_type_id=case_type.id,
                department_id=dept_id,
                step_order=i,
                expected_duration_hours=48 if i == 1 else 72,
                required_clearance_level=0,
            )
            db.add(step)
            created_routing_steps += 1

    # Seed staff members
    created_staff = 0
    staff_data = [
        {"employee_id": "NV001", "full_name": "Nguyễn Văn An",
         "dept_code": "RECEPTION", "clearance_level": 1, "role": "officer"},
        {"employee_id": "NV002", "full_name": "Trần Thị Bình",
         "dept_code": "ADMIN", "clearance_level": 2, "role": "officer"},
        {"employee_id": "NV003", "full_name": "Lê Văn Cường",
         "dept_code": "JUDICIAL", "clearance_level": 1, "role": "officer"},
        {"employee_id": "NV004", "full_name": "Phạm Thị Dung",
         "dept_code": "FINANCE", "clearance_level": 1, "role": "officer"},
        {"employee_id": "NV005", "full_name": "Hoàng Văn Em",
         "dept_code": "POLICE", "clearance_level": 1, "role": "officer"},
        {"employee_id": "NV006", "full_name": "Đỗ Thị Phương",
         "dept_code": "INTERNAL", "clearance_level": 2, "role": "officer"},
        {"employee_id": "NV007", "full_name": "Vũ Đức Giang",
         "dept_code": "LEADERSHIP", "clearance_level": 3, "role": "manager"},
    ]
    for s in staff_data:
        existing = await db.execute(select(StaffMember).where(StaffMember.employee_id == s["employee_id"]))
        if existing.scalar_one_or_none() is None:
            dept_id = dept_map.get(s["dept_code"])
            if dept_id:
                staff = StaffMember(
                    id=uuid.uuid4(),
                    employee_id=s["employee_id"],
                    full_name=s["full_name"],
                    department_id=dept_id,
                    clearance_level=s["clearance_level"],
                    role=s["role"],
                    password_hash=hash_password("password123"),
                )
                db.add(staff)
                created_staff += 1

    # Seed citizens (matching mock VNeID demo accounts + extras)
    created_citizens = 0
    citizen_data = [
        {"id_number": "012345678901", "full_name": "Phạm Văn Dũng", "phone_number": "0901234567"},
        {"id_number": "012345678902", "full_name": "Nguyễn Thị Mai", "phone_number": "0912345678"},
        {"id_number": "012345678903", "full_name": "Trần Văn Hùng", "phone_number": "0923456789"},
    ]
    for c in citizen_data:
        existing = await db.execute(select(Citizen).where(Citizen.id_number == c["id_number"]))
        if existing.scalar_one_or_none() is None:
            citizen = Citizen(
                id=uuid.uuid4(),
                vneid_subject_id=c["id_number"],
                id_number=c["id_number"],
                full_name=c["full_name"],
                phone_number=c["phone_number"],
            )
            db.add(citizen)
            created_citizens += 1

    await db.commit()
    return {
        "case_types_created": created_case_types,
        "requirement_groups_created": created_groups,
        "requirement_slots_created": created_slots,
        "case_type_routing_steps_created": created_routing_steps,
        "staff_created": created_staff,
        "citizens_created": created_citizens,
    }


async def main():
    async with async_session_factory() as db:
        result = await seed(db)
        import logging
        logging.getLogger(__name__).info("Seed complete: %s", result)

if __name__ == "__main__":
    import selectors
    import sys
    if sys.platform == "win32":
        selector = selectors.SelectSelector()
        loop = asyncio.SelectorEventLoop(selector)
        loop.run_until_complete(main())
        loop.close()
    else:
        asyncio.run(main())
