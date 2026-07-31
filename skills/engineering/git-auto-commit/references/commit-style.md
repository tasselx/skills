# Commit Style Reference

Use this reference when writing the commit message. User preference here: **detailed by default** (subject + body). Still respect an existing repository style if recent history clearly uses subject-only and the user has not asked for detail.

## Priority

1. Explicit user preference (this skill prefers detailed messages).
2. Existing repository style from recent commits (scopes, type names, emoji).
3. Default detailed bilingual conventional style below.

## Types

- `feat`: new user-facing capability.
- `fix`: bug fix or behavior correction.
- `refactor`: internal restructuring without behavior change.
- `perf`: performance improvement.
- `docs`: documentation-only change.
- `test`: test-only change.
- `build`: build system or dependency change.
- `ci`: CI workflow change.
- `chore`: maintenance change that does not fit the above.

## Scope

Choose the scope from:

1. Existing scopes in `git log --oneline -20`.
2. Changed top-level directory or package.
3. Feature module name.
4. Architecture layer such as `network`, `auth`, `ui`, `build`, or `deps`.

Use no scope only when the repository commonly omits scopes.

## Subject

Use mixed Chinese-English naturally: Chinese for the description, English for technical terms, API names, and keywords. No need for a separate English translation.

```text
feat(payment): 增加 Stripe 订阅支付流程
fix(auth): 修复 Token 过期导致 401 问题
refactor(network): 重构 HTTP interceptor 层
```

Keep the subject concise, searchable, and without a trailing period. Subject summarizes intent; details go in the body.

## Body (default: required)

**Prefer a body for almost every non-trivial commit.** Goal: a reviewer can understand the change from the message alone without reading the full diff.

Include a body when any of these are true (almost always):

- More than one logical change point in the diff.
- New or renamed functions / methods / types / APIs.
- Behavior, edge-case, or constraint changes.
- Multi-file or multi-module work with one coherent intent.
- Migration, breaking change, or manual follow-up.
- Important behavior that is not fully obvious from the subject.

Skip the body only when the entire change is a trivial one-liner and the subject already states it completely (typo fix, comment-only, pure whitespace/format, single-value config bump).

### Body style

- 2–8 short bullets after a blank line under the subject.
- Each bullet is one change point: what + why (if non-obvious).
- Use concrete symbols from the diff (method names, flags, constants, params).
- Do not narrate routine file paths (`改了 a.dart 和 b.dart`).
- Do not paste huge code blocks.
- Order bullets by importance (user-facing / behavior first, helpers last).

### Body template

```text
type(scope): 中英文混排一句话概述

- 核心行为或能力变化
- 关键新增/修改的 API、方法或状态
- 约束、限流、边界或兼容处理（如有）
- 重构或替换（如用工具方法替换 magic number）
```

## Examples

### Trivial (subject only — rare)

```text
fix(auth): 修正登录页文案错别字
```

### Simple fix (still with body)

```text
fix(gift): 修复 multiType=3 时送礼接收者昵称展示

- multiType=3 分支下接收者昵称未正确取自目标用户字段
- 统一昵称回退逻辑，避免展示为空或展示成送礼者昵称
```

### Feature / multi-point change (detailed body)

```text
feat(fishing): 新增拖拽连发与子弹速率限制，优化 TriggerEvent 事件处理

- 新增 onPanUpdate/onPanEnd/onPanCancel 拖拽连发机制
- 新增 _startHoldFire/_stopHoldFire 连发控制逻辑
- 新增 _canAddBullet 子弹速率限制（基于自瞄间隔）
- 新增 pauseCallback 支持自瞄暂停时停止连发
- 重构 _handleTriggerEvent 传入 cannonLevel 参数
- 新增 FishUtil 工具方法：isEventGunLevel、isBossFishLevel、goldFishLevelByGun 等
- 替换硬编码鱼等级 magic number 为 FishUtil 方法调用
```

### Breaking change

```text
feat(api)!: 重构用户认证接口

BREAKING CHANGE: 移除 /v1/auth/legacy 端点，统一使用 /v2/auth/oauth
- 移除 LegacyAuthProvider 类
- 新增 OAuthProvider 作为默认认证方式
- 迁移指南见 docs/migration/auth-v2.md
```

### Multi-module feature

```text
feat(payment): 增加 Stripe 订阅支付流程

- 新增 SubscriptionPlan 模型与数据库迁移
- 接入 Stripe 支付网关
- 添加订阅状态 webhook 处理
- 前端订阅管理页面待后续实现
```
