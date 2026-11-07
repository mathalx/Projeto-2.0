# Specification: Architecture - Initial Project Structure

## Purpose
Define the foundational folder structure, module boundaries, and version control guidelines.

## Requirements
1. The project must have a clear separation between `core`, `modules`, and `shared`.
2. Storage folders (`storage/photos`, `storage/reports`, `storage/exports`) must be ignored by Git except for `.gitkeep`.
3. Secrets and environment variables must be managed via `.env` and excluded from version control.
