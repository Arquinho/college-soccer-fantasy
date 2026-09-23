# College Soccer Fantasy — Delivery Candidate v6

This package is intended to look and behave like the product that will be handed to a developer, while remaining safe to run locally as a prototype.

Start with `bash run.sh`, then visit `http://127.0.0.1:5012`.

The first screen is Login. For the delivery demo, any non-empty email/password can enter, or use **Continue as Demo Manager**. This is intentional: real identity verification is a production integration, not simulated security.

The prototype is cache-first. Opening the site should not perform a full NCAA/NAIA/NJCAA crawl. Use the visible Refresh/Sync controls when a current public-source update is needed.

See `V6_CHANGES.md`, `DEPLOYMENT.md`, and `HANDOFF_CHECKLIST.md` for the developer handoff.
