# 错题本 P0/P1

手机 PWA + FastAPI. 两屏：校对知识点、变式过关、系统分享练习卡。
无账号班级微信 SDK。api/ 后端与评测；web/ 前端。

## API

- `GET /tree` 冻结知识点树
- `GET /gold` 评测金标
- `POST /tag` 题干预打知识点
- `POST /variants` 同错因变式
- `POST /ingest` 拍题识别（multipart 字段名 `image`）

`POST /ingest` 调用 DashScope 兼容模式的 Qwen-VL，只抽题、不给答案。返回：

```json
{"stem":"...","options":null,"formula_tex":null,"has_figure":false,"knowledge_id":"..."}
```

环境变量：

- `DASHSCOPE_API_KEY` 必填，缺则 `/ingest` 返回 503
- `QWEN_VL_MODEL` 可选，默认 `qwen-vl-max`（也可用 `qwen2.5-vl-72b-instruct`）

摄像头 UI 仍等 8 张识别评测通过后再做。评测图 Drive id 见 `api/eval/recog/README.md`。
