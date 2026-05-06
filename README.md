# 个人知识库 MVP

当前版本目标是尽快跑通最小业务闭环：

```text
文档导入 -> blocks -> KO 抽取 -> slot 检索编排 -> 裁决 -> EvidenceBundle
```

## 当前范围

- 支持本地文本类文件解析：`.md`、`.txt`
- 支持最小 `Fact` / `Experience` 抽取
- 支持本地简化检索器 `LocalRetriever`
- 支持基于 `slot` 的 EvidenceBundle 输出
- 暂不接入公司内部知识库与向量召回接口

## 快速启动

安装依赖：

```bash
python -m pip install -e .
```

启动 API：

```bash
uvicorn apps.api.main:app --reload
```

访问：

- `GET /health`
- `POST /parse`
- `POST /extract`
- `POST /bundle`

## 目录

```text
apps/api                 FastAPI 入口
offline_pipeline/parse   文档解析
offline_pipeline/extract KO 抽取
online_runtime/retrieval 检索适配层
online_runtime/decision  裁决逻辑
online_runtime/export    EvidenceBundle 生成
libs/common              通用模型与工具
data/samples             样例数据
```

## 下一步

- 增加 PDF/DOCX 解析
- 接入 CompanyRetriever
- 增加 Experience grounding
- 增加更强的 metadata/filter

