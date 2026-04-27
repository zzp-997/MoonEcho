"""AI 发布前脱敏提醒服务。

检测匿名内容中可识别信息，提供发布前提醒。

检测类型：
- 真实姓名（中文2-4字姓名 + 常见姓氏库匹配）
- 公司+职位组合
- 住址信息
- 手机号
- 微信号
- 身份证号
- 银行卡号
- 邮箱地址

设计要点：
- 使用正则模式匹配，不依赖外部 AI 服务
- 建议性提醒，不强制（返回检测结果给前端展示提醒弹窗）
- 检测结果包含类型、匹配位置、建议文案
- 避免过度误报：结合上下文判断
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 可识别信息类型枚举
# ---------------------------------------------------------------------------

class IdentityInfoType(str, Enum):
    """可识别信息类型。"""

    REAL_NAME = "real_name"             # 真实姓名
    COMPANY_POSITION = "company_position"  # 公司+职位
    ADDRESS = "address"                 # 住址信息
    PHONE_NUMBER = "phone_number"       # 手机号
    WECHAT_ID = "wechat_id"            # 微信号
    ID_CARD = "id_card"                # 身份证号
    BANK_CARD = "bank_card"            # 银行卡号
    EMAIL = "email"                    # 邮箱地址
    QQ_NUMBER = "qq_number"            # QQ号


# ---------------------------------------------------------------------------
# 检测结果
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class IdentityDetection:
    """单条可识别信息检测结果。"""

    info_type: IdentityInfoType
    matched_text: str           # 匹配到的文本
    position: int               # 在原文中的起始位置
    confidence: float = 0.5     # 置信度 0.0-1.0
    suggestion: str = ""        # 建议文案


@dataclass(slots=True)
class IdentityDetectionResult:
    """脱敏检测综合结果。"""

    has_warning: bool = False
    detections: list[IdentityDetection] = field(default_factory=list)
    warning_message: str = ""

    def add_detection(self, detection: IdentityDetection) -> None:
        """添加一条检测结果。"""
        self.detections.append(detection)
        if not self.has_warning:
            self.has_warning = True

    def get_warning_message(self) -> str:
        """生成综合提醒文案。"""
        if not self.detections:
            return ""

        # 按类型去重统计
        type_counts: dict[str, int] = {}
        for d in self.detections:
            label = _INFO_TYPE_LABELS.get(d.info_type, d.info_type.value)
            type_counts[label] = type_counts.get(label, 0) + 1

        if len(type_counts) == 1:
            label = list(type_counts.keys())[0]
            return f"你发布的内容里可能包含{label}，要注意保护隐私哦"

        labels = "、".join(type_counts.keys())
        return f"你发布的内容里可能包含{labels}，要注意保护隐私哦"


# ---------------------------------------------------------------------------
# 类型标签映射
# ---------------------------------------------------------------------------

_INFO_TYPE_LABELS: dict[IdentityInfoType, str] = {
    IdentityInfoType.REAL_NAME: "真实姓名",
    IdentityInfoType.COMPANY_POSITION: "公司职位信息",
    IdentityInfoType.ADDRESS: "住址信息",
    IdentityInfoType.PHONE_NUMBER: "手机号",
    IdentityInfoType.WECHAT_ID: "微信号",
    IdentityInfoType.ID_CARD: "身份证号",
    IdentityInfoType.BANK_CARD: "银行卡号",
    IdentityInfoType.EMAIL: "邮箱地址",
    IdentityInfoType.QQ_NUMBER: "QQ号",
}

_INFO_TYPE_SUGGESTIONS: dict[IdentityInfoType, str] = {
    IdentityInfoType.REAL_NAME: "建议用昵称或化名代替真实姓名",
    IdentityInfoType.COMPANY_POSITION: "建议不要透露具体公司名称和职位",
    IdentityInfoType.ADDRESS: "建议不要透露具体住址信息",
    IdentityInfoType.PHONE_NUMBER: "建议不要公开手机号，注意保护隐私",
    IdentityInfoType.WECHAT_ID: "建议不要公开微信号，注意保护隐私",
    IdentityInfoType.ID_CARD: "请勿公开身份证号，这非常危险",
    IdentityInfoType.BANK_CARD: "请勿公开银行卡号，这非常危险",
    IdentityInfoType.EMAIL: "建议不要公开邮箱地址",
    IdentityInfoType.QQ_NUMBER: "建议不要公开QQ号，注意保护隐私",
}


# ---------------------------------------------------------------------------
# 常见姓氏库（前200大姓，覆盖约96%汉族人口）
# ---------------------------------------------------------------------------

_COMMON_SURNAMES: set[str] = {
    "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈",
    "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许",
    "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏",
    "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章",
    "云", "苏", "潘", "葛", "奚", "范", "彭", "郎", "鲁", "韦",
    "昌", "马", "苗", "凤", "花", "方", "俞", "任", "袁", "柳",
    "酆", "鲍", "史", "唐", "费", "廉", "岑", "薛", "雷", "贺",
    "倪", "汤", "滕", "殷", "罗", "毕", "郝", "邬", "安", "常",
    "乐", "于", "时", "傅", "皮", "卞", "齐", "康", "伍", "余",
    "元", "卜", "顾", "孟", "平", "黄", "和", "穆", "萧", "尹",
    "姚", "邵", "湛", "汪", "祁", "毛", "禹", "狄", "米", "贝",
    "明", "臧", "计", "伏", "成", "戴", "谈", "宋", "茅", "庞",
    "熊", "纪", "舒", "屈", "项", "祝", "董", "梁", "杜", "阮",
    "蓝", "闵", "席", "季", "麻", "强", "贾", "路", "娄", "危",
    "江", "童", "颜", "郭", "梅", "盛", "林", "刁", "钟", "徐",
    "邱", "骆", "高", "夏", "蔡", "田", "樊", "胡", "凌", "霍",
    "虞", "万", "支", "柯", "昝", "管", "卢", "莫", "经", "房",
    "裘", "缪", "干", "解", "应", "宗", "丁", "宣", "贲", "邓",
    "郁", "单", "杭", "洪", "包", "诸", "左", "石", "崔", "吉",
    "钮", "龚", "程", "嵇", "邢", "滑", "裴", "陆", "荣", "翁",
    "荀", "羊", "於", "惠", "甄", "曲", "家", "封", "芮", "羿",
    "储", "靳", "汲", "邴", "糜", "松", "井", "段", "富", "巫",
    "乌", "焦", "巴", "弓", "牧", "隗", "山", "谷", "车", "侯",
    "宓", "蓬", "全", "郗", "班", "仰", "秋", "仲", "伊", "宫",
    "宁", "仇", "栾", "暴", "甘", "钭", "厉", "戎", "祖", "武",
    "符", "刘", "景", "詹", "束", "龙", "叶", "幸", "司", "韶",
    "郜", "黎", "蓟", "薄", "印", "宿", "白", "怀", "蒲", "台",
    "从", "鄂", "索", "咸", "籍", "赖", "卓", "蔺", "屠", "蒙",
    "池", "乔", "阴", "郁", "胥", "能", "苍", "双", "闻", "莘",
    "党", "翟", "谭", "贡", "劳", "逄", "姬", "申", "扶", "堵",
    "冉", "宰", "郦", "雍", "却", "璩", "桑", "桂", "濮", "牛",
    "寿", "通", "边", "扈", "燕", "冀", "郏", "浦", "尚", "农",
    "温", "别", "庄", "晏", "柴", "瞿", "阎", "充", "慕", "连",
    "茹", "习", "宦", "艾", "鱼", "容", "向", "古", "易", "慎",
    "戈", "廖", "庾", "终", "暨", "居", "衡", "步", "都", "耿",
    "满", "弘", "匡", "国", "文", "寇", "广", "禄", "阙", "东",
    "欧", "殳", "沃", "利", "蔚", "越", "夔", "隆", "师", "巩",
    "厍", "聂", "晁", "勾", "敖", "融", "冷", "訾", "辛", "阚",
    "那", "简", "饶", "空", "曾", "毋", "沙", "乜", "养", "鞠",
    "须", "丰", "巢", "关", "蒯", "相", "查", "后", "荆", "红",
    "游", "竺", "权", "逯", "盖", "益", "桓", "公", "万俟", "司马",
    "上官", "欧阳", "夏侯", "诸葛", "尉迟", "皇甫", "公孙", "慕容",
}


# ---------------------------------------------------------------------------
# 正则检测模式
# ---------------------------------------------------------------------------

# 手机号（中国大陆，1开头11位）
_PHONE_PATTERN = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')

# 微信号（6-20位字母开头，允许字母数字下划线连字符）
_WECHAT_PATTERN = re.compile(
    r'(?:微信|vx|weixin)[:\s：]\s*([a-zA-Z][a-zA-Z0-9_-]{5,19})',
    re.IGNORECASE,
)

# QQ号（5-12位纯数字，需有上下文标记）
_QQ_PATTERN = re.compile(
    r'(?:QQ|qq|Q群)[:\s：]\s*(\d{5,12})',
)

# 身份证号（18位，最后一位可以是X）
_ID_CARD_PATTERN = re.compile(
    r'(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)',
)

# 银行卡号（16-19位纯数字，需有上下文标记）
_BANK_CARD_PATTERN = re.compile(
    r'(?:银行卡|卡号|账号)[:\s：]\s*(\d{16,19})',
)

# 邮箱地址
_EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
)

# 住址模式（省市区 + 具体地址）
_ADDRESS_PATTERN = re.compile(
    r'(?:住|住在|住在哪|地址|家庭住址|我家在|我住在)[:\s：]?\s*'
    r'([\u4e00-\u9fa5]{2,6}(?:省|市|区|县|镇|街道|路|号|栋|楼|室)[\u4e00-\u9fa50-9]{3,30})',
)

# 公司+职位组合
_COMPANY_POSITION_PATTERN = re.compile(
    r'(?:在|任职|就职|工作于|就职于)[:\s]?\s*'
    r'([\u4e00-\u9fa5]{2,10}(?:公司|集团|企业|科技|有限|股份|工作室))'
    r'[\s，,]?\s*(?:任|担任|做|职位是|岗位是|当)[:\s]?\s*'
    r'([\u4e00-\u9fa5]{2,8}(?:经理|总监|主管|工程师|设计师|分析师|专员|助理|顾问|总裁|主任))',
)

# 简单公司名模式（公司名 + 在/工作）
_COMPANY_ALONE_PATTERN = re.compile(
    r'(?:在|入职|加入)[:\s]?\s*([\u4e00-\u9fa5]{2,10}(?:公司|集团|企业|科技|有限|股份|工作室))',
)

# 姓名模式（"我叫XX"、"我是XX"、"姓名XX"、"名字叫XX"）
_NAME_EXPLICIT_PATTERN = re.compile(
    r'(?:我叫|我是|我的名字|姓名是|名字叫|本人)[:\s]?\s*([\u4e00-\u9fa5]{2,4})',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# 姓名上下文排除模式（避免误报）
# ---------------------------------------------------------------------------

# 非姓名上下文（如"今天真的很开心"不会被误判）
_NAME_EXCLUSION_CONTEXTS: list[str] = [
    "心情", "感觉", "觉得", "真的", "好像", "应该",
    "今天", "昨天", "明天", "最近", "一直", "总是",
    "可以", "想要", "希望", "但是", "可是", "不过",
    "因为", "所以", "如果", "虽然", "就是", "还是",
]


# ---------------------------------------------------------------------------
# 脱敏检测核心
# ---------------------------------------------------------------------------

class IdentityDetector:
    """脱敏提醒服务。

    检测匿名内容中的可识别信息，提供发布前建议性提醒。

    使用示例：
        detector = IdentityDetector()
        result = detector.detect("我叫张三，手机号13812345678")
        if result.has_warning:
            # 展示提醒弹窗
    """

    def detect(self, content: str) -> IdentityDetectionResult:
        """检测内容中的可识别信息。

        Args:
            content: 待检测内容

        Returns:
            检测结果
        """
        result = IdentityDetectionResult()

        if not content or len(content.strip()) == 0:
            return result

        # 1. 手机号检测
        self._detect_phone(content, result)

        # 2. 微信号检测
        self._detect_wechat(content, result)

        # 3. QQ号检测
        self._detect_qq(content, result)

        # 4. 身份证号检测
        self._detect_id_card(content, result)

        # 5. 银行卡号检测
        self._detect_bank_card(content, result)

        # 6. 邮箱检测
        self._detect_email(content, result)

        # 7. 住址检测
        self._detect_address(content, result)

        # 8. 公司+职位检测
        self._detect_company_position(content, result)

        # 9. 真实姓名检测
        self._detect_real_name(content, result)

        # 生成综合提醒文案
        if result.has_warning:
            result.warning_message = result.get_warning_message()
            logger.info(
                "[IdentityDetector] 检测到可识别信息，类型数: %d，"
                "检测项: %s",
                len(result.detections),
                ", ".join(d.info_type.value for d in result.detections),
            )

        return result

    # =========================================================================
    # 具体检测方法
    # =========================================================================

    def _detect_phone(self, content: str, result: IdentityDetectionResult) -> None:
        """检测手机号。"""
        for match in _PHONE_PATTERN.finditer(content):
            phone = match.group()
            # 简单校验：排除明显不是手机号的11位数字
            if phone.startswith("1") and len(phone) == 11:
                # 脱敏显示
                masked = phone[:3] + "****" + phone[7:]
                result.add_detection(IdentityDetection(
                    info_type=IdentityInfoType.PHONE_NUMBER,
                    matched_text=masked,
                    position=match.start(),
                    confidence=0.9,
                    suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.PHONE_NUMBER],
                ))

    def _detect_wechat(self, content: str, result: IdentityDetectionResult) -> None:
        """检测微信号。"""
        for match in _WECHAT_PATTERN.finditer(content):
            wechat_id = match.group(1)
            # 脱敏显示
            if len(wechat_id) > 3:
                masked = wechat_id[:2] + "***" + wechat_id[-1:]
            else:
                masked = "***"
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.WECHAT_ID,
                matched_text=masked,
                position=match.start(),
                confidence=0.85,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.WECHAT_ID],
            ))

    def _detect_qq(self, content: str, result: IdentityDetectionResult) -> None:
        """检测QQ号。"""
        for match in _QQ_PATTERN.finditer(content):
            qq = match.group(1)
            # 脱敏显示
            masked = qq[:2] + "***" + qq[-2:] if len(qq) > 4 else "***"
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.QQ_NUMBER,
                matched_text=masked,
                position=match.start(),
                confidence=0.8,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.QQ_NUMBER],
            ))

    def _detect_id_card(self, content: str, result: IdentityDetectionResult) -> None:
        """检测身份证号。"""
        for match in _ID_CARD_PATTERN.finditer(content):
            id_card = match.group()
            # 脱敏显示
            masked = id_card[:6] + "********" + id_card[-4:]
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.ID_CARD,
                matched_text=masked,
                position=match.start(),
                confidence=0.95,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.ID_CARD],
            ))

    def _detect_bank_card(self, content: str, result: IdentityDetectionResult) -> None:
        """检测银行卡号。"""
        for match in _BANK_CARD_PATTERN.finditer(content):
            card = match.group(1)
            # 脱敏显示
            masked = card[:4] + "****" + card[-4:] if len(card) > 8 else "****"
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.BANK_CARD,
                matched_text=masked,
                position=match.start(),
                confidence=0.9,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.BANK_CARD],
            ))

    def _detect_email(self, content: str, result: IdentityDetectionResult) -> None:
        """检测邮箱地址。"""
        for match in _EMAIL_PATTERN.finditer(content):
            email = match.group()
            # 脱敏显示
            at_idx = email.index("@")
            if at_idx > 2:
                masked = email[:2] + "***" + email[at_idx:]
            else:
                masked = "***" + email[at_idx:]
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.EMAIL,
                matched_text=masked,
                position=match.start(),
                confidence=0.85,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.EMAIL],
            ))

    def _detect_address(self, content: str, result: IdentityDetectionResult) -> None:
        """检测住址信息。"""
        for match in _ADDRESS_PATTERN.finditer(content):
            addr = match.group(1)
            # 脱敏显示：只保留省市级别
            if len(addr) > 6:
                masked = addr[:6] + "***"
            else:
                masked = addr[:3] + "***"
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.ADDRESS,
                matched_text=masked,
                position=match.start(),
                confidence=0.75,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.ADDRESS],
            ))

    def _detect_company_position(self, content: str, result: IdentityDetectionResult) -> None:
        """检测公司+职位组合。"""
        for match in _COMPANY_POSITION_PATTERN.finditer(content):
            company = match.group(1)
            position = match.group(2)
            # 脱敏显示
            masked_company = company[:2] + "***公司" if len(company) > 4 else "***公司"
            result.add_detection(IdentityDetection(
                info_type=IdentityInfoType.COMPANY_POSITION,
                matched_text=f"{masked_company} {position}",
                position=match.start(),
                confidence=0.8,
                suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.COMPANY_POSITION],
            ))

        # 单独出现公司名
        if not result.detections or not any(
            d.info_type == IdentityInfoType.COMPANY_POSITION
            for d in result.detections
        ):
            for match in _COMPANY_ALONE_PATTERN.finditer(content):
                company = match.group(1)
                masked = company[:2] + "***公司" if len(company) > 4 else "***公司"
                result.add_detection(IdentityDetection(
                    info_type=IdentityInfoType.COMPANY_POSITION,
                    matched_text=masked,
                    position=match.start(),
                    confidence=0.7,
                    suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.COMPANY_POSITION],
                ))

    def _detect_real_name(self, content: str, result: IdentityDetectionResult) -> None:
        """检测真实姓名。

        策略：
        1. 显式声明："我叫张三"、"我是张三"
        2. 姓氏 + 2-3字名 + 非姓名上下文排除
        """
        # 1. 显式声明检测（高置信度）
        for match in _NAME_EXPLICIT_PATTERN.finditer(content):
            name = match.group(1)
            # 排除常见非姓名词汇
            if name in ("开心", "难过", "很好", "不错", "可以", "这样",
                        "什么", "那个", "这个", "自己", "别人", "大家"):
                continue

            # 检查姓氏
            surname = name[0]
            if surname in _COMMON_SURNAMES:
                # 脱敏显示
                masked = surname + "**"
                result.add_detection(IdentityDetection(
                    info_type=IdentityInfoType.REAL_NAME,
                    matched_text=masked,
                    position=match.start(),
                    confidence=0.9,
                    suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.REAL_NAME],
                ))

        # 2. 隐式姓名检测（中置信度）
        # 检测 "小X"、"老X" + 姓氏的模式
        name_prefix_pattern = re.compile(r'[小老阿]\s*([\u4e00-\u9fa5])')
        for match in name_prefix_pattern.finditer(content):
            char = match.group(1)
            if char in _COMMON_SURNAMES:
                # 可能是称呼，低置信度
                masked = match.group()[0] + "*"
                result.add_detection(IdentityDetection(
                    info_type=IdentityInfoType.REAL_NAME,
                    matched_text=masked,
                    position=match.start(),
                    confidence=0.5,
                    suggestion=_INFO_TYPE_SUGGESTIONS[IdentityInfoType.REAL_NAME],
                ))


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_identity_detector() -> IdentityDetector:
    """创建脱敏提醒服务实例。

    Returns:
        IdentityDetector 实例
    """
    return IdentityDetector()
