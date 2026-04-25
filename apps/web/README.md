# Distill Dashboard Web App

Internal React dashboard scaffold for the Distill control plane.

## Stack

- React 19
- TypeScript
- Vite 6
- Yarn 1
- React Router

`Vite 6` is pinned here because the current local Node runtime is `20.18.x`.
The latest `create-vite` release requires `20.19+`.

## Commands

```bash
cd apps/web
yarn install
```

Start the read-only API in one terminal:

```bash
cd ../..
.venv/bin/distill-web-serve
```

Then run the Vite app in another terminal:

```bash
cd apps/web
yarn dev
```

Production build:

```bash
cd apps/web
yarn build
```

From repo root you can also use:

```bash
make web-install
make web-dev
make web-build
```

## Current scope

The app currently ships a dashboard shell with three routes:

- `Overview`
- `Pipeline`
- `Review`

The data now comes from the local SQLite snapshot and generated pack files via a
minimal Python JSON API. The current scope is read-only on purpose: unsupported
actions such as trigger-run and review writeback are hidden until a real backend
exists.
