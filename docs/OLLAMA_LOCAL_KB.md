# Ollama 与本地知识库说明

## 目标

在接公司内部知识库与向量召回接口之前，系统先具备一套自有的最轻量实现：

- 使用 Ollama 做 KO 抽取
- 使用 Ollama `/api/embed` 做本地向量
- 使用 JSON 文件落本地知识库
- 使用本地向量召回支撑 slot 检索

同时，这套实现从结构上必须是可替换的，而不是写死在主链路里。

## 当前实现

### 抽取

- 模块：[offline_pipeline/extract/ko_extractor.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/offline_pipeline/extract/ko_extractor.py>)
- 模式：`Ollama LLM first, rule fallback`
- provider 工厂：[libs/llm/factory.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/libs/llm/factory.py>)

输出三类对象：

- `facts`
- `experiences`
- `expressions`

### 向量

- 模块：[libs/embedding/embedder.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/libs/embedding/embedder.py>)
- 首选：`OllamaEmbedder`
- 兜底：`HashEmbedder`
- 选择方式：通过 provider/backend 配置，而不是主链路写死

### 本地知识库

- 模块：[online_runtime/retrieval/local_kb.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/local_kb.py>)
- 存储位置：`data/local_kb/{doc_id}.json`

索引内容包括：

- `blocks`
- `block_vectors`
- `knowledge_objects`
- `ko_vectors`
- `expressions`
- `expression_vectors`

### 模块化召回后端

- 抽象接口：[online_runtime/retrieval/backend.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/backend.py>)
- backend 工厂：[online_runtime/retrieval/factory.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/factory.py>)
- 组合检索器：[online_runtime/retrieval/composite_retriever.py](<C:/Users/vimdr/Desktop/CNPE/个人知识库/demo/online_runtime/retrieval/composite_retriever.py>)

当前 backend：

- `local_vector`
- `local_keyword`
- `company`（占位）

## 设计取舍

### 为什么先做本地知识库

因为在接公司检索接口之前，必须先有一条完整可验证的内部链路：

```text
文档 -> 抽取 -> 建索引 -> 检索 -> 裁决 -> bundle
```

否则后续即使接上公司接口，也很难判断问题出在抽取层、索引层还是检索层。

### 为什么必须模块化

因为当前环境和公司内网环境不一致：

- 本机可以使用 `ollama`
- 公司环境未必用 `ollama`
- 未来还会增加更多召回方式提升 robust

因此：

- 模型调用必须可配置 provider
- embedding 必须可配置 provider
- 检索必须是 backend 列表，而不是单个硬编码实现

### 为什么允许规则 fallback

当前原则不是“规则主导”，而是：

- LLM 负责主抽取
- 规则只在 LLM 失败、缺失或明显不稳定时辅助兜底

这符合当前项目的方向，也能避免 MVP 完全退化成规则系统。

## 后续演进

1. 抽取 prompt 按文类细化
2. 本地知识库支持跨文档聚合
3. 增加持久化元数据和更新时间
4. 在接口层切换到 `CompanyBackend`
5. 增加更多 backend，例如 rerank backend、结构化过滤 backend、外部搜索 backend
