from dataclasses import dataclass


Color = tuple[float, float, float, float]
Point3D = tuple[float, float, float]


@dataclass(frozen=True)
class RenderSpec:
    fps: int = 24
    frame_start: int = 1
    frame_end: int = 120
    width: int = 1280
    height: int = 720
    entry_end: int = 20
    idle_start: int = 21

    @property
    def duration_seconds(self) -> float:
        return self.frame_end / self.fps


@dataclass(frozen=True)
class DeskSpec:
    id: str
    module: str
    title: str
    english: str
    role: str
    responsibility: str
    color: Color
    action: str
    props: tuple[str, ...]
    destination: str
    location: Point3D
    rotation_degrees: float
    card_side: str


DESKS = (
    DeskSpec(
        "a1", "A1 智能选题", "智能选题", "TOPIC PLANNING", "策划编辑",
        "聚合热点信号，形成可执行的报道方向。",
        (0.784, 0.063, 0.180, 1.0), "查看热点屏、移动选题卡",
        ("热点趋势屏", "选题卡"), "../../demo/pages/m1-topics.html",
        (-4.7, -0.6, 0.0), -72.0, "right",
    ),
    DeskSpec(
        "a2", "A2 智能采集", "智能采集", "SMART COLLECTION", "记者",
        "汇集现场采访、音视频与公开信源，整理可用素材。",
        (0.910, 0.459, 0.141, 1.0), "戴耳机、整理采访素材",
        ("耳机", "采访素材夹"), "../../demo/pages/m2-collection.html",
        (-2.8, 3.7, 0.0), -144.0, "right",
    ),
    DeskSpec(
        "a3", "A3 智能写作", "智能写作", "ASSISTED WRITING", "文字编辑",
        "组织事实与结构，协同生成并打磨新闻稿件。",
        (0.176, 0.549, 0.353, 1.0), "敲键盘、查看稿件",
        ("键盘", "稿件屏"), "../../demo/pages/m3-writing.html",
        (1.6, 4.2, 0.0), 156.0, "left",
    ),
    DeskSpec(
        "a4", "A4 智能审校", "智能审校", "SMART REVIEW", "审校编辑",
        "检查事实、语言与规范问题，确认修订结果。",
        (0.659, 0.196, 0.455, 1.0), "标记文本、确认问题",
        ("批注笔", "问题确认屏"), "../../demo/pages/m4-review.html",
        (5.0, 1.2, 0.0), 96.0, "left",
    ),
    DeskSpec(
        "a5", "A5 全渠道分发", "全渠道分发", "OMNICHANNEL DELIVERY", "运营编辑",
        "适配不同平台形态，编排并发布全渠道内容。",
        (0.831, 0.647, 0.078, 1.0), "切换多块平台屏幕",
        ("平台副屏", "发布控制键"), "../../demo/pages/m5-channels.html",
        (3.4, -3.4, 0.0), 30.0, "left",
    ),
    DeskSpec(
        "a6", "A6 效果洞察", "效果洞察", "IMPACT INSIGHTS", "数据分析师",
        "观察传播表现与受众反馈，提炼下一轮优化信号。",
        (0.082, 0.588, 0.647, 1.0), "查看图表和传播信号",
        ("图表屏", "传播信号柱"), "../../demo/pages/m6-insights.html",
        (-1.3, -4.2, 0.0), -12.0, "right",
    ),
)

HIT_REGION_NAME = "newsroom-hit-regions.json"
NEWSROOM_OUTPUT_NAMES = {
    "video": "newsroom.mp4",
    "cover": "newsroom-cover.png",
    "blend": "newsroom.blend",
    "hit_regions": HIT_REGION_NAME,
    "highlights": {
        desk.id: f"newsroom-{desk.id}-highlight.png" for desk in DESKS
    },
}


def validate_desks(desks: tuple[DeskSpec, ...]) -> list[str]:
    errors: list[str] = []
    if [desk.id for desk in desks] != [f"a{index}" for index in range(1, 7)]:
        errors.append("desk ids must be ordered a1 through a6")
    if len({desk.color for desk in desks}) != 6:
        errors.append("desk clothing colors must be unique")
    if len({desk.destination for desk in desks}) != 6:
        errors.append("desk destinations must be unique")
    if any(desk.card_side not in {"left", "right"} for desk in desks):
        errors.append("card_side must be left or right")
    if any(len(desk.props) < 2 for desk in desks):
        errors.append("each desk must define at least two role props")
    return errors


A1_ROLE = {
    "module": "A1 智能选题",
    "role": "策划编辑",
    "responsibility": "聚合热点信号，形成可执行的报道方向。",
    "color": (0.784, 0.063, 0.180, 1.0),
}

OUTPUT_NAMES = {
    "video": "sample.mp4",
    "cover": "sample-cover.png",
    "highlight": "sample-highlight.png",
}


def rgba_hex(color: tuple[float, float, float, float]) -> str:
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in color)
