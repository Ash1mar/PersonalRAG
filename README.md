# 个人知识库 MVP

当前版本目标是尽快跑通最小业务闭环：

```text
文档导入 -> blocks -> 可配置 LLM KO 抽取 -> 可配置检索后端建索引 -> 可组合召回 -> slot 检索编排 -> 裁决 -> EvidenceBundle
```

## 当前范围

- 支持本地文本类文件解析：`.md`、`.txt`
- 支持 `Fact` / `Experience` / `Expression` 的 LLM 优先抽取
- 规则抽取只作为 LLM 失败时的辅助 fallback
- 支持模块化模型提供者，当前实现为 `ollama`
- 支持模块化召回后端，当前实现为 `local_vector`、`local_keyword`
- 支持本地轻量知识库落盘：`data/local_kb/*.json`
- 支持可组合召回与 `CompositeRetriever`
- 支持基于 `slot` 的 EvidenceBundle 输出
- 已预留公司检索适配器，但当前默认先使用自建本地知识库

## 快速启动

安装依赖：

```bash
python -m pip install -e .
```

启动 API：

```bash
uvicorn apps.api.main:app --reload
```

可选环境变量：

```bash
PKB_CHAT_PROVIDER=ollama
PKB_CHAT_MODEL=qwen2.5-coder:7b
PKB_EMBEDDING_PROVIDER=ollama
PKB_EMBEDDING_MODEL=qwen2.5-coder:7b
PKB_RETRIEVAL_BACKENDS=local_vector,local_keyword
PKB_OLLAMA_BASE_URL=http://localhost:11434
PKB_LOCAL_KB_DIR=./data/local_kb
```

访问：

- `GET /health`
- `POST /parse`
- `POST /extract`
- `POST /index`
- `POST /search`
- `POST /bundle`

## 当前实现

### 1. Ollama 优先抽取

- 统一抽取入口在 [offline_pipeline/extract/ko_extractor.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/offline_pipeline/extract/ko_extractor.py>)
- 对每个 block 调用配置好的 `chat provider`
- 用结构化 JSON schema 直接抽取 `facts / experiences / expressions`
- 当 LLM 返回空结果或调用失败时，再退回规则辅助

当前默认 provider：

- `ollama`

后续可继续增加：

- 公司内网模型网关
- OpenAI 兼容接口
- 其他本地或私有部署模型

### 2. 本地知识库与向量召回

- 本地知识库入口在 [online_runtime/retrieval/local_kb.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/local_kb.py>)
- 默认使用配置好的 `embedding provider` 生成向量
- 如果本地 embedding 失败，则自动退回哈希向量 fallback
- 索引文件会持久化到 `data/local_kb/`

### 3. 模块化召回后端

- 抽象入口在 [online_runtime/retrieval/backend.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/backend.py>)
- 工厂入口在 [online_runtime/retrieval/factory.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/factory.py>)
- 组合入口在 [online_runtime/retrieval/composite_retriever.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/composite_retriever.py>)

当前后端：

- `local_vector`：向量召回
- `local_keyword`：关键词召回
- `company`：占位，后续接公司接口

这意味着主链路已经不再依赖某一个固定召回实现，后续可以继续叠加更多 backend 提升 robust。

### 4. EvidenceBundle 链路

- 链路入口在 [online_runtime/export/bundle.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/export/bundle.py>)
- 当前流程是：

```text
parse -> extract_knowledge -> build local kb index -> retrieve -> judge -> EvidenceBundle
```

其中 `retrieve` 已经支持多 backend 组合。

## API 用法

### `POST /extract`

输入文档后返回：

- `document`
- `facts`
- `experiences`
- `expressions`
- `summary`

其中 `summary` 会说明当前使用的是 `ollama_llm_plus_fallback` 还是 `rules_fallback`。

### `POST /index`

为一份文档构建配置好的检索后端索引并持久化。

返回：

- `doc_id`
- `backend_results`
- `block_count`
- `knowledge_object_count`
- `expression_count`

### `POST /search`

对已构建的本地知识库做检索。

支持：

- `query`
- `top_k`
- `doc_id`（可选）
- `item_types`（可选，支持 `block` / `fact` / `experience` / `expression`）
- `retrieval_backends`（可选，覆盖默认后端列表）

## 目录

```text
apps/api                 FastAPI 入口
offline_pipeline/parse   文档解析
offline_pipeline/extract KO 抽取
online_runtime/retrieval 检索适配层
online_runtime/decision  裁决逻辑
online_runtime/export    EvidenceBundle 生成
libs/common              通用模型与工具
libs/llm                 Ollama 客户端
libs/embedding           向量封装
data/samples             样例数据
```

## 下一步

- 增加 PDF/DOCX 解析
- 收紧 `Fact / Experience / Expression` 的 prompt 与后处理
- 给本地知识库增加跨文档聚合与增量更新
- 接入真正的公司 retrieval backend
- 增加 Experience grounding
- 增加更强的 metadata/filter
