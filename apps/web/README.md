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

The data is mock-only for now. The next step is wiring these screens to the
Distill pipeline and pack APIs.
