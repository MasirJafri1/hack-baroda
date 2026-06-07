export const RISKY_POOL_DIFF = `diff --git a/src/config/db-pool-update.ts b/src/config/db-pool-update.ts
index 92c81da..a83b2ef 100644
--- a/src/config/db-pool-update.ts
+++ b/src/config/db-pool-update.ts
@@ -14,11 +12,12 @@ export const dbConfig = {
   host: process.env.DB_HOST,
-  maxPoolSize: 10,
+  maxPoolSize: 500,
   idleTimeout: 30000,
   connectionTimeout: 2000,
-  leakDetectionThreshold: 0
+  leakDetectionThreshold: 1000
 };`;

export const SAFE_POOL_DIFF = `diff --git a/src/config/db-pool-update.ts b/src/config/db-pool-update.ts
index 92c81da..a83b2ef 100644
--- a/src/config/db-pool-update.ts
+++ b/src/config/db-pool-update.ts
@@ -14,11 +12,12 @@ export const dbConfig = {
   host: process.env.DB_HOST,
-  maxPoolSize: 10,
+  maxPoolSize: 50,
   idleTimeout: 30000,
   connectionTimeout: 2000,
   enableQueue: true
 };`;

export const RISKY_WEBSOCKET_DIFF = `diff --git a/app/websocket_handler.py b/app/websocket_handler.py
index 92c81da..a83b2ef 100644
--- a/app/websocket_handler.py
+++ b/app/websocket_handler.py
@@ -12,11 +12,12 @@ class ConnectionManager:
-    async def connect(self, websocket: WebSocket):
-        await websocket.accept()
-        self.active_connections.append(websocket)
-
-    async def disconnect(self, websocket: WebSocket):
-        self.active_connections.remove(websocket)
+    async def handle_connection(self, websocket: WebSocket):
+        await websocket.accept()
+        self.active_connections.append(websocket)
+        while True:
+            data = await websocket.receive_text()
+            await self.send_personal_message(f"Message received: {data}", websocket)
+`;

export const SAFE_WEBSOCKET_DIFF = `diff --git a/app/websocket_handler.py b/app/websocket_handler.py
index 92c81da..a83b2ef 100644
--- a/app/websocket_handler.py
+++ b/app/websocket_handler.py
@@ -12,11 +12,12 @@ class ConnectionManager:
+    async def handle_connection(self, websocket: WebSocket):
+        await websocket.accept()
+        self.active_connections.append(websocket)
+        try:
+            while True:
+                data = await websocket.receive_text()
+                await self.send_personal_message(f"Message received: {data}", websocket)
+        except WebSocketDisconnect:
+            self.active_connections.remove(websocket)
+`;

export const stageLabels: Record<string, string> = {
  github_crawler: 'GitHub Crawler',
  context_agent: 'Context Agent',
  reviewer_v1: 'Reviewer V1',
  reviewer_v2: 'Reviewer V2',
  retrieval_agent: 'Retrieval Agent',
  git_expert: 'Git Expert',
  cloud_expert: 'Cloud Expert',
  code_expert: 'Code Expert',
  big_boss: 'Big Boss',
};

export const stages = [
  'github_crawler',
  'context_agent',
  'reviewer_v1',
  'reviewer_v2',
  'retrieval_agent',
  'git_expert',
  'cloud_expert',
  'code_expert',
  'big_boss',
];
