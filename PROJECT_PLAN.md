# 个人知识库开发计划

## 1. 目标

本项目的目标不是做一个通用型笔记库，而是做一个面向正式写作的知识证据系统。

核心链路：

```text
文档导入 -> blocks -> Knowledge Objects -> slot 检索编排 -> 裁决 -> EvidenceBundle
```

其中：

- `Block` 解决“材料在哪里”
- `Fact` 解决“写什么事实”
- `Expression` 解决“怎么说”
- `Experience` 解决“哪些历史做法在当前条件下还能继续使用”
- `EvidenceBundle` 解决“按写作 slot 输出什么证据和裁决结果”

---

## 2. 当前约束与调整

公司内部已有现成的知识库与向量召回接口，因此当前阶段不重点建设完整自研检索基础设施。

当前策略调整为：

- 保留检索层的统一接口
- 先用本地简化实现跑通链路
- 后续再接入公司内部知识库/向量召回接口
- 先把知识组织、裁决逻辑、EvidenceBundle 结构做稳定

因此，当前最小业务闭环为：

```text
文档导入 -> blocks -> KO 抽取 -> slot 检索编排 -> 简化召回 -> 裁决 -> EvidenceBundle
```

---

## 3. 核心设计

### 3.1 Knowledge Objects

#### Fact

用于沉淀可直接写入正式材料的客观事实。

最小字段：

- `k_id`
- `k_type = fact`
- `canonical`
- `time`
- `evidence`
- `confidence`

#### Expression

用于约束正式写作中的表达口径。

当前阶段只做轻量版：

- 人工维护少量 canonical expressions
- 按 topic 或 task_type 提供给生成阶段

后续再升级为 bootstrap expression library。

#### Experience

用于表达历史做法、机制、措施，以及其是否适用于当前任务。

当前阶段先抽取：

- `condition`
- `action`
- `evidence`

后续再增加 grounding、validity、issue/measure/outcome linkage。

---

## 4. 当前阶段的技术取舍

### 4.1 优先做

- 文档导入与解析
- `blocks` 数据结构
- `Fact` 抽取
- `Experience` 抽取
- `slot -> filters` 编排
- EvidenceBundle 结构定义
- 检索适配层抽象
- 本地简化 retriever

### 4.2 暂缓做

- 自建 `pgvector`
- 自建 BM25 / hybrid retrieval
- 完整 `PageIndex-A / PageIndex-B`
- `doc_tree` 长文树索引
- 完整 `Expression` 资产治理
- 高复杂度 rerank

这些能力后续都可以补，但不应阻塞第一版闭环。

---

## 5. 分阶段开发计划

### Phase 0：工程骨架

目标：项目可启动、目录清晰、便于后续迭代。

计划内容：

- 建立基础目录结构
- 建立 API 入口
- 建立公共配置、日志、ID 工具
- 建立最小数据模型定义
- 准备样例数据目录
- 明确后续模块边界

建议目录：

```text
apps/
  api/
offline_pipeline/
  parse/
  extract/
online_runtime/
  retrieval/
  decision/
  export/
libs/
  common/
data/
  samples/
  exports/
docs/
```

---

### Phase 1：离线最小链路

目标：把文档稳定转成结构化 blocks 和基础 KO。

计划内容：

- 本地文件导入
- `PDF/DOCX -> blocks`
- 解析 `doc_id / page_no / heading_path / order / text`
- 实现 `Fact` 抽取
- 实现 `Experience` 抽取
- `Expression` 先用手工维护的小型配置表

阶段产物：

- `blocks.json` 或等价持久化结果
- `facts.json`
- `experiences.json`

---

### Phase 2：检索适配层

目标：让上层业务逻辑不依赖具体检索实现。

计划内容：

- 定义统一 Retriever 接口
- 实现 `LocalRetriever`
- 预留 `CompanyRetriever`
- 支持 `query + filters + top_k` 方式调用

建议接口：

```python
retrieve_blocks(query: str, filters: dict, top_k: int)
retrieve_kos(query: str, filters: dict, top_k: int)
```

说明：

- `LocalRetriever` 只要求简单可跑通
- `CompanyRetriever` 后续用于接公司内部知识库与向量召回接口

---

### Phase 3：在线编排与 EvidenceBundle

目标：跑通按写作 slot 输出证据包的核心链路。

计划内容：

- 定义 `slot schema`
- 实现 `slot -> filters`
- 调用 retriever 获取候选 blocks / KOs
- 实现 `object_judge`
- 实现 `validity_checker`
- 实现 `evidence_selector`
- 导出 `EvidenceBundle`

这一阶段的完成标准：

- 输入一个写作任务
- 输入一组 outline / slots
- 输出按 slot 组织的 EvidenceBundle

---

### Phase 4：增强能力

目标：在不推翻主链路的前提下逐步增强效果。

增强项候选：

- 接入公司内部知识库接口
- 接入公司内部向量召回接口
- 增加更丰富的 metadata/filter
- 增加 rerank
- 增加 `Experience grounding`
- 增加 `Expression bootstrap library`
- 增加 `PageIndex-A/B` 的工程化实现
- 增加 `doc_tree` 用于长文范围定位

---

## 6. 当前里程碑

第一阶段的验收目标收敛为以下三项：

1. 导入样例文档后，能够生成 `blocks + facts + experiences`
2. 给定任务与 outline 后，能够输出按 slot 组织的 `EvidenceBundle`
3. 检索层可以在 `LocalRetriever` 与未来的 `CompanyRetriever` 之间切换

---

## 7. 接下来立即执行的事项

按优先级排序：

1. 初始化项目目录结构
2. 建立最小 Python 工程入口
3. 定义核心数据结构：`Block`、`Fact`、`Experience`、`Slot`、`EvidenceBundle`
4. 实现最小 parser
5. 实现最小 extractor
6. 实现 retriever 抽象与本地简化版
7. 实现 EvidenceBundle 生成

---

## 8. 记录规则

这份文档作为长期维护的项目计划文件使用。

后续若有新的想法、设计调整、接口约束、阶段变化，统一追加到本文件中，建议按以下方式维护：

- 新增一个带日期的小节
- 写明“变更原因”
- 写明“影响范围”
- 写明“是否影响当前开发顺序”

建议格式：

```text
## YYYY-MM-DD 更新

### 变更
- ...

### 原因
- ...

### 影响
- ...
```

## 2026-04-30 更新

### 变更
- 已初始化 MVP 工程骨架
- 已创建最小 FastAPI 入口
- 已实现 `.md/.txt` 最小解析器
- 已实现 `Fact` / `Experience` 最小抽取
- 已实现 `LocalRetriever`
- 已预留 `CompanyRetriever` 占位
- 已实现最小 `EvidenceBundle` 导出链路

### 原因
- 先把核心业务闭环跑通，验证设计而不是提前建设重型基础设施

### 影响
- 当前仓库已经进入 Phase 0 到 Phase 3 的初始实现阶段
- 后续优先补的是解析能力、检索适配和裁决质量，而不是重建底层向量基础设施
