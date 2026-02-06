# AI 撰写模式实现计划

## 需求概述

新增"AI撰写模式"，让 AI 不再只是推送新闻链接列表，而是用更易消化的方式综合讲述当天的重要新闻，减少用户阅读负担。

## 示例输出

```
📰 今日要闻速览

【中美关系】
习近平与特朗普今日通话，聚焦贸易与防务议题。双方就关税问题
交换意见，特朗普政府释放缓和信号——财长贝森特承认此前"关税
导致通胀"的判断有误。

【美伊博弈】
美伊核谈判出现变数。伊朗希望更改会谈地点，美方拒绝，谈判
濒临破裂。原定2月6日在阿曼举行的会谈能否如期进行存疑。

【市场动态】
美股科技板块重挫：纳指跌2.29%，半导体指数暴跌超6%，AMD
单日跌超17%。与此同时，欧洲化工板块创4年最大单日涨幅。
```

## 实现阶段

### Phase 1: 配置扩展 ✅
- [x] 修改 `config/analysis_config.yaml` 添加 ai_writing 配置

### Phase 2: AI 撰写器模块 ✅
- [x] 新建 `app/ai/news_writer.py`
- [x] 实现 `AINewsWriter` 类

### Phase 3: 渲染器扩展 ✅
- [x] 修改 `app/notification/renderer.py` 添加摘要渲染函数

### Phase 4: 发送流程集成 ✅
- [x] 修改 `app/notification/important_news_sender.py` 集成 AI 撰写

### Phase 5: 配置加载器更新 ✅
- [x] 修改 `app/utils/config_loader.py` 加载新配置

## 文件变更清单

| 操作 | 文件 | 状态 |
|------|------|------|
| 修改 | `config/analysis_config.yaml` | ✅ |
| 新建 | `app/ai/news_writer.py` | ✅ |
| 修改 | `app/notification/renderer.py` | ✅ |
| 修改 | `app/notification/important_news_sender.py` | ✅ |
| 修改 | `app/utils/config_loader.py` | ✅ |

## 使用方法

在 `config/analysis_config.yaml` 中启用 AI 撰写模式：

```yaml
ai_writing:
  enabled: true                    # 设为 true 启用
  style: "news_anchor"             # 风格：news_anchor/analyst/brief
  max_news_per_digest: 50          # 每次最多处理新闻数
  output_language: "zh"            # 输出语言
  include_sources: true            # 是否附上来源链接
  group_by_topic: true             # 是否按主题分组
```

## 进度跟踪

- 开始时间: 2026-02-04
- 完成时间: 2026-02-04
- 当前状态: ✅ 已完成
- 完成阶段: 5/5
