```
Clients (query)
┌───────────────────────────────┐
│ Grafana / curl / scripts     │
│  - /loki/api/v1/query        │
│  - /loki/api/v1/query_range  │
└──────────────┬────────────────┘
               │ HTTPS (auth/TLS at the gateway)
               ▼
        ┌───────────────────┐
        │   LOKI GATEWAY    │  ← single front door (auth, TLS, routing, LB)
        └───────┬───────────┘
                │ routes to read path
                ▼
        ┌───────────────────┐
        │ Query Frontend    │  ← optional but common (splits/queues queries,
        └───────┬───────────┘     caching, results merge)
                │
         fan‑out│ to workers
                ▼
        ┌───────────────────┐        ┌───────────────────┐
        │    Querier (N)    │  ...   │    Querier (N)    │  ← executes LogQL,
        └──┬──────────────┬─┘        └──┬──────────────┬─┘    hits index & chunks
           │              │               │              │
           │              │               │              │
           ▼              ▼               ▼              ▼
   ┌────────────┐  ┌────────────┐   ┌────────────┐  ┌────────────┐
   │ Index GW   │  │  Ingester  │   │  Object    │  │  Cache     │
   │ (labels)   │  │ (recent)   │   │ Storage    │  │ (mem/redis)│
   └────┬───────┘  └────┬───────┘   │  (S3/GCS)  │  └────────────┘
        │               │           └──────┬─────┘
        │               └── read recent           │
        └── read label/series index               └─ queriers fetch chunks
```