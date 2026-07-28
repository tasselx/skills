# Commit Style Reference

Use this reference when the repository history does not already make the style obvious.

## Priority

1. Existing repository style from recent commits.
2. Explicit user preference.
3. Default bilingual conventional style.

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

Use Chinese first, followed by short English technical keywords:

```text
feat(payment): 增加订阅支付流程 Subscription Payment Flow
fix(auth): 修复 Token 过期问题 Token Expiration Fix
refactor(network): 重构请求层结构 Network Layer Refactor
```

Keep the subject concise, searchable, and without a trailing period.

## Body

Skip the body for simple changes.

Add a body when the commit includes:

- Multiple modules with one coherent intent.
- Migration or manual follow-up.
- Breaking change or public API change.
- Important behavior that is not obvious from the subject.

Use short bullets in the body; do not narrate routine file lists.

## Body Examples

Simple change (subject only, no body):

```text
fix(auth): 修复 Token 过期问题 Token Expiration Fix
```

Breaking change with body:

```text
feat(api)!: 重构用户认证接口 Refactor Auth API

BREAKING CHANGE: 移除 /v1/auth/legacy 端点，统一使用 /v2/auth/oauth
- 移除 LegacyAuthProvider 类
- 新增 OAuthProvider 作为默认认证方式
- 迁移指南见 docs/migration/auth-v2.md
```

Multi-module change with body:

```text
feat(payment): 增加订阅支付流程 Subscription Payment Flow

- 新增 SubscriptionPlan 模型与数据库迁移
- 接入 Stripe 支付网关
- 添加订阅状态 webhook 处理
- 前端订阅管理页面待后续实现
```
