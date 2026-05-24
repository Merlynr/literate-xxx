# XX甄选 Web 端

商家工作台（`/app`）+ 运营后台（`/admin`），对接 `python-bff` FastAPI。

## 开发

1. 确保 BFF 可访问（默认 `http://8.141.7.56:8000`，需 `DEBUG=true` 以使用 dev-login）。

2. 启动 Web（`.env.development` 已指向远程 BFF；也可用 `/api/v1` 走 Vite 代理）：

```bash
cd web-fe
npm install
npm run dev
```

3. 浏览器打开：

- 商家端：http://localhost:5173/app/login
- 运营端：http://localhost:5173/admin/login

## 环境变量

默认 `VITE_API_BASE_URL=http://8.141.7.56:8000/api/v1`。

若改回本地代理，在 `.env.development` 写 `VITE_API_BASE_URL=/api/v1`（`vite.config.ts` 里 proxy 指向同一台 BFF）。
