# Knowledge Base Platform — Code Guidelines

## 1. Code Style & Formatting

### ESLint Configuration (root `.eslintrc.js`)

```js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: { project: ['./tsconfig.json', './apps/*/tsconfig.json'], ecmaVersion: 2022 },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/strict-type-checked',
    'prettier',
  ],
  plugins: ['@typescript-eslint', 'import'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': ['error', { allowExpressions: false }],
    '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
    '@typescript-eslint/no-floating-promises': 'error',
    'import/order': ['error', { 'newlines-between': 'always', alphabetize: { order: 'asc' } }],
    'no-console': 'error',
  },
};
```

### Prettier Configuration (`.prettierrc`)

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "endOfLine": "lf",
  "arrowParens": "always"
}
```

Prettier is run as an ESLint rule (`eslint-config-prettier` disables formatting rules; `eslint-plugin-prettier` is NOT used — run Prettier separately via Husky `pre-commit` hook).

---

## 2. TypeScript Conventions

- **Strict mode** enforced in all `tsconfig.json` files:
  ```json
  { "compilerOptions": { "strict": true, "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true, "noImplicitReturns": true } }
  ```
- **No `any`**: use `unknown` for truly unknown data and narrow with type guards. `@typescript-eslint/no-explicit-any` is set to `error`.
- **Explicit return types** on all exported functions and class methods — no return-type inference on public API.
- **Interface-first design**: use `interface` for all domain contracts and shapes; use `type` only for unions, intersections, conditional types, or mapped types.
- **No type assertions (`as T`)** except when bridging third-party libraries that return `unknown`. Every assertion must include a comment explaining why it is safe.

```typescript
// ✅ Correct — interface contract, explicit return type, no any
export interface ArticleSummary {
  id: string;
  title: string;
  slug: string;
  publishedAt: Date | null;
}

export function toSummary(article: Article): ArticleSummary {
  return {
    id: article.id,
    title: article.title,
    slug: article.slug,
    publishedAt: article.publishedAt ?? null,
  };
}

// ❌ Wrong — any kills type safety, missing return type
export function toSummary(article: any): any { /* ... */ }
```

---

## 3. NestJS Conventions

### 3.1 Module Structure

Every domain is a **self-contained NestJS feature module**. The layout is:

```
apps/api/src/
  modules/
    article/
      article.module.ts         ← imports TypeOrmModule, BullModule
      article.controller.ts
      article.service.ts
      article.repository.ts
      entities/
        article.entity.ts
        article-version.entity.ts
      dto/
        create-article.dto.ts
        update-article.dto.ts
        article-response.dto.ts
      __tests__/
        article.service.spec.ts
        article.e2e-spec.ts
    search/
    ai/
    auth/
  shared/
    database/      ← TypeORM DataSource, base repository
    redis/         ← Redis client provider
    queues/        ← BullMQ queue definitions
    guards/        ← JwtAuthGuard, RolesGuard
    interceptors/  ← ResponseTransformInterceptor, LoggingInterceptor
    filters/       ← AllExceptionsFilter
    decorators/    ← @CurrentUser(), @Roles()
```

**Shared services** (Redis, BullMQ, TypeORM DataSource) live in `SharedModule` and are globally
registered (`@Global()`). Feature modules **never import other feature modules** — cross-module
communication uses domain events (`EventEmitter2`) or shared service interfaces.

### 3.2 Controller Conventions

```typescript
@Controller({ path: 'articles', version: '1' })
@UseGuards(JwtAuthGuard, RolesGuard)
@UseInterceptors(ResponseTransformInterceptor)
@ApiTags('Articles')
export class ArticleController {
  constructor(private readonly articleService: ArticleService) {}

  @Post()
  @Roles(Role.EDITOR, Role.ADMIN)
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create a new article draft' })
  async createArticle(
    @Body() dto: CreateArticleDto,
    @CurrentUser() user: AuthUser,
  ): Promise<ArticleResponseDto> {
    return this.articleService.createArticle(dto, user.id);
  }

  @Get(':id')
  async getArticle(
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<ArticleResponseDto> {
    return this.articleService.getArticleById(id);
  }
}
```

Rules:
- Controllers handle **only** HTTP concerns: parse request, delegate to service, return DTO.
- All inputs validated globally via `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })`.
- Route parameters use inline pipe validators (`ParseUUIDPipe`, `ParseIntPipe`).
- All responses go through `ResponseTransformInterceptor` (wraps in `{ data, meta, timestamp }` envelope).
- Never access `req.body` directly — always use typed DTOs.

### 3.3 Service Conventions

- All **business logic** lives in services. Controllers contain zero business logic.
- Services are injected via constructor; never use `ModuleRef.get()` inside a service.
- Use **domain services** for cross-cutting orchestration: `PublicationService` coordinates
  `ArticleService`, `SearchService`, and `NotificationService` without any one importing the others.
- Services must not call `res.json()` or any HTTP-specific API — the sole exception is streaming
  responses where `res: Response` is passed explicitly and documented.

### 3.4 Repository Pattern

```typescript
@Injectable()
export class ArticleRepository {
  constructor(
    @InjectRepository(Article)
    private readonly repo: Repository<Article>,
    private readonly dataSource: DataSource,
  ) {}

  async findPublishedBySlug(slug: string): Promise<Article | null> {
    return this.repo.findOne({
      where: { slug, status: ArticleStatus.PUBLISHED },
      relations: ['author', 'collection', 'tags'],
    });
  }

  async saveWithVersion(article: Article, version: ArticleVersion): Promise<Article> {
    return this.dataSource.transaction(async (manager) => {
      const saved = await manager.save(Article, article);
      await manager.save(ArticleVersion, { ...version, articleId: saved.id });
      return saved;
    });
  }
}
```

- TypeORM `Repository<T>` injected via `@InjectRepository()` — never construct `new Repository()`.
- Raw SQL (`dataSource.query()`) is **only** permitted for performance-critical paths where the ORM
  query builder is insufficient (e.g., pgvector `<=>` operator). Every raw query must include a
  comment: `// Raw SQL: TypeORM QueryBuilder does not support pgvector operators.`
- **Always use transactions** for writes spanning multiple tables. Never call two sequential
  `repo.save()` calls outside a transaction.

### 3.5 Error Handling (RFC 7807)

```typescript
// shared/errors/app.exception.ts
export class AppException extends HttpException {
  constructor(
    public readonly code: ErrorCode,
    message: string,
    status: HttpStatus,
    public readonly details?: Record<string, unknown>,
  ) {
    super(
      { type: `https://kbp.io/errors/${code}`, title: message, status, details },
      status,
    );
  }
}

// Usage in service
if (!article) {
  throw new AppException(
    ErrorCode.ARTICLE_NOT_FOUND,
    'Article not found',
    HttpStatus.NOT_FOUND,
    { articleId: id },
  );
}
```

- All error codes are defined in `shared/errors/error-codes.enum.ts`.
- **Never** throw raw `Error` or `HttpException` from services — always use `AppException`.
- `AllExceptionsFilter` catches unhandled errors, maps them to RFC 7807 format, and logs with
  `error` severity including `correlationId`.

### 3.6 Logging (Structured, No PII)

```typescript
// ✅ Correct — structured, includes correlationId, no PII
this.logger.log({
  message: 'Article published',
  correlationId: cls.get('correlationId'),
  articleId: article.id,
  authorId: article.authorId,
});

// ❌ Wrong — logs PII (email), raw string
this.logger.log(`User ${user.email} published article`);
```

- Use `PinoLogger` (via `nestjs-pino`). Configure:
  ```ts
  redact: ['req.headers.authorization', 'req.headers.cookie', '*.password', '*.email', '*.token']
  ```
- Log levels: `error` for exceptions, `warn` for recoverable issues, `log` for business events,
  `debug` for diagnostic detail (disabled in production via `LOG_LEVEL=info`).
- Correlation ID is injected from `X-Correlation-ID` header (or generated as UUID v4) by
  `CorrelationIdMiddleware` and stored in `AsyncLocalStorage` for propagation without param threading.

### 3.7 Configuration Management

```typescript
@Injectable()
export class AppConfig {
  constructor(private readonly config: ConfigService) {}

  get dbHost(): string {
    return this.config.getOrThrow<string>('DB_HOST');
  }

  get openaiApiKey(): string {
    return this.config.getOrThrow<string>('OPENAI_API_KEY');
  }
}
```

- Use `ConfigService.getOrThrow<T>()` (not `.get()`) — fail fast at startup when required config is absent.
- Secrets (DB password, API keys, SAML certs) are loaded from AWS Secrets Manager via a bootstrap
  Lambda that injects them as env vars before ECS tasks start. **Never hardcode or commit secrets.**
- All supported environment variables must be documented in `.env.example` with descriptions and
  example values (never real values).

### 3.8 Testing

- **Unit tests** (`*.spec.ts`): mock all dependencies with `createMock<T>()`; test service logic in isolation.
- **Integration tests** (`*.int-spec.ts`): `TestingModule` with real TypeORM repo against a Docker test DB; reset DB between suites.
- **e2e tests** (`*.e2e-spec.ts`): Supertest against the full NestJS app; cover happy path and key error cases per endpoint.
- Minimum **80% line coverage** in CI: `jest --coverage --coverageThreshold='{"global":{"lines":80}}'`.
- Use `@faker-js/faker` for test data; define reusable factories in `test/factories/`.

---

## 4. Next.js Conventions

### 4.1 Server vs. Client Components Decision Matrix

| Requirement | Component Type |
|-------------|---------------|
| Fetch data at request time (DB/API) | Server Component |
| SEO-critical or static content | Server Component |
| Uses `useState`, `useEffect`, event handlers | `'use client'` |
| Browser APIs, heavy libs (TipTap, charts) | `'use client'` |
| Form with optimistic UI | `'use client'` + Server Action |

Default to Server Components. Add `'use client'` only at the lowest-level component that requires
it. Never pass class instances, functions, or Promises as props to Client Components.

### 4.2 Data Fetching Patterns

```typescript
// Server Action — for mutations
'use server';
export async function publishArticleAction(articleId: string): Promise<void> {
  const session = await getServerSession(authOptions);
  if (!session?.user) redirect('/login');
  await apiClient.post(`/v1/articles/${articleId}/publish`);
  revalidatePath(`/articles/${articleId}`);
}

// React Query — client-side data that changes frequently
export function useArticleSearch(query: string): UseQueryResult<SearchResultDto> {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () => searchArticles(query),
    staleTime: 30_000,
    enabled: query.length >= 2,
    placeholderData: keepPreviousData,
  });
}
```

### 4.3 TipTap Editor Integration

```typescript
'use client';
export function ArticleEditor({ content, onChange }: ArticleEditorProps): JSX.Element {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ codeBlock: false }),
      Image.configure({ HTMLAttributes: { class: 'article-image rounded-lg' } }),
      Link.configure({ openOnClick: false, autolink: true }),
      CodeBlockLowlight.configure({ lowlight }),
      Placeholder.configure({ placeholder: 'Start writing your article…' }),
      CharacterCount.configure({ limit: 100_000 }),
    ],
    content,
    onUpdate: ({ editor }) => onChange(editor.getJSON()),
    editorProps: {
      attributes: { class: 'prose prose-lg max-w-none focus:outline-none min-h-[400px]' },
    },
  });

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <EditorToolbar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
}
```

- Store article content as **TipTap JSON** (`editor.getJSON()`), not HTML.
- Render to HTML server-side for SEO pages using `generateHTML(contentJson, extensions)` from `@tiptap/html`.
- Image uploads: the `Image` extension's `addNodeView` intercepts the paste/drop event, uploads
  directly to S3 via presigned URL, and updates the image `src` to the CloudFront URL on success.

### 4.4 Tailwind CSS Conventions

```typescript
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ' +
  'disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary:   'bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800',
        secondary: 'bg-white text-gray-900 border border-gray-300 hover:bg-gray-50',
        ghost:     'text-gray-700 hover:bg-gray-100 hover:text-gray-900',
        danger:    'bg-red-600 text-white hover:bg-red-700',
      },
      size: {
        sm: 'h-8 px-3 text-sm gap-1.5',
        md: 'h-10 px-4 text-sm gap-2',
        lg: 'h-12 px-6 text-base gap-2',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps): JSX.Element {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
```

- Use `cva` for all component variants. **No inline `style` props** — Tailwind classes exclusively.
- Custom design tokens (brand palette, spacing scale, typography) live in `tailwind.config.ts`.
  Never hard-code color hex values in component files.
- `cn()` utility combines `clsx` + `tailwind-merge` for conditional class composition.
- `prose` class from `@tailwindcss/typography` is used for all article content rendering.

---

## 5. Database Conventions

- **Entity naming**: PascalCase class (`Article`), snake_case table (`articles`), snake_case columns (`created_at`, `author_id`).
- **Migration naming**: `YYYYMMDDHHMMSS_description.ts` — e.g., `20240115120000_add_embedding_column.ts`.
- **Never use `synchronize: true`** outside of ephemeral local sandboxes. Production uses explicit
  migrations only. The TypeORM `DataSource` config sets `synchronize: process.env.NODE_ENV === 'test'`.
- **Always use transactions** for writes that span multiple tables (see `saveWithVersion` example).
- **Indexes**: add `@Index()` for all foreign keys, all `WHERE`-clause columns, and all `ORDER BY`
  columns used by the application. Document the justifying query in the migration comment.
- **Soft deletes**: `@DeleteDateColumn()` on `articles`, `collections`, `users`. Hard delete is
  reserved exclusively for GDPR erasure requests and requires the `Owner` role.
- **UUID PKs**: all entities use `@PrimaryGeneratedColumn('uuid')`; enable `uuid-ossp` extension
  in the baseline migration (`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`).

---

## 6. API Conventions

- **Versioning**: URI versioning (`/v1/`, `/v2/`). Breaking changes always introduce a new version; deprecated versions return `Deprecation: true` and `Sunset` headers.
- **Pagination**: cursor-based for large datasets; offset-based only for small admin lists (< 1 k rows).
  ```json
  { "data": [...], "meta": { "cursor": "eyJpZCI6IjEyMyJ9", "hasNextPage": true, "total": 1240 } }
  ```
- **Sorting/Filtering**: `?sort=createdAt:desc` and `?filter[status]=published` — whitelist all accepted keys; reject unknowns with 400.
- **Error format** (RFC 7807):
  ```json
  { "type": "https://kbp.io/errors/ARTICLE_NOT_FOUND", "title": "Article not found", "status": 404 }
  ```

---

## 7. Security Conventions

- **Input sanitization**: all TipTap HTML sanitized with `DOMPurify` server-side before persistence and rendering.
- **SQL injection**: TypeORM queries always use parameterized values; string interpolation in `dataSource.query()` is a critical violation.
- **Authentication**: validate JWT signature and expiry on every request; use RS256 (asymmetric key pair).
- **Authorization**: permissions checked at the **service layer**; guards are a first-pass filter only.
- **CORS**: whitelist origins explicitly; reject `*` in non-local environments.
- **Rate limiting**: 100 req/min global per IP; 20 req/min AI endpoints; 10 req/min auth endpoints via `ThrottlerModule` + Redis.
- **Helmet**: `helmet()` enabled globally — CSP, HSTS, X-Frame-Options.

---

## 8. Git Conventions

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<ticket>-<short-desc>` | `feature/KB-142-tiptap-image-upload` |
| Bug fix | `fix/<ticket>-<short-desc>` | `fix/KB-201-search-empty-query` |
| Chore / dependency | `chore/<desc>` | `chore/upgrade-nestjs-10` |
| Release | `release/<semver>` | `release/1.4.0` |
| Hotfix | `hotfix/<ticket>-<desc>` | `hotfix/KB-310-auth-token-leak` |

### Commit Messages (Conventional Commits)

```
feat(articles): add version history restore endpoint

Adds POST /v1/articles/:id/versions/:versionId/restore which creates
a new draft from the specified historical snapshot. The current draft
is saved as a version before restoration.

Closes KB-145
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `revert`.

Breaking changes: append `!` after type/scope and include `BREAKING CHANGE:` footer.

### PR Requirements

PRs must include: **Summary**, **Linked ticket**, **Type of change** (feat/fix/chore),
**Test plan** (how you verified it), **Screenshots** for UI changes, **Migration steps**
for schema changes, and a **Rollback plan** for any infra or schema change.
Minimum 2 reviewer approvals required; the PR author cannot approve their own PR.

---

## 9. Code Review Checklist

- [ ] Code compiles with zero TypeScript errors in strict mode
- [ ] All exported functions and class methods have explicit return types
- [ ] No `any` types; no unsafe type assertions without a justifying comment
- [ ] All inputs validated with DTOs and `class-validator` decorators
- [ ] Business logic is in the service layer, not the controller
- [ ] All service methods covered by unit tests (mock dependencies)
- [ ] Transactions used for all multi-table writes
- [ ] New DB columns have appropriate indexes; migration tested up and down
- [ ] No N+1 queries — checked with query logging or `EXPLAIN ANALYZE`
- [ ] All error cases handled and mapped to correct HTTP status codes via `AppException`
- [ ] No PII in any log statement; `correlationId` present in all structured logs
- [ ] No hardcoded secrets, config values, or environment-specific URLs
- [ ] Input HTML sanitized with DOMPurify before persistence
- [ ] Permissions checked at service layer (not just guards)
- [ ] OpenAPI spec updated for new or changed endpoints
- [ ] Feature flag used for any incomplete or experimental feature
- [ ] All async operations have error handling (no unhandled Promise rejections)
- [ ] New environment variables documented in `.env.example`
- [ ] PR scope is focused (single concern per PR)
- [ ] Rollback plan included for DB migrations or infra changes
- [ ] Accessibility: no new critical axe-core violations in affected UI

---

## 10. Performance Guidelines

**N+1 Prevention**
Always eager-load required relations in the initial query using `relations` option or
`QueryBuilder.leftJoinAndSelect`. For endpoints that load a variable number of related entities
per item, implement the `DataLoader` pattern to batch SQL `IN (...)` queries.

```typescript
// ✅ Correct — single query with join
const articles = await repo.find({ relations: ['author', 'tags'] });

// ❌ Wrong — N+1 (one query per article to load author)
const articles = await repo.find();
for (const a of articles) { a.author = await userRepo.findOneBy({ id: a.authorId }); }
```

**Index Usage**
Run `EXPLAIN (ANALYZE, BUFFERS)` on all new queries during development. Any query that shows
`Seq Scan` on a table with > 10,000 rows requires either an index or a documented justification.
Composite indexes must be ordered with the highest-selectivity column first.

**Caching Strategy**

| Data | Cache | TTL | Invalidation |
|------|-------|-----|--------------|
| Published article content | Redis | 5 min | Article publish/update |
| Search results (query hash) | Redis | 60 s | Article index update |
| User permissions | Redis | 30 s | Role/ACL change |
| Collection tree | Redis | 2 min | Collection create/move/delete |

**Pagination**: all list endpoints enforce a maximum `limit` of 100 rows. Background jobs processing
all articles must use cursor-based batching (1,000 rows/batch).

**Bundle Size**: analyzed in CI with `@next/bundle-analyzer`. No new dependency > 50 KB gzipped
without team approval. Prefer `next/dynamic` for heavy Client Components not needed on initial load.

---

## 11. Operational Policy Addendum

### 11.1 Content Governance Policies

All code that implements content workflows (article CRUD, publication state machine, version
history) must enforce the following invariants: articles cannot be published without an assigned
author, a non-empty title, and a non-empty `contentText`. Bulk-import or bulk-publish scripts
require two-engineer review and Tech Lead approval. Content deletion is always soft-delete;
hard-delete functions are restricted to the Owner role and must log an audit entry before execution.

### 11.2 Reader Data Privacy Policies

No analytics tracking code, event pixels, or third-party telemetry scripts may be added to the
reader-facing application without a documented privacy review. All analytics instrumentation must
use the internal `AnalyticsService` abstraction — no direct calls to third-party SDKs from
component code. Search query text must never appear in exception tracking payloads (Sentry,
Datadog APM) or error log messages. Components that render user-generated content must always pass
output through the server-side `DOMPurify` sanitizer before rendering.

### 11.3 AI Usage Policies

LangChain chain configurations — prompt templates, retrieval parameters, and model settings — are
code artifacts stored in the repository under version control, not in database configuration tables.
Changes to prompt templates require a PR reviewed by at least one engineer with AI/ML expertise.
Prompt templates must always instruct the model to cite sources and to explicitly acknowledge when
context is insufficient, and must never instruct the model to claim certainty beyond what the
retrieved context supports. The `EmbeddingService` must never store raw query text in a way that
is linkable to individual user identity.

### 11.4 System Availability Policies

Any change that modifies a TypeORM entity or migration file must be deployed with a canary
strategy: update 10% of ECS tasks, monitor for 15 minutes, then proceed with full rollout.
Migrations must be backward-compatible with the running application version. If a migration cannot
be made backward-compatible, it must be decomposed into a multi-phase sequence: (1) add nullable
column, (2) deploy new app version, (3) backfill data, (4) make column non-nullable, (5) remove
old column. Circuit breakers must be configured for all external service calls (OpenAI, Elasticsearch,
Redis) using `opossum`; fallback functions must be integration-tested and rehearsed quarterly.
