# M0 生产流水线分镜素材

布局壳：`demo/assets/app.js` + `styles.css`。

- 墨线框 = `.storyboard-art` 边框，与 PNG 同盒对齐
- 仅 `breakout: true` 的帧（A3、A5）在框外叠装饰，其余裁切在框内
- 标题默认显示，职责句悬停出现

## PNG

透明底手绘风；出框装饰由 CSS `.storyboard-deco` 绘制，勿在 PNG 里再画一套框线。

| 文件 | 模块 |
|------|------|
| `a1-topics.png` | A1 智能选题 |
| `a2-collection.png` | A2 智能采集 |
| `a3-writing.png` | A3 智能写作 |
| `a4-review.png` | A4 智能审校 |
| `a5-channels.png` | A5 全渠道分发 |
| `a6-insights.png` | A6 效果洞察 |

替换：覆盖同名 PNG（建议透明底，主体略超出中心安全区以便出框）。
