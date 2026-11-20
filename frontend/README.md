# KahveCell Frontend

React, TypeScript, Vite, React Router, and Leaflet frontend for the KahveCell API.

## Run locally

From this directory:

```bash
npm install
cp .env.example .env
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Start the
FastAPI backend separately at `http://localhost:8000`; the API base URL can be
changed with `VITE_API_BASE_URL`.

The demo OTP is `1234`. The subscription page uses mock card numbers only:
`4242424242424242` succeeds and `4000000000000002` fails. Do not enter real card
details.

## Pages

- `/login` and `/register`: phone + simulated OTP authentication
- `/`: nearby shops, search, and Leaflet map
- `/shops`: redirects to the home page
- `/shops/:shopId`: shop details and menu
- `/orders/new?shop_id=:id`: customized coffee order
- `/orders/:orderId/qr`: order status and signed QR code
- `/orders/history`: customer order history
- `/subscriptions`: plans and mock payment
