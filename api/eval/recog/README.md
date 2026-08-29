# 识别评测图（8 张）

仓库不提交 JPEG（GitHub 文本推送会损坏二进制）。本地可把图放到本目录，文件名如下。
每项取 Drive 上最大的那份。

| 题号 | 本地文件 | Drive file id | 金标知识点 |
|------|----------|---------------|------------|
| 01 | recog-01-print-perfect-square.jpg | 10FGl-GPDHVHG3lPtVTjeub37dJmqRTEL | poly.perfect-square |
| 06 | recog-06-hand-factor.jpg | 1xPuPeRH0WK03_Rr4GGLEPJSdP8nrOrql | poly.common-factor |
| 12 | recog-12-print-radical.jpg | 179v37gayKoiz0S9GnGifm-obFOoOCNmr | rad.abs |
| 14 | recog-14-hand-rationalize.jpg | 1TJf1VAWDCqUQ6473qeaT2zFxHYYLuRl7 | rad.rationalize |
| 18 | recog-18-print-SSA.jpg | 1SLy9SqlE7iSjviKmRH6oraxEnAww1gxh | cong.ssa |
| 20 | recog-20-hand-SAS.jpg | 13ogfjlPSSinVEteyZ4J6GaS5I21VQBuJ | cong.sas |
| 21 | recog-21-hand-equilateral.jpg | 1fKIZW0FtdiLSBXsMvjArub_nN_x9-jba | tri.equilateral |
| 23 | recog-23-print-pythagoras.jpg | 1uBoELkck13sybDVdMNIw67YoL_ro0L06 | pyg.converse |

题 21 用 14KB 的新图（id `1fKIZW0FtdiLSBXsMvjArub_nN_x9-jba`）。
有 `DASHSCOPE_API_KEY` 且本目录有图时，`pytest api/eval/test_ingest.py` 会对每张 POST `/ingest`。
