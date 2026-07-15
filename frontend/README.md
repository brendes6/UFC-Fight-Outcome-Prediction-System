# UFC Predictor — Frontend

React + Vite single-page app for the UFC Fight Prediction Platform. It lets you
pick two fighters and see the model's predicted winner, alongside sidebars for
upcoming and previously predicted fights.

## Structure

```
src/
  api/       HTTP client for the prediction backend (client.js)
  domain/    Pure business logic, e.g. fighter-tag normalization (fighters.js)
  components/ React UI components
```

## Development

```bash
npm install
npm run dev      # start the dev server
npm run build    # production build
npm run lint     # eslint
npm test         # run unit tests (node:test)
```

## Configuration

The client talks to the deployed Cloud Run backend by default. To point it at a
different backend (e.g. a local one), copy `.env.example` to `.env` and set
`VITE_API_URL`.
